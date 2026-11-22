"""NOR-gate netlist -> physical redstone (torch NOR gates), placed as a crossbar.

Every signal is a dust column on the floor (y=L0) running south (+z), one column every 4 blocks; a column is
reused once its signal's last reader has been placed. Every gate gets its own band of 8 rows. Its inputs
branch off their columns, pass a repeater (diode), climb a stone step and join a lane of dust on glass two
blocks above the floor (y=L2) that crosses over the other columns. The lane ends in a stone block whose wall
torch is the gate output (NOR of everything on the lane); the output steps down to a new floor column.
"""
L0, L1, L2 = -60, -59, -58
PITCH, BAND = 4, 8


def compile(gates, inputs, x0=0, z0=0):
    """gates: list of (name, [input names]) in topological order, each a NOR. inputs: primary input names.
    Returns blocks, {input: source position}, {signal: probe position (floor dust)}."""
    last = {}
    for g, (name, ins) in enumerate(gates):
        for s in ins:
            last[s] = g
    col, free, used = {}, [], 0
    def alloc():
        nonlocal used
        if free:
            return free.pop(0)
        used += 1
        return used - 1
    B, src, probe = {}, {}, {}
    X = lambda c: x0 + PITCH * c
    start = {}
    for s in inputs:
        col[s] = alloc(); start[s] = z0 - 1
        src[s] = (X(col[s]), L0, z0 - 2)
        probe[s] = (X(col[s]), L0, z0 - 1)
    zend = z0 + BAND * len(gates)
    for g, (name, ins) in enumerate(gates):
        zb = z0 + BAND * g
        # columns that stay alive through this band: dust zb..zb+7 with a repeater at zb+4
        xs = [X(col[s]) + 2 for s in ins]
        for s in ins:
            x = X(col[s])
            B[(x + 1, L0, zb)] = "redstone_wire"; B[(x + 2, L0, zb)] = "redstone_wire"
            B[(x + 2, L0, zb + 1)] = "repeater[facing=north]"
            B[(x + 2, L0, zb + 2)] = "stone"; B[(x + 2, L1, zb + 2)] = "redstone_wire"
        # free the columns whose last reader is this gate, then place the output column
        for s in ins:
            if last[s] == g and s in col:
                B.update(column(X(col[s]), start[s], zb))
                free.append(col.pop(s)); free.sort()
        c = alloc(); xg = X(c)
        span = xs + [xg]
        for x in range(min(span), max(span) + 1):
            if x != xg:
                B[(x, L1, zb + 3)] = "glass"; B[(x, L2, zb + 3)] = "redstone_wire"
        for x in range(min(span), max(span) + 1):     # lane repeaters toward the gate every 12 blocks
            d = abs(x - xg)
            if d and d % 12 == 0:
                B[(x, L2, zb + 3)] = "repeater[facing=%s]" % ("west" if x < xg else "east")
        B[(xg, L2, zb + 3)] = "stone"
        B[(xg, L2, zb + 4)] = "redstone_wall_torch[facing=south]"
        B[(xg, L1, zb + 5)] = "stone"; B[(xg, L2, zb + 5)] = "redstone_wire"
        B[(xg, L0, zb + 6)] = "stone"; B[(xg, L1, zb + 6)] = "redstone_wire"
        col[name] = c; start[name] = zb + 7
        probe[name] = (xg, L0, zb + 7)
    for s, c in col.items():                       # outputs and inputs never read run to the end
        B.update(column(X(c), start[s], zend + 1))
        probe[s] = (X(c), L0, zend + 1)
    compile2.level = level
    return B, src, probe


def column(x, z_from, z_to, z0=0):
    """Floor dust from z_from to z_to, with a repeater wherever the strength would fall below 6 (never on a
    tap row, where the branch must touch plain dust)."""
    B, st = {}, 13
    for z in range(z_from, z_to + 1):
        st -= 1
        if st < 6 and (z - z0) % BAND not in (0, 1, 2) and z < z_to:
            B[(x, L0, z)] = "repeater[facing=north]"; st = 15
        else:
            B[(x, L0, z)] = "redstone_wire"
    return B


# ---- netlist helpers (all NOR)
class Net:
    """NOR netlist builder with constant folding ("0"/"1" are constants)."""
    def __init__(self):
        self.gates, self.n, self.memo = [], 0, {}
    def nor(self, *ins):
        if "1" in ins:
            return "0"
        ins = tuple(sorted(set(i for i in ins if i != "0")))
        if not ins:
            return "1"
        if ins in self.memo:
            return self.memo[ins]
        self.n += 1; name = f"g{self.n}"
        self.gates.append((name, list(ins))); self.memo[ins] = name
        return name
    def NOT(self, a): return self.nor(a)
    def OR(self, *a): return self.NOT(self.nor(*a))
    def AND(self, a, b): return self.nor(self.NOT(a), self.NOT(b))
    def fa(self, a, b, c):
        g1 = self.nor(a, b); g2 = self.nor(a, g1); g3 = self.nor(b, g1); g4 = self.nor(g2, g3)
        g5 = self.nor(g4, c); g6 = self.nor(g4, g5); g7 = self.nor(c, g5)
        return self.nor(g6, g7), self.nor(g1, g5)            # sum, carry


def simulate(gates, values):
    """values: {input: 0/1}. Returns all signal values."""
    v = dict(values); v["0"] = 0; v["1"] = 1
    for name, ins in gates:
        v[name] = 0 if any(v[i] for i in ins) else 1
    return v


def compile2(gates, inputs, outputs, x0=0, z0=0):
    """Like compile(), but packs many gates into one band: gates whose inputs are ready share a band when their
    lanes are disjoint (with a gap), touch no other gate's taps, and no signal feeds two gates in the band."""
    readers = {}
    for name, ins in gates:
        for s in ins:
            readers[s] = readers.get(s, 0) + 1
    col, start, free, used = {}, {}, [], [0]
    def alloc_near(xt, bad):
        cands = sorted(free + [used[0]], key=lambda c: (abs(x0 + PITCH * c + 2 - xt), c))
        for c in cands:
            if c not in bad:
                return c
    B, src, probe = {}, {}, {}
    X = lambda c: x0 + PITCH * c
    for s in inputs:
        c = used[0]; used[0] += 1
        col[s] = c; start[s] = z0 - 1; src[s] = (X(c), L0, z0 - 2)
    pending = list(gates); band = 0; ready = set(inputs) | {"0", "1"}; level = {}
    while pending:
        zb = z0 + BAND * band
        lanes, taps, fed, placed, frees = [], set(), set(), [], []
        cand = [g for g in pending if all(i in ready for i in g[1])]
        cand.sort(key=lambda g: sum(X(col[i]) for i in g[1]) / len(g[1]))
        for name, ins in cand:
            if any(i in fed for i in ins):
                continue
            mytaps = {X(col[i]) + 2 for i in ins}
            if mytaps & taps:
                continue
            xt = sum(mytaps) / len(mytaps)
            # output column: freed by this gate or currently free; try nearest first
            opts = sorted(set(free) | {col[i] for i in ins if readers[i] == 1} | {used[0]},
                          key=lambda c: (abs(X(c) - xt), c))
            ok = None
            for c in opts:
                if any(X(c) == X(col[s]) for s in col if s not in ins and col[s] == c):
                    continue
                if any(c == cc for _, _, cc, _ in placed):
                    continue
                lo, hi = min(mytaps | {X(c)}), max(mytaps | {X(c)})
                if any(not (hi + 2 <= a or b + 2 <= lo) for a, b in lanes):
                    continue
                if any(lo <= t <= hi for t in taps):
                    continue
                if any(lo <= X(cc) <= hi for _, _, cc, _ in placed):
                    continue
                if any(a <= X(c) <= b for a, b in lanes):
                    continue
                ok = (c, lo, hi); break
            if ok is None:
                continue
            c, lo, hi = ok
            lanes.append((lo, hi)); taps |= mytaps; fed |= set(ins)
            placed.append((name, ins, c, (lo, hi)))
        if not placed:
            raise RuntimeError("no gate placeable in band %d" % band)
        for name, ins, c, (lo, hi) in placed:
            for s in ins:
                x = X(col[s])
                B[(x + 1, L0, zb)] = "redstone_wire"; B[(x + 2, L0, zb)] = "redstone_wire"
                B[(x + 2, L0, zb + 1)] = "repeater[facing=north]"
                B[(x + 2, L0, zb + 2)] = "stone"; B[(x + 2, L1, zb + 2)] = "redstone_wire"
                readers[s] -= 1
            xg = X(c)
            for x in range(lo, hi + 1):
                if x != xg:
                    B[(x, L1, zb + 3)] = "glass"
                    d = abs(x - xg)
                    B[(x, L2, zb + 3)] = ("repeater[facing=%s]" % ("west" if x < xg else "east")) if d % 12 == 0 else "redstone_wire"
            B[(xg, L2, zb + 3)] = "stone"
            B[(xg, L2, zb + 4)] = "redstone_wall_torch[facing=south]"
            B[(xg, L1, zb + 5)] = "stone"; B[(xg, L2, zb + 5)] = "redstone_wire"
            B[(xg, L0, zb + 6)] = "stone"; B[(xg, L1, zb + 6)] = "redstone_wire"
        for name, ins, c, _ in placed:          # free finished inputs, then claim outputs
            for s in ins:
                if readers[s] == 0 and s in col and s not in outputs:
                    B.update(column(X(col[s]), start[s], zb, z0))
                    free.append(col.pop(s))
        for name, ins, c, _ in placed:
            if c in free:
                free.remove(c)
            if c == used[0]:
                used[0] += 1
            col[name] = c; start[name] = zb + 7; probe[name] = (X(c), L0, zb + 7); level[name] = band
            ready.add(name); pending.remove((name, ins))
        band += 1
    zend = z0 + BAND * band
    for s, c in col.items():
        B.update(column(X(c), start[s], zend + 1, z0))
        probe[s] = (X(c), L0, zend + 1)
    compile2.level = level
    return B, src, probe
