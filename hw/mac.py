"""Array MAC cell: b = w AND x, then full adder (a, b, c) -> (s, cout).
Tiles into A_next = A + x*w (rows = bits of x, columns = bits of the result, sums jog one column east per row).
Layers: 0 floor (y=-60), 1 step (y=-59, dust on stone), 2 glass lane (y=-58, dust on glass).
Cell local x in [-15, 12] (east edge 12), z in [-1, 31]. Carry enters east on L2 at z=4, leaves west on L2 at z=4.
NOT x enters east on L2 at z=0 (row-wide line). w lane vertical at x=11. a enters top at x=1, s leaves at (29, 0, 31)."""
from cells import xor_cell, CMP, REP

PX, PZ = 28, 33


class Lay:
    def __init__(self): self.B = {}; self.net = {}

    def put(self, x, l, z, b, net=None):
        self.B[(x, l, z)] = b
        if net: self.net[(x, l, z)] = net

    def dust(self, x, l, z, net):
        self.put(x, l, z, "redstone_wire", net)
        if l == 2 and (x, 1, z) not in self.B: self.put(x, 1, z, "glass")
        if l == 1 and (x, 0, z) not in self.B: self.put(x, 0, z, "stone")

    def rep(self, x, l, z, facing, net, delay=1):
        self.put(x, l, z, REP % facing if delay == 1 else f"repeater[facing={facing},delay={delay}]", net)
        if l == 2: self.put(x, 1, z, "stone")

    def line(self, net, l, pts):
        """Dust along axis-aligned segments between consecutive (x, z) points on layer l."""
        for (x0, z0), (x1, z1) in zip(pts, pts[1:]):
            sx = (x1 > x0) - (x1 < x0); sz = (z1 > z0) - (z1 < z0)
            x, z = x0, z0
            while True:
                if (x, l, z) not in self.B: self.dust(x, l, z, net)
                if (x, z) == (x1, z1): break
                x += sx; z += sz

    def sub(self, B, ox, oz, nets=None):
        for (dx, l, dz), b in B.items():
            self.put(dx + ox, l, dz + oz, b)


def cell():
    L = Lay()
    # NOT x row (L2, z=0) with one repeater, tap at x=9 down to the AND comparator side
    L.rep(11, 2, 0, "east", "nx"); L.rep(-4, 2, 0, "east", "nx"); L.line("nx", 2, [(12, 0), (-15, 0)])
    L.dust(9, 2, 1, "nx"); L.dust(9, 1, 2, "nx"); L.line("nx", 0, [(9, 3), (9, 4)])
    L.rep(9, 0, 5, "north", "nx")
    # w lane (floor, x=11) with branch into the AND comparator rear
    L.line("w", 0, [(11, -1), (11, 31)]); L.rep(11, 0, 2, "north", "w"); L.rep(11, 0, 16, "north", "w"); L.rep(11, 0, 28, "north", "w")
    L.dust(10, 0, 6, "w")
    L.put(9, 0, 6, CMP % "east", "b")                       # b = w - NOTx
    # b to XOR1 v input (glass at x=4)
    L.dust(8, 0, 6, "b"); L.rep(7, 0, 6, "east", "b"); L.line("b", 0, [(6, 6), (4, 6)]); L.rep(4, 0, 7, "north", "b")
    L.dust(4, 1, 8, "b"); L.dust(4, 2, 9, "b")
    # a column (floor x=1) into XOR1, branch west along z=2 to the carry cluster
    L.line("a", 0, [(1, -1), (1, 9)]); L.rep(1, 0, 0, "north", "a"); L.rep(1, 0, 7, "north", "a")
    L.line("a", 0, [(0, 2), (-12, 2), (-12, 22), (-9, 22)])
    L.rep(-4, 0, 2, "east", "a"); L.rep(-12, 0, 6, "north", "a"); L.rep(-12, 0, 16, "north", "a")
    # XOR1 (a, b) -> p at (2,18); XOR2 (p, c) -> s at (5,28)
    X, _, _ = xor_cell()
    L.sub(X, 0, 12); L.sub(X, 3, 22)
    # c row (L2, z=4) from the east edge: branch south at x=7 into XOR2 v, west to x=-3 then down to the cluster
    L.rep(10, 2, 4, "east", "c"); L.rep(2, 2, 4, "east", "c"); L.line("c", 2, [(12, 4), (-3, 4)])
    L.rep(7, 2, 10, "north", "c"); L.rep(7, 2, 17, "north", "c"); L.line("c", 2, [(7, 5), (7, 19)])
    L.dust(-3, 1, 5, "c"); L.line("c", 0, [(-3, 6), (-3, 25)])
    L.rep(-3, 0, 12, "north", "c"); L.rep(-3, 0, 21, "north", "c")
    # p: to XOR2 u, and west on L2 (z=19) down into the cluster at x=-6
    L.dust(2, 0, 19, "p"); L.rep(3, 0, 19, "west", "p"); L.dust(4, 0, 19, "p")
    L.dust(1, 0, 19, "p"); L.dust(0, 1, 19, "p"); L.dust(-1, 2, 19, "p"); L.rep(-2, 2, 19, "east", "p")
    L.line("p", 2, [(-3, 19), (-6, 19)]); L.dust(-6, 1, 20, "p"); L.dust(-6, 0, 21, "p")
    # carry cluster around D=(-6,23): NP = 15 - p, K = c - NP, G = a - p, cout = K | G
    L.rep(-6, 0, 22, "north", "p"); L.dust(-6, 0, 23, "p")
    L.put(-5, 0, 22, "redstone_block"); L.put(-5, 0, 23, CMP % "north", "np"); L.dust(-5, 0, 24, "np")
    L.put(-5, 0, 25, CMP % "east", "cout"); L.rep(-4, 0, 25, "east", "c")
    L.put(-7, 0, 23, CMP % "north", "cout"); L.dust(-7, 0, 22, "a"); L.rep(-8, 0, 22, "west", "a")
    L.line("cout", 0, [(-6, 25), (-7, 25), (-7, 24)])
    # cout: west along z=25, north along x=-14, up to L2 and out of the west edge at z=4
    L.line("cout", 0, [(-8, 25), (-14, 25), (-14, 6)]); L.rep(-10, 0, 25, "east", "cout"); L.rep(-14, 0, 20, "south", "cout"); L.rep(-14, 0, 8, "south", "cout")
    L.dust(-14, 1, 5, "cout"); L.line("cout", 2, [(-14, 4), (-15, 4)])
    # s: south, east along z=30 over the w lane on L2, then down to the next row's a column at x=29
    L.line("s", 0, [(5, 29), (5, 30), (8, 30)]); L.rep(6, 0, 30, "west", "s")
    L.dust(9, 1, 30, "s"); L.line("s", 2, [(10, 30), (12, 30)]); L.dust(13, 1, 30, "s")
    L.line("s", 0, [(14, 30), (29, 30), (29, 31)]); L.rep(20, 0, 30, "west", "s")
    return L


NB, XB, WB = 13, 4, 5       # accumulator bits (signed), x bits (unsigned), w bits (signed)


def array():
    """Rows i = x bits, columns k: cell (i,k) adds w_min(k,4)*x_i into result bit k+i.
    Returns layout plus pin positions: A inputs, w lane tops, x inputs, result bit outputs."""
    L = Lay()
    for i in range(XB):
        for k in range(NB - i):
            C = cell()
            for (x, l, z), b in C.B.items():
                L.put(x - k * PX, l, z + i * PZ, b, C.net.get((x, l, z)))
        z0 = i * PZ                                       # NOT x_i generator at the east end of row i
        L.put(16, 0, z0, "redstone_block"); L.put(15, 0, z0, CMP % "east", "nx")
        L.rep(15, 0, z0 + 1, "south", "x%d" % i); L.dust(15, 0, z0 + 2, "x%d" % i)
        L.dust(14, 0, z0, "nx"); L.dust(13, 1, z0, "nx")
    pins = {"A": [(1 - k * PX, 0, -2) for k in range(NB)],
            "w": [(11 - k * PX, 0, -2) for k in range(NB)],
            "x": [(15, 0, i * PZ + 3) for i in range(XB)],
            "out": [(29, 0, i * PZ + 31) for i in range(XB - 1)] +
                   [(29 - k * PX, 0, (XB - 1) * PZ + 31) for k in range(NB - XB + 1)]}
    return L, pins


def expected(A, x, w):
    v = (A + x * w) % (1 << NB)
    return v - (1 << NB) if v >= 1 << (NB - 1) else v
