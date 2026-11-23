"""One physical neuron on the carry-save MAC: y = clamp((w0*x0 + w1*x1 + b) // 4, 0, 15).
Physical parts (all redstone, MAC frame coords (x, layer, z)):
  registers  repeater latches for x0, x1 (4 bit), w0, w1 (5 bit signed), b (6 bit signed), written through WE rows
  crossbar   AND (comparator: data - NOTsel) per stored bit, OR into the MAC x / w lanes by glass climbs
  sequencer  RUN latch + delay-line raster: slot 0 reset, 1 x0*w0, 2 x1*w1, 3 2*(b>>1), 4 1*(b&1), 5-7 carry flush,
             row 8 strobes the output latch and clears RUN
  activation S taps of bits 2..12 (floor /4), sat = OR(q4..q9), out_k = (q_k | sat) - sign, output latch + lamps
Commands only place data pins, pulse WE pins and pulse START."""
from mac import system, PX, NB
from cells import CMP

OX, OZ = 20, -260            # controller (sequencer + crossbar) origin
NF = 21                      # forward repeaters per sequencer row; 40 repeaters x 4 rt = 160 rt per slot
BUS = NF + 4                 # GO bus column
GT = lambda k: (14, 11) if k == 0 else (10, 7)   # GO taps (x) on the return lane: slot + 80 rt (reset) or + 96 rt, 8 rt wide
QX = lambda i: 60 + 4 * i    # activation column of q_i (= S bit i+2)
QZ = lambda i: -56 - 3 * i   # L4 row of q_i
COLS = ["w4", "w3", "w2", "w1", "w0", "x0", "x1", "x2", "x3"]


class Off:
    """Offset writer into a Lay; every new cell must be empty unless it is a declared pin."""
    def __init__(self, L, ox, oz): self.L, self.ox, self.oz = L, ox, oz
    def chk(self, x, l, z):
        assert (x, l, z) not in self.L.B, ("collision", (x, l, z), self.L.B[(x, l, z)])
    def d(self, x, z, net, l=0):
        p = (self.ox + x, l, self.oz + z)
        if p in self.L.B and self.L.net.get(p) == net: return
        self.chk(*p); self.L.dust(*p, net)
    def r(self, x, z, f, net, delay=1, l=0):
        p = (self.ox + x, l, self.oz + z); self.chk(*p); self.L.rep(*p, f, net, delay)
    def p(self, x, z, b, net=None, l=0):
        q = (self.ox + x, l, self.oz + z); self.chk(*q); self.L.put(*q, b, net)
    def at(self, x, z, l=0): return (self.ox + x, l, self.oz + z)


def seq(L):
    """Sequencer in its local frame. Returns pins and outlet points (MAC frame)."""
    o = Off(L, OX, OZ)
    # RUN latch: Q = (START | Q) - END, output south down x=0
    o.r(0, -7, "north", "start")                                    # START pin at (0,-8)
    o.d(0, -6, "runr"); o.p(0, -5, CMP % "north", "run")
    o.r(-1, -5, "west", "end")
    o.r(0, -4, "north", "run")
    for x, z in [(0, -3), (1, -3), (2, -3), (2, -4), (2, -5), (2, -6)]: o.d(x, z, "run")
    o.r(1, -6, "east", "run")
    for z in (-2, -1, 0): o.d(0, z, "run")
    tap = lambda k: "run" if k == 0 else "t%d" % k
    for k in range(9):
        z0 = 8 * k
        for x in range(1, NF + 1): o.r(x, z0, "west", "f%d" % k, delay=4)
        for dz in range(3): o.d(NF + 1, z0 + dz, "f%d" % k)
        XA, XB_ = GT(k)
        for x in range(NF, 0, -1):
            if x == XA: o.d(x, z0 + 2, "ga%d" % k)
            elif x == XB_: o.d(x, z0 + 2, "gb%d" % k)
            else: o.r(x, z0 + 2, "east", "f%d" % k, delay=4)
        if k < 8:
            for dz in range(2, 9): o.d(0, z0 + dz, tap(k + 1))
        else:
            o.d(0, z0 + 2, "t9")
        if k <= 4:                                                  # window SEL_k = tap(kP) - tap((k+1)P)
            o.d(-1, z0, tap(k)); o.d(-2, z0, tap(k)); o.d(-2, z0 + 1, tap(k))
            o.p(-2, z0 + 2, CMP % "north", "sel%d" % k); o.r(-1, z0 + 2, "east", tap(k + 1))
            o.d(-2, z0 + 3, "sel%d" % k)
            if k >= 1:                                              # NOTsel_k = 15 - SEL_k, out at (-4, z0+2)
                o.r(-3, z0 + 3, "east", "sel%d" % k); o.p(-4, z0 + 3, CMP % "south", "ns%d" % k)
                o.p(-4, z0 + 4, "redstone_block"); o.d(-4, z0 + 2, "ns%d" % k)
        # GO_k (k<8) or STROBE (k=8) = tap(a) - tap(a + 8 rt)
        g = "go%d" % k if k < 8 else "strobe"
        o.d(XA, z0 + 3, "ga%d" % k); o.d(XA, z0 + 4, "ga%d" % k); o.p(XA, z0 + 5, CMP % "north", g)
        for x, z in [(XB_, z0 + 3), (XB_, z0 + 4), (XB_, z0 + 5), (XB_ + 1, z0 + 5)]: o.d(x, z, "gb%d" % k)
        o.r(XA - 1, z0 + 5, "west", "gb%d" % k)
        if k < 8:
            for x in range(XA, BUS): o.r(x, z0 + 6, "west", g) if x in (12, 19, BUS - 1) else o.d(x, z0 + 6, g)
    for z in range(4, 63):                                          # GO bus, flows north
        if z % 8 == 2 and z > 6: o.r(BUS, z, "south", "go")
        else: o.d(BUS, z, "go")
    o.d(10, 70, "strobe")
    return o


def crossbar(L, regs):
    """Tiles c (lane x = -60 + 6c) x rows r=1..4 (latch row z = 8r). regs[(c, r)] = register name or 'const'."""
    o = Off(L, OX, OZ)
    xc = lambda c: -60 + 6 * c
    for r in range(1, 5):
        zl = 8 * r
        o.p(-63, zl - 2, "redstone_block"); o.p(-62, zl - 2, CMP % "west", "lk%d" % r)   # LOCK_r = 15 - WE_r, WE pin (-62, zl-3)
        for c in range(9):
            x = xc(c)
            o.r(x + 1, zl - 2, "west", "lk%d" % r)
            if c: o.r(x + 1, zl + 2, "east", "ns%d" % r)
            kind = regs.get((c, r))
            if not kind: continue
            if kind == "const": o.p(x + 4, zl, "redstone_block")
            else: o.r(x + 4, zl, "east", kind); o.r(x + 4, zl - 1, "north", "lk%d" % r)
            o.p(x + 3, zl, CMP % "east", "and%d_%d" % (c, r)); o.r(x + 3, zl + 1, "south", "ns%d" % r)
            o.d(x + 2, zl, COLS[c]); o.p(x + 1, zl, "glass"); o.d(x + 1, zl, COLS[c], l=1)
        for x in range(-61, -7): o.d(x, zl - 2, "lk%d" % r)
        for x in range(-57, -4): o.d(x, zl + 2, "ns%d" % r)
    for c in range(9):
        for z in range(8, 41):
            if z % 8 == 4: o.r(xc(c), z, "north", COLS[c], l=2)
            else: o.d(xc(c), z, COLS[c], l=2)
    return o


def registers():
    regs, pins = {}, {}
    for b in range(5):
        c = 4 - b
        regs[(c, 1)] = "W0_%d" % b; regs[(c, 2)] = "W1_%d" % b; regs[(c, 3)] = "B_%d" % (b + 1)
    regs[(4, 4)] = "B_0"
    for i in range(4):
        regs[(5 + i, 1)] = "X0_%d" % i; regs[(5 + i, 2)] = "X1_%d" % i
    regs[(6, 3)] = "const"; regs[(5, 4)] = "const"
    for (c, r), n in regs.items():
        if n != "const": pins[n] = (OX - 60 + 6 * c + 5, 0, OZ + 8 * r)
    return regs, pins


def activation(L):
    """Shift (bits 2..12), saturation, sign gate, output latch. Inputs arrive on L4 rows QZ(i) from the west."""
    o = Off(L, 0, 0)
    for i in range(4):                                              # junction cells first so path() leaves them dust
        x = QX(i)
        o.d(x + 2, -44, "sat"); o.d(x + 2, -43, "sat"); o.p(x + 1, -43, "glass"); o.d(x + 1, -43, "sat", l=1)
        o.d(x, -43, "q%d" % i, l=2)
        o.d(x + 2, -40, "sign"); o.r(x + 2, -39, "north", "sign")
        for z in range(-38, -33): o.d(x + 2, z, "sign")
        o.r(x + 1, -34, "east", "sign")
        o.r(x, -35, "north", "q%d" % i); o.p(x, -34, CMP % "north", "o%d" % i); o.d(x, -33, "o%d" % i)
        o.r(x, -32, "north", "y%d" % i); o.p(x, -31, "redstone_lamp")
        o.d(x + 2, -29, "lko"); o.r(x + 2, -30, "south", "lko"); o.d(x + 2, -31, "lko"); o.d(x + 2, -32, "lko"); o.r(x + 1, -32, "east", "lko")
    for i in range(4, 10): o.d(QX(i), -44, "sat"); o.r(QX(i), -45, "north", "q%d" % i)
    o.r(QX(4) - 1, -44, "east", "sat"); o.r(67, -44, "east", "sat"); o.r(86, -44, "east", "sat")
    o.p(105, -29, "redstone_block"); o.p(104, -29, CMP % "east", "lko"); o.r(104, -30, "north", "stb")   # lock row kept off the lamps (z=-31)
    return o


def expand(pts):
    out = [pts[0]]
    for (x1, l1, z1) in pts[1:]:
        x0, l0, z0 = out[-1]
        if l1 != l0: out.append((x1, l1, z1)); continue
        sx = (x1 > x0) - (x1 < x0); sz = (z1 > z0) - (z1 < z0)
        while (x0, z0) != (x1, z1): x0 += sx; z0 += sz; out.append((x0, l1, z0))
    return out


def route(L, net, pts, strength=15):
    for c in expand(pts):
        assert c not in L.B or L.net.get(c) == net, ("route %s hits" % net, c, L.B[c], L.net.get(c))
    return L.path(net, pts, strength)


def neuron():
    L, P = system(True)
    regs, pins = registers()
    seq(L); crossbar(L, regs); activation(L)
    # pins of the MAC become repeaters fed by the controller
    L.rep(15, 0, 3, "south", "x0"); [L.rep(15, 0, 3 + 33 * i, "south", "x%d" % i) for i in range(1, 4)]
    for k in range(4): L.rep(11 - k * PX, 0, -21, "north", "w%d" % k)
    L.rep(-101, 2, -31, "north", "w4")
    L.rep(-155, 0, -42, "east", "go"); L.rep(20, 2, -10, "east", "rst")
    # crossbar lanes -> MAC inputs (L0). Lane c leaves the crossbar at (OX-60+6c, 2, OZ+40)
    lx = lambda c: OX - 60 + 6 * c
    zt = {"x3": -182, "x2": -180, "x1": -178, "x0": -176, "w4": -174, "w3": -172, "w2": -170, "w0": -168, "w1": -166}
    for c, n in enumerate(COLS):
        x = lx(c); top = [(x, 2, OZ + 40), (x, 2, OZ + 41), (x, 1, OZ + 42), (x, 0, OZ + 43), (x, 0, zt[n])]
        if n[0] == "x":
            i = int(n[1]); xe = 45 + 3 * i; z0 = 4 + 33 * i
            route(L, n, top + [(xe, 0, zt[n]), (xe, 0, z0), (15, 0, z0)], strength=11)
        elif n == "w4":
            route(L, n, top + [(-101, 0, zt[n]), (-101, 0, -34), (-101, 1, -33), (-101, 2, -32)], strength=11)
        else:
            k = int(n[1]); route(L, n, top + [(11 - k * PX, 0, zt[n]), (11 - k * PX, 0, -22)], strength=11)
    # RST: window 0 output (-2, 3) local -> MAC rst pin
    route(L, "rst", [(OX - 3, 0, OZ + 3), (OX - 66, 0, OZ + 3), (OX - 67, 1, OZ + 3), (OX - 68, 2, OZ + 3),
                   (OX - 68, 2, -40), (24, 2, -40), (24, 2, -10), (21, 2, -10)], strength=8)
    # GO: bus top (20, 4) local, up to L4 inside the controller, down to L2 for the trip to the MAC go pin
    route(L, "go", [(OX + BUS, 0, OZ + 3), (OX + BUS, 1, OZ + 2), (OX + BUS, 2, OZ + 1), (OX + BUS, 3, OZ + 0), (OX + BUS, 4, OZ - 1),
                  (OX + BUS, 4, OZ - 14), (OX - 72, 4, OZ - 14), (OX - 72, 4, -120), (OX - 72, 3, -119), (OX - 72, 2, -118),
                  (OX - 72, 2, -100), (-150, 2, -100), (-150, 2, -44), (-150, 1, -43), (-150, 0, -42), (-154, 0, -42)], strength=11)
    # STROBE: row 8 output (7..10, 70) local; END back to the RUN latch reset, STB to the output latch
    route(L, "strobe", [(OX + 10, 0, OZ + 70), (OX + BUS + 1, 0, OZ + 70), (OX + BUS + 2, 1, OZ + 70), (OX + BUS + 3, 2, OZ + 70),
                      (OX + BUS + 4, 2, OZ + 70), (OX + BUS + 4, 2, OZ - 10), (OX - 4, 2, OZ - 10), (OX - 4, 1, OZ - 9),
                      (OX - 4, 0, OZ - 8), (OX - 4, 0, OZ - 5), (OX - 2, 0, OZ - 5)], strength=10)
    L.rep(OX + 10, 0, OZ + 71, "north", "stb")
    route(L, "stb", [(OX + 10, 0, OZ + 72), (OX + 10, 1, OZ + 73), (OX + 10, 2, OZ + 74), (OX + 10, 2, OZ + 76),
                   (108, 2, OZ + 76), (108, 2, -35), (108, 1, -34), (108, 0, -33), (108, 0, -31), (104, 0, -31)])
    # S taps: A lane corners -> L4 rows -> activation columns
    for j in range(2, NB):
        i = j - 2
        if j == 2: x0, z0 = 1 - 2 * PX, -33
        else: x0, z0 = -1 - PX * j, -27
        L.rep(x0, 4, z0, "south", "q%d" % i)
        pts = [(x0, 4, z0 - 1), (x0, 4, QZ(i)), (QX(i), 4, QZ(i)), (QX(i), 4, -52), (QX(i), 3, -51), (QX(i), 2, -50)]
        if i < 4: pts += [(QX(i), 2, -38), (QX(i), 1, -37), (QX(i), 0, -36)]
        elif i < 10: pts += [(QX(i), 1, -49), (QX(i), 0, -48), (QX(i), 0, -46)]
        else: pts += [(QX(i), 1, -49), (QX(i), 0, -48), (QX(i), 0, -40), (QX(0) + 2, 0, -40)]
        route(L, "q%d" % i if i < 10 else "sign", pts)
    route(L, "sat", [(QX(9), 0, -44), (QX(0) + 2, 0, -44)])
    route(L, "lko", [(103, 0, -29), (QX(0) + 2, 0, -29)])
    P = dict(P)
    P.update(start=(OX, 0, OZ - 8), we={r: (OX - 62, 0, OZ + 8 * r - 3) for r in range(1, 5)}, reg=pins,
             y=[(QX(i), 0, -32) for i in range(4)], sat=(QX(4), 0, -44))
    return L, P


def ref(x0, x1, w0, w1, b):
    return max(0, min(15, (w0 * x0 + w1 * x1 + b) // 4))


if __name__ == "__main__":
    L, P = neuron()
    print(len(L.B), "blocks")
