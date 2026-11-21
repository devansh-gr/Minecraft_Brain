"""In-game check of the illuminated anatomy: each region injected alone must light every expected lamp of
that region and none of the other regions' lamps."""
import json, random, sys, time
from rcon import cmd
import test as T

E = json.load(open("build/expect.json"))
on = lambda p: "passed" in cmd("execute if block %d %d %d redstone_lamp[lit=true]" % tuple(p))
res = {}
for r in E:
    v = {f"c{i}": 0 for i in range(8)}
    v[f"c{T.CH.index(r)}"] = 15
    T.idle(); time.sleep(3)
    cmd("function brain:dbg/inject {" + ",".join(f"{k}:{x}" for k, x in v.items()) + "}")
    time.sleep(24)
    own = sum(on(p) for p in E[r]["lit"])
    others = [p for o in E if o != r for p in random.sample(E[o]["lit"], 150)]
    stray = sum(on(p) for p in others)
    res[r] = dict(expected=len(E[r]["lit"]), lit=own, other_checked=len(others), other_lit=stray)
    print(r, res[r]); sys.stdout.flush()
T.idle()
json.dump(res, open("build/anatomy.json", "w"), indent=1)
print("ALL OK" if all(x["lit"] == x["expected"] and x["other_lit"] == 0 for x in res.values()) else "MISMATCH")
