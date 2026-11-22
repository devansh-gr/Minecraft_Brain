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
    def __init__(self):
        self.gates, self.n = [], 0
    def nor(self, *ins):
        self.n += 1; name = f"g{self.n}"
        self.gates.append((name, list(ins))); return name
    def NOT(self, a): return self.nor(a)
    def OR(self, *a): return self.NOT(self.nor(*a))
    def AND(self, a, b): return self.nor(self.NOT(a), self.NOT(b))
    def fa(self, a, b, c):
        g1 = self.nor(a, b); g2 = self.nor(a, g1); g3 = self.nor(b, g1); g4 = self.nor(g2, g3)
        g5 = self.nor(g4, c); g6 = self.nor(g4, g5); g7 = self.nor(c, g5)
        return self.nor(g6, g7), self.nor(g1, g5)            # sum, carry
