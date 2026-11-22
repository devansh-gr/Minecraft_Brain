import itertools, time
from rs import *
from cells import xor_cell, at, Y
B, feed, out = xor_cell()
x0, z0 = 200, 0
clear(x0 - 4, z0 - 6, x0 + 10, z0 + 10)
W = at(B, x0, z0)
place(W)
def src(k, on):
    dx, l, dz = feed[k]
    if l == 2:
        cmd(f"setblock {x0+dx} {Y[1]} {z0+dz} glass")
    cmd(f"setblock {x0+dx} {Y[l]} {z0+dz} {'redstone_block' if on else 'air'}")
print(len(W), "blocks")
for a, b in itertools.product([0, 1], repeat=2):
    src("a", a); src("b", b); time.sleep(1.5)
    o = power(x0 + out[0], Y[out[1]], z0 + out[2])
    print(a, b, "->", o, "OK" if (o > 0) == (a != b) else "WRONG")
