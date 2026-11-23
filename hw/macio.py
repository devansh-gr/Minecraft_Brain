"""RCON I/O for the in-game MAC at (X0, Z0): input blocks, latch readout, clock, MSPT. No arithmetic."""
import re, time
from rs import cmd
from mac import system, NB, PX
import os
CSA = os.environ.get("MAC_CSA") == "1"
X0, Z0 = (1000, 400) if CSA else (1000, 0)
Y = {l: -60 + l for l in range(6)}
L, P = system(CSA)
def at(p): return (p[0] + X0, Y[p[1]], p[2] + Z0)
def src(p, on):
    x, y, z = at(p)
    if p[1] == 2: cmd(f"setblock {x} {y-1} {z} glass")
    cmd(f"setblock {x} {y} {z} {'redstone_block' if on else 'air'}")
def latch(j):
    x, y, z = at((1 - PX * j, 0, -7)); return "passed" in cmd(f"execute if block {x} {y} {z} repeater[powered=true]")
def clatch(j):
    x, y, z = at((6 - PX * j, 0, -7)); return "passed" in cmd(f"execute if block {x} {y} {z} repeater[powered=true]")
def C():
    return sum(clatch(j) << j for j in range(4, NB)) if CSA else 0
def A():
    """Binary value held in the S latches. In CSA mode call flush() first so the carry register is 0."""
    v = sum(latch(j) << j for j in range(NB)); return v - (1 << NB) * (v >= 1 << (NB - 1))
def flush(D=12, n=4):
    """Physical carry resolution: n ops with x=0 move pending carries up 4 bits each until C = 0."""
    setin(0, 0)
    for _ in range(n): time.sleep(D); go()
    time.sleep(D)
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

def build():
    from rs import place
    W = {(x + X0, Y[l], z + Z0): b for (x, l, z), b in L.B.items()}
    xs = [p[0] for p in W]; zs = [p[2] for p in W]
    bx = (min(xs) - 2, max(xs) + 2); bz = (min(zs) - 2, max(zs) + 2)
    for x in range(bx[0], bx[1] + 1, 128):                       # <= 256 chunks per forceload command
        for z in range(bz[0], bz[1] + 1, 128):
            r = cmd(f"forceload add {x} {z} {min(x + 127, bx[1])} {min(z + 127, bz[1])}")
            assert "rror" not in r and "too many" not in r.lower(), r
    time.sleep(3)
    for y in range(-52, -61, -1):
        for x in range(bx[0], bx[1] + 1, 200):
            for z in range(bz[0], bz[1] + 1, 160):
                cmd(f"fill {x} {y} {z} {min(x + 199, bx[1])} {y} {min(z + 159, bz[1])} air")
    place(W)
    missing = [p for p, b in list(W.items())[::97] if "passed" not in cmd("execute if block %d %d %d %s" % (*p, b.split("[")[0]))]
    assert not missing, ("blocks missing after build", missing[:5])
    return len(W), bx[1] - bx[0] - 3, bz[1] - bz[0] - 3
