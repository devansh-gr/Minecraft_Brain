"""Accumulator loop in the simulator: reset, then back-to-back A <- A + x*w ops. A is read only from the latch repeaters."""
import random, sys, time
from rsim import Sim
from mac import system, expected, NB, PX, WB
Y = {l: -60 + l for l in range(6)}
L, P = system()
S = Sim({(x, Y[l], z): b for (x, l, z), b in L.B.items()})
def at(p): return (p[0], Y[p[1]], p[2])
def src(p, on):
    if p[1] == 2: S.set((p[0], Y[1], p[2]), "glass")
    S.set(at(p), "redstone_block" if on else "air")
def A():
    v = sum(int(S.out[(1 - PX * j, Y[0], -7)] > 0) << j for j in range(NB)); return v - (1 << NB) * (v >= 1 << (NB - 1))
def pulse():
    src(P["go"], 1); t1 = S.settle(1500); src(P["go"], 0); t2 = S.settle(1500); return t1, t2
def setin(x, w):
    for i, p in enumerate(P["x"]): src(p, (x >> i) & 1)
    for k, p in enumerate(P["w"]): src(p, (w >> k) & 1)
src(P["rst"], 1); setin(0, 0); S.settle(1500); pulse(); src(P["rst"], 0); S.settle(1500)
print("after reset A =", A())
r = random.Random(int(sys.argv[2]) if len(sys.argv) > 2 else 5)
ops = [(15, -16), (15, 15), (7, -9), (1, 1)] + [(r.randrange(16), r.randrange(-16, 16)) for _ in range(int(sys.argv[1]) if len(sys.argv) > 1 else 4)]
acc = 0; ok = A() == 0
for x, w in ops:
    t0 = time.time(); setin(x, w); ts = S.settle(1500); tp = pulse()
    acc = expected(acc, x, w); got = A(); ok += got == acc
    print(f"x={x:2d} w={w:3d} -> A={got:6d} want {acc:6d} {'OK' if got == acc else 'WRONG'} settle {ts} rt, pulse {tp} ({time.time()-t0:.0f}s)")
print(f"{ok}/{len(ops) + 1}"); raise SystemExit(ok != len(ops) + 1)
