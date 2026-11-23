"""Exhaustive in-game test of a 9-NOR full adder built by nor.py."""
import itertools, time
from rs import *
from nor import Net, compile
n = Net(); s, c = n.fa("a", "b", "cin")
B, src, probe = compile(n.gates, ["a", "b", "cin"], x0=0, z0=0)
xs = [p[0] for p in B]; zs = [p[2] for p in B]
print(f"{len(n.gates)} gates, {len(B)} blocks, footprint {max(xs)-min(xs)+1} x {max(zs)-min(zs)+3}")
clear(min(xs) - 2, min(zs) - 4, max(xs) + 2, max(zs) + 2)
place(B)
ok = 0
for a, b, ci in itertools.product([0, 1], repeat=3):
    for k, v in zip(["a", "b", "cin"], [a, b, ci]):
        cmd("setblock %d %d %d %s" % (*src[k], "redstone_block" if v else "stone"))
    settle(60)
    got = (power(*probe[s]) > 0, power(*probe[c]) > 0)
    want = ((a + b + ci) % 2 == 1, a + b + ci >= 2)
    ok += got == want
    print(a, b, ci, "->", int(got[0]), int(got[1]), "OK" if got == want else "WRONG")
print(f"{ok}/8")
raise SystemExit(ok != 8)
