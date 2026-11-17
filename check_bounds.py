"""Bounds under every weight configuration the plasticity rule permits (V in [-8,12], W and c fixed)."""
import json, random, time
from reference import forward
from rcon import cmd
import test as T
random.seed(7)

def baseW():
    W = [[T.score(f"W{i}_{j}", "brain.w") for j in range(16)] for i in range(8)]
    return W
W = baseW(); b = [0]*16; c = [0]*8
# 1. reference fuzz: extremes + random, track the largest |pre-clamp sum|
worst, bad = 0, 0
confs = [("all 12", lambda: 12), ("all -8", lambda: -8), ("random", lambda: random.randint(-8, 12)),
         ("alternating", None)]
for t in range(20000):
    kind = t % 4
    V = [[(12 if kind == 0 else -8 if kind == 1 else random.randint(-8, 12) if kind == 2 else (12 if (j+k) % 2 else -8))
          for k in range(8)] for j in range(16)]
    x = [random.choice([0, 15]) if t % 3 else random.randint(0, 15) for _ in range(8)]
    h, o = forward(x, W, b, V, c)
    s = [sum(V[j][k]*h[j] for j in range(16)) for k in range(8)]
    worst = max(worst, max(abs(v) for v in s))
    bad += not (all(0 <= v <= 15 for v in h) and all(0 <= v <= 15 for v in o))
print(f"reference fuzz: 20000 configs, out-of-range activations: {bad}, largest |pre-clamp output sum|: {worst} (analytic max 2880)")

# 2. in-game: extreme weights, all inputs 15, via memory replay (game computes, reference checks)
def ingame(Vfill, label):
    T.idle()
    for j in range(16):
        for k in range(8):
            cmd(f"scoreboard players set V{j}_{k} brain.w {Vfill(j, k)}")
    cmd('data modify storage brain:mem list prepend value {q:"bounds test ",x:[15,15,15,15,15,15,15,15],o:[0,0,0,0,0,0,0,0],win:"",les:"",tr:""}')
    cmd("function brain:ui/replay0")
    while (T.score("#t", "brain.st") or 0) < 62: time.sleep(0.3)
    x, h, o = T.vec("x"), T.vec("h", 16), T.vec("o")
    V = [[T.score(f"V{j}_{k}", "brain.w") for k in range(8)] for j in range(16)]
    hr, orf = forward(x, baseW(), b, V, c)
    ok = h == hr and o == orf and all(0 <= v <= 15 for v in h + o)
    print(f"in-game {label:12s} x=15: h={h} o={o} matches reference: {h == hr and o == orf}, in range: {all(0 <= v <= 15 for v in h + o)}")
    return ok
res = [ingame(lambda j, k: 12, "all V=12"), ingame(lambda j, k: -8, "all V=-8"),
       ingame(lambda j, k: 12 if (j + k) % 2 else -8, "alternating")]
T.idle(); cmd("function brain:ui/reset_learning")

# 3. in-game plasticity fuzz: 400 TRAIN updates with maximal activations and random targets
cmd("function brain:ui/replay0")       # x all 15 again -> largest deltas
while T.score("#state", "brain.st") == 1 and (T.score("#t", "brain.st") or 0) < 62: time.sleep(0.3)
T.idle()
for n in range(400):
    cmd(f"function brain:learn/t{random.randrange(8)}")
V = [T.score(f"V{j}_{k}", "brain.w") for j in range(16) for k in range(8)]
print(f"in-game 400 TRAIN updates: V range [{min(V)}, {max(V)}], all within [-8, 12]: {all(-8 <= v <= 12 for v in V)}; "
      f"distinct values used: {sorted(set(V))}")
cmd("function brain:ui/reset_learning"); cmd("data remove storage brain:mem list[0]"); cmd("function brain:mem/show")
json.dump(dict(fuzz_bad=bad, worst=worst, ingame=res, train_range=[min(V), max(V)]), open("build/bounds.json", "w"))
