"""Physical multiplier: 4-bit unsigned x times 5-bit signed lever weight w -> 9-bit signed product."""
import random, sys, itertools, time
from nor import Net, compile2, simulate
from arith import mul_us
net = Net()
X = [f"x{b}" for b in range(4)]; Wb = [f"w{b}" for b in range(5)]
P = mul_us(net, X, Wb, 9)
outs = [p for p in P if p not in ("0", "1")]
B, src, probe = compile2(net.gates, X + Wb, set(outs))
xs = [p[0] for p in B]; zs = [p[2] for p in B]
print(f"{len(net.gates)} gates, {len(B)} blocks, footprint {max(xs)-min(xs)+1} x {max(zs)-min(zs)+3}")
# python check of the netlist first
for x, w in itertools.product(range(16), range(-16, 16)):
    v = simulate(net.gates, {**{X[b]: (x >> b) & 1 for b in range(4)}, **{Wb[b]: ((w & 31) >> b) & 1 for b in range(5)}})
    r = sum(v[p] << b for b, p in enumerate(P)); r -= 512 * (r >= 256)
    assert r == x * w, (x, w, r)
print("netlist exact for all 512 cases")
if "--build" in sys.argv:
    from rs import *
    if "--fresh" in sys.argv:
        clear(min(xs) - 2, min(zs) - 4, max(xs) + 2, max(zs) + 2)
        place(B)
    else:
        relight(B)
    time.sleep(5)
    rnd = random.Random(7); cases = [(15, -16), (15, 15), (0, -16), (1, -1)] + [(rnd.randint(0, 15), rnd.randint(-16, 15)) for _ in range(int(sys.argv[-1]))]
    ok = 0
    for x, w in cases:
        for b in range(4): cmd("setblock %d %d %d %s" % (*src[X[b]], "redstone_block" if (x >> b) & 1 else "stone"))
        for b in range(5): cmd("setblock %d %d %d %s" % (*src[Wb[b]], "redstone_block" if ((w & 31) >> b) & 1 else "stone"))
        t0 = time.time(); t_ok = None
        while time.time() - t0 < int(sys.argv[-2]):
            time.sleep(1)
            r = sum((power(*probe[p]) > 0) << b for b, p in enumerate(P) if p in probe); r -= 512 * (r >= 256)
            if r == x * w and t_ok is None: t_ok = time.time() - t0
            if r != x * w: t_ok = None
        print(f"  correct from {t_ok if t_ok is None else round(t_ok)} s", end="")
        ok += r == x * w
        print(f"x={x:2d} w={w:3d} redstone={r:4d} expected={x*w:4d}", "OK" if r == x * w else "WRONG")
    print(f"{ok}/{len(cases)} physical cases correct")
    raise SystemExit(ok != len(cases))
