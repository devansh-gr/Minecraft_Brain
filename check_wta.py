"""Exercise the physical comparator WTA directly through the barrels (no network, no ramp)."""
import json, random, time
from rcon import cmd
import test as T
random.seed(3)
xs = [T.EXP[r]["x"] for r in T.CH]          # physical channels 1..8

def fill(level, z, v):
    for x, s in zip(xs, v):
        cmd(f"function brain:fill/s{s} {{x:{x},y:{level},z:{z}}}")

def run(v):
    fill(-59, 1, [0]*8); fill(-60, 2, [0]*8); time.sleep(1.5)
    fill(-60, 2, v); time.sleep(5)                       # inhibition first: max chain settles
    fill(-59, 1, v); time.sleep(1.5)                     # then excitation
    dec = [int(cmd(f"data get block {x} -59 2 OutputSignal").split(": ")[-1]) for x in xs]
    heads = [int("passed" in cmd(f"execute if block {x} -59 3 repeater[powered=true]")) for x in xs]
    M = int(cmd("data get block 32 -60 -1 OutputSignal").split(": ")[-1])
    return dec, heads, M

V = [("all zero", [0]*8)]
V += [(f"one-hot ch{c+1}", [9 if i == c else 0 for i in range(8)]) for c in range(8)]
for c in range(8):
    v = [random.randint(1, 13) for _ in range(8)]; v[c] = 14
    V.append((f"unique max ch{c+1}", v))
V += [("tie ch2+ch3 (spec)", [2, 11, 11, 4, 7, 3, 1, 6]), ("tie ch1+ch8", [12, 3, 5, 7, 2, 9, 4, 12]),
      ("3-way tie ch2,5,7", [1, 10, 4, 3, 10, 6, 10, 2]), ("8-way tie at 7", [7]*8), ("8-way tie at 15", [15]*8),
      ("8-way tie at 1", [1]*8), ("15 vs 14", [14, 15, 14, 14, 14, 14, 14, 14]), ("spec unique", [2, 5, 11, 4, 7, 3, 1, 6])]
T.idle()
rows, passed = [], 0
for name, v in V:
    dec, heads, M = run(v)
    mx = max(v)
    want = [int(mx > 0 and s == mx) for s in v]
    ok = heads == want and M == mx and all(d == (s if w else 0) for d, s, w in zip(dec, v, want))
    passed += ok
    rows.append(dict(name=name, v=v, M=M, decision=dec, fired=heads, expected=want, ok=ok))
    print(f"{'PASS' if ok else 'FAIL'} {name:20s} v={v} M={M:2d} fired={heads}")
fill(-59, 1, [0]*8); fill(-60, 2, [0]*8)
print(f"{passed}/{len(V)} vectors correct")
json.dump(rows, open("build/wta.json", "w"), indent=1)
