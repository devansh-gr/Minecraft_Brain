"""Repeater-lock D latch: data repeater R is locked by clock repeater L pointing into its side."""
import time
from rs import *
x0, y, z0 = 240, -60, 40
clear(x0 - 4, z0 - 2, x0 + 2, z0 + 4)
place({(x0, y, z0 + 1): "repeater[facing=north]", (x0 - 1, y, z0 + 1): "repeater[facing=west]",
       (x0, y, z0 + 2): "redstone_wire", (x0, y, z0 + 3): "redstone_wire"})
def d(v): cmd(f"setblock {x0} {y} {z0} {'redstone_block' if v else 'air'}")
def clk(v): cmd(f"setblock {x0-2} {y} {z0+1} {'redstone_block' if v else 'air'}")
def q(): time.sleep(0.6); return int(power(x0, y, z0 + 3) > 0)
steps = [("clk0 d1", 0, 1, 1), ("clk0 d0", 0, 0, 0), ("d1", None, 1, 1), ("lock, d0", 1, 0, 1),
         ("unlock", 0, None, 0), ("lock at 0", 1, None, 0), ("locked, d1", None, 1, 0), ("unlock", 0, None, 1)]
ok = 0
for name, c, dv, want in steps:
    if c is not None: clk(c); time.sleep(0.3)
    if dv is not None: d(dv)
    got = q(); ok += got == want
    print(f"{name:14s} q={got} want={want}", "OK" if got == want else "WRONG")
print(f"{ok}/{len(steps)}"); raise SystemExit(ok != len(steps))
