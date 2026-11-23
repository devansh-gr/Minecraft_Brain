"""Combinational A + x*w array in the simulator against Python arithmetic."""
import random, sys, time
from rsim import Sim
from mac import array, expected, NB, XB, WB
from cells import Y

L, P = array()
W = {(x, Y[l], z): b for (x, l, z), b in L.B.items()}
print(len(L.B), "blocks")
cases = [(0, 0, 0), (0, 15, -16), (0, 15, 15), (-4096, 15, -16), (4095, 1, 1), (-1, 1, 1), (100, 7, -9)]
r = random.Random(3)
cases += [(r.randrange(-4096, 4096), r.randrange(16), r.randrange(-16, 16)) for _ in range(int(sys.argv[1]) if len(sys.argv) > 1 else 6)]
ok = 0
for A, x, w in cases:
    t0 = time.time(); S = Sim(W)
    for k, p in enumerate(P["A"]):
        if (A >> k) & 1: S.set((p[0], Y[0], p[2]), "redstone_block")
    for k, p in enumerate(P["w"]):
        if (w >> min(k, WB - 1)) & 1: S.set((p[0], Y[0], p[2]), "redstone_block")
    for i, p in enumerate(P["x"]):
        if (x >> i) & 1: S.set((p[0], Y[0], p[2]), "redstone_block")
    ticks = S.settle(800)
    bits = [int(S.power((p[0], Y[p[1]], p[2])) > 0) for p in P["out"]]
    v = sum(b << j for j, b in enumerate(bits)); v -= (1 << NB) * (v >= 1 << (NB - 1))
    good = v == expected(A, x, w); ok += good
    print(f"A={A:6d} x={x:2d} w={w:3d} -> {v:6d} want {expected(A, x, w):6d} {'OK' if good else 'WRONG'} ticks {ticks} ({time.time()-t0:.0f}s)")
print(f"{ok}/{len(cases)}"); raise SystemExit(ok != len(cases))
