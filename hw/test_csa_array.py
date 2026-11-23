"""Carry-save array in the simulator: (S, C) + x*w -> (S', C'), check S'+C' and settle time vs the ripple array."""
import random, sys
from rsim import Sim
from mac import array, NB, PX, PZ, WB
Y = {l: -60 + l for l in range(6)}
M = 1 << NB
L, P = array(csa=True)
W = {(x, Y[l], z): b for (x, l, z), b in L.B.items()}
cpin = [(3 - PX * k, 0, -2) for k in range(NB)]
cout = {k + 4: (3 - PX * k, 0, 130) for k in range(NB - 4)}
r = random.Random(2); ok = 0; worst = 0
cases = [(M - 1, 0, 1, 1), (0, 0, 15, -16), (0, 0, 15, 15)] + [(r.randrange(M), r.randrange(M) & ~15, r.randrange(16), r.randrange(-16, 16)) for _ in range(int(sys.argv[1]) if len(sys.argv) > 1 else 5)]
for Sv, Cv, x, w in cases:
    S = Sim(W)
    def on(p): S.set((p[0], Y[0], p[2]), "redstone_block")
    for k in range(NB):
        if (Sv >> k) & 1: on(P["A"][k])
        if (Cv >> k) & 1: on(cpin[k])
        if (w >> min(k, WB - 1)) & 1: on(P["w"][k])
    for i in range(4):
        if (x >> i) & 1: on(P["x"][i])
    t = S.settle(800); worst = max(worst, t)
    s2 = sum(int(S.power((p[0], Y[0], p[2])) > 0) << j for j, p in enumerate(P["out"]))
    c2 = sum(int(S.power((p[0], Y[0], p[2])) > 0) << j for j, p in cout.items())
    good = (s2 + c2) % M == (Sv + Cv + x * w) % M; ok += good
    print(f"S={Sv:5d} C={Cv:5d} x={x:2d} w={w:3d}: S'+C'={(s2+c2)%M:5d} want {(Sv+Cv+x*w)%M:5d} {'OK' if good else 'WRONG'} ticks {t}")
print(f"{ok}/{len(cases)} worst settle {worst} rt ({len(L.B)} blocks)"); raise SystemExit(ok != len(cases))
