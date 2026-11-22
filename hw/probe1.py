"""Probe redstone facts the layout depends on."""
from rs import *
clear(-2, -2, 30, 12)
B = {}
# 1) repeater on glass, facing convention: source block at x=0, repeater at x=1 'facing west' should carry east
B[(0, -59, 0)] = "glass"; B[(1, -59, 0)] = "glass"; B[(2, -59, 0)] = "glass"
B[(1, -58, 0)] = "repeater[facing=west]"; B[(2, -58, 0)] = "redstone_wire"
# 2) dust ramp up onto glass: floor dust at z=2 x=0..1, stone at x=2 with dust on top (L1), glass at x=3 L1 with dust on L2
for x in (0, 1): B[(x, -60, 2)] = "redstone_wire"
B[(2, -60, 2)] = "stone"; B[(2, -59, 2)] = "redstone_wire"
B[(3, -59, 2)] = "glass"; B[(3, -58, 2)] = "redstone_wire"; B[(4, -59, 2)] = "glass"; B[(4, -58, 2)] = "redstone_wire"
# 3) crossing: lane on L2 over glass along x at z=4 (x=0..6), column dust on L0 along z at x=3 (z=2..6) under it
for x in range(8, 15): B[(x, -59, 4)] = "glass"; B[(x, -58, 4)] = "redstone_wire"
for z in range(1, 8): B[(11, -60, z)] = "redstone_wire"
# 4) NOR: lane dust into stone block at L2, wall torch on its south face
B[(20, -59, 4)] = "glass"; B[(20, -58, 4)] = "redstone_wire"; B[(21, -58, 4)] = "stone"
B[(21, -58, 5)] = "redstone_wall_torch[facing=south]"
B[(21, -59, 6)] = "stone"; B[(21, -58, 6)] = "redstone_wire"
place(B); settle()
print("idle: rep-out", power(2, -58, 0), "ramp top", power(4, -58, 2), "lane", power(14, -58, 4), "col", power(11, -60, 7), "torch-out", power(21, -58, 6))
cmd("setblock 0 -58 0 redstone_block"); cmd("setblock -1 -60 2 redstone_block"); cmd("setblock 7 -58 4 redstone_block"); settle()
print("A on: rep-out", power(2, -58, 0), "ramp top", power(4, -58, 2), "lane", power(14, -58, 4), "col", power(11, -60, 7))
cmd("setblock 11 -60 0 redstone_block"); cmd("setblock 7 -58 4 air"); settle()
print("col on, lane off: lane", power(14, -58, 4), "col", power(11, -60, 7))
cmd("setblock 19 -58 4 redstone_block"); settle()
print("NOR input on: torch-out", power(21, -58, 6), "torch lit", "passed" in cmd("execute if block 21 -58 5 redstone_wall_torch[lit=true]"))
