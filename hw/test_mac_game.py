"""In-game MAC: build (--build), physical reset, back-to-back A <- A + x*w.
Commands only set x/w/GO/RST input blocks and read latch states; arithmetic and storage are redstone."""
import random, re, sys, time
from rs import cmd, place
from mac import system, expected, NB, PX, zrow
X0, Z0 = 1000, 0
Y = {l: -60 + l for l in range(6)}
L, P = system()
W = {(x + X0, Y[l], z + Z0): b for (x, l, z), b in L.B.items()}
xs = [p[0] for p in W]; zs = [p[2] for p in W]
bx = (min(xs) - 2, max(xs) + 2); bz = (min(zs) - 2, max(zs) + 2)
def at(p): return (p[0] + X0, Y[p[1]], p[2] + Z0)
if "--build" in sys.argv:
    for x in range(bx[0], bx[1] + 1, 240):
        print(cmd(f"forceload add {x} {bz[0]} {min(x + 239, bx[1])} {bz[1]}"))
    for y in range(-52, -61, -1):
        for x in range(bx[0], bx[1] + 1, 200):
            for z in range(bz[0], bz[1] + 1, 160):
                cmd(f"fill {x} {y} {z} {min(x + 199, bx[1])} {y} {min(z + 159, bz[1])} air")
    t = time.time(); place(W); print(f"built {len(W)} blocks in {time.time()-t:.0f}s, footprint {bx[1]-bx[0]-3} x {bz[1]-bz[0]-3}")
def src(p, on):
    x, y, z = at(p)
    if p[1] == 2: cmd(f"setblock {x} {y-1} {z} glass")
    cmd(f"setblock {x} {y} {z} {'redstone_block' if on else 'air'}")
def latch(j):
    x, y, z = at((1 - PX * j, 0, -7)); return "passed" in cmd(f"execute if block {x} {y} {z} repeater[powered=true]")
def A():
    v = sum(latch(j) << j for j in range(NB)); return v - (1 << NB) * (v >= 1 << (NB - 1))
def dbits():
    return tuple("passed" in cmd("execute if block %d %d %d redstone_wire[power=0]" % at((1 - PX * j, 0, -8))) for j in range(NB))
def wait_stable(limit=60, min_wait=22):
    """Poll the latch inputs; return time of the last change once quiet for 4 s and past min_wait (sim worst case 17 s)."""
    t0 = time.time(); last = None; tl = 0
    while time.time() - t0 < limit:
        b = dbits()
        if b != last: last = b; tl = time.time() - t0
        if time.time() - t0 > min_wait and time.time() - t0 - tl > 4: return tl
        time.sleep(0.5)
    return None
def mspt():
    m = re.search(r"([\d.]+)\s*ms", cmd("tick query")); return float(m.group(1)) if m else None
def pulse():
    src(P["go"], 1); time.sleep(1.5); src(P["go"], 0); return wait_stable()
def setin(x, w):
    for i, p in enumerate(P["x"]): src(p, (x >> i) & 1)
    for k, p in enumerate(P["w"]): src(p, (w >> k) & 1)
src(P["rst"], 1); setin(0, 0); wait_stable(); pulse(); src(P["rst"], 0); time.sleep(1)
a0 = A(); print("after physical reset A =", a0)
r = random.Random(7)
n = int(sys.argv[sys.argv.index("--ops") + 1]) if "--ops" in sys.argv else 8
ops = [(15, -16), (15, 15), (7, -9), (1, 1), (0, 13)] + [(r.randrange(16), r.randrange(-16, 16)) for _ in range(n)]
if "--overflow" in sys.argv: ops = [(15, 15)] * 19 + [(15, -16)] * 2
acc = 0; ok = int(a0 == 0)
for x, w in ops:
    setin(x, w); t_s = wait_stable(); t_p = pulse(); m = mspt()
    acc = expected(acc, x, w); got = A(); ok += got == acc
    print(f"x={x:2d} w={w:3d} -> A={got:6d} want {acc:6d} {'OK' if got == acc else 'WRONG'}  settle {t_s:.1f}s  writeback {t_p:.1f}s  mspt {m}", flush=True)
print(f"{ok}/{len(ops) + 1} correct"); raise SystemExit(ok != len(ops) + 1)
