"""RCON I/O for the in-game MAC at (X0, Z0): input blocks, latch readout, clock, MSPT. No arithmetic."""
import re, time
from rs import cmd
from mac import system, NB, PX
X0, Z0 = 1000, 0
Y = {l: -60 + l for l in range(6)}
L, P = system()
def at(p): return (p[0] + X0, Y[p[1]], p[2] + Z0)
def src(p, on):
    x, y, z = at(p)
    if p[1] == 2: cmd(f"setblock {x} {y-1} {z} glass")
    cmd(f"setblock {x} {y} {z} {'redstone_block' if on else 'air'}")
def latch(j):
    x, y, z = at((1 - PX * j, 0, -7)); return "passed" in cmd(f"execute if block {x} {y} {z} repeater[powered=true]")
def A():
    v = sum(latch(j) << j for j in range(NB)); return v - (1 << NB) * (v >= 1 << (NB - 1))
def setin(x, w):
    for i, p in enumerate(P["x"]): src(p, (x >> i) & 1)
    for k, p in enumerate(P["w"]): src(p, (w >> k) & 1)
def go(hold=1.0):
    src(P["go"], 1); time.sleep(hold); src(P["go"], 0)
def reset(wait=15):
    src(P["rst"], 1); time.sleep(wait); go(); time.sleep(wait); src(P["rst"], 0)
def tickstats():
    t = cmd("tick query"); g = lambda k: float(re.search(k + r":\s*([\d.]+)ms", t).group(1))
    return g("P50"), g("P95"), g("P99")
