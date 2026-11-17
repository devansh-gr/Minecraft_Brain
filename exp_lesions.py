"""Phase 3 experiments with physical readouts. Lesioned region = whatever the intact run physically selects."""
import json
from rcon import cmd
import test as T
R, EXP = T.R, T.EXP
Q = ["what color is", "the sky when i", "feel sad and", "hear music?"]
out = {}
def run(tag):
    T.idle(); T.ask(Q, wait=20)
    r = dict(o=T.vec("o"), fired=T.fired(), lit=T.lit_regions(), status=T.status().strip('"'),
             blocked_lamp=T.lamp_on(30), delivered_lamp=T.lamp_on(28))
    out[tag] = r; print(f"{tag:28s} o={r['o']} fired={r['fired']} lit={r['lit']} BLOCKED={r['blocked_lamp']} status={r['status']}")
    return r
cmd("function brain:ui/reset_learning"); cmd("function brain:ui/repair")
# --- mandatory axon experiment (steps 1-8)
a = run("1-2 intact"); win = a["fired"][0]; x = EXP[win]["x"]
T.lever(x + 2, 12, True); run("3-5 axon cut")
T.lever(x + 2, 12, False); run("6-8 axon repaired")
# --- region lesion: computation changes, runner-up wins
T.lever(x, -21, True); run("region lesion"); T.lever(x, -21, False)
# --- synapse lesion + recovery by training the lesioned region
T.lever(x, -46, True); s = run("synapse lesion")
cmd(f"function brain:ui/target{R.index(win)}"); T.lever(10, -74, True)
for n in range(3):
    cmd("function brain:ui/train"); run(f"synapse lesion + TRAIN x{n+1}")
T.lever(10, -74, False); T.lever(x, -46, False); cmd("function brain:ui/reset_learning"); run("repaired + weights reset")
out["lesioned_region"] = win
json.dump(out, open("build/phase3.json", "w"), indent=1)
