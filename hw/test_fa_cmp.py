import itertools, time
from rs import *
from cells import fa_cell, at, Y
B, feed, out = fa_cell()
x0, z0 = 200, 40
clear(x0 - 4, z0 - 6, x0 + 26, z0 + 20)
W = at(B, x0, z0)
place(W)
def src(k, on):
    dx, l, dz = feed[k]
    if l == 2:
        cmd(f"setblock {x0+dx} {Y[1]} {z0+dz} glass")
    cmd(f"setblock {x0+dx} {Y[l]} {z0+dz} {'redstone_block' if on else 'air'}")
xs = [d for d, _, _ in B]; zs = [d for _, _, d in B]
print(len(W), "blocks, footprint", max(xs) - min(xs) + 1, "x", max(zs) - min(zs) + 1)
ok = 0
for a, b, c in itertools.product([0, 1], repeat=3):
    src("a", a); src("b", b); src("c", c); time.sleep(2)
    s, co = (power(x0 + p[0], Y[p[1]], z0 + p[2]) > 0 for p in out.values())
    good = (s, co) == ((a + b + c) & 1, (a + b + c) >> 1)
    ok += good
    print(a, b, c, "-> s", int(s), "cout", int(co), "OK" if good else "WRONG")
print(f"{ok}/8 correct")
