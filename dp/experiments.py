"""Repair, demo and the five experiment presets."""
import json, math
from .common import *


def emit(c):
    w, R, N, J, ri, cx, hx, hname, W, V, feeds, col, lc, kw, lever_region, lever_syn, lever_axon, lever, lamp, status, bar = (c.w, c.R, c.N, c.J, c.ri, c.cx, c.hx, c.hname, c.W, c.V, c.feeds, c.col, c.lc, c.kw, c.lever_region, c.lever_syn, c.lever_axon, c.lever, c.lamp, c.status, c.bar)
    # ---------------- repair, demo, experiments
    rep = []
    for i in range(N):
        rep += [f"setblock {cx[R[i]]} {L1} -21 lever[face=floor,facing=north,powered=false]",
                f"setblock {cx[R[i]]} {L1} -46 lever[face=floor,facing=north,powered=false]",
                f"setblock {cx[R[i]]+2} {L1} 12 lever[face=floor,facing=north,powered=false]"]
    w("ui/repair", rep + ['data modify entity @e[type=text_display,tag=train,limit=1] text set value "ALL LESIONS REPAIRED"'])
    def setq(q):
        lines = (q + ["", "", "", ""])[:4]
        return "data merge block %d %d %d {front_text:{messages:%s}}" % (*SIGN, json.dumps(lines))
    demo = ["execute if score #state brain.st matches 1 run return 0", "scoreboard players add #demo brain.st 1",
            f"execute if score #demo brain.st matches {len(DEMO_QS)}.. run scoreboard players set #demo brain.st 0"]
    demo += [f"execute if score #demo brain.st matches {n} run {setq(q)}" for n, q in enumerate(DEMO_QS)]
    w("ui/demo", demo + ["function brain:ui/run"])
    w("ui/e1", ["function brain:ui/demo"])
    w("ui/e2", ["execute if score #state brain.st matches 1 run return 0", "scoreboard players add #e2 brain.st 1",
                "execute if score #e2 brain.st matches 2.. run scoreboard players set #e2 brain.st 0",
                "execute if score #e2 brain.st matches 1 run function brain:dbg/inject_a",
                "execute if score #e2 brain.st matches 0 run function brain:dbg/inject_b"])
    occ = R.index("occipital")
    w("ui/e3", [setq(E3_Q), f"function brain:ui/target{occ}",
                f"setblock {LEV['learn']} {L1} {CZ} lever[face=floor,facing=north,powered=true]",
                'data modify entity @e[type=text_display,tag=train,limit=1] text set value '
                '"EXP 3 READY: RUN, then TRAIN\\n(target Visual), then RUN again"'])
    w("ui/e4", [setq(E4_Q), "function brain:ui/repair",
                'data modify entity @e[type=text_display,tag=train,limit=1] text set value '
                '"EXP 4: RUN, then pull the\\nParietal AXON lever, RUN again,\\nrepair it, RUN again"'])
    par = R.index("parietal")
    w("ui/e5", [setq(E4_Q), "function brain:ui/repair",
                f"setblock {cx['parietal']} {L1} -46 lever[face=floor,facing=north,powered=true]",
                f"function brain:ui/target{par}",
                f"setblock {LEV['learn']} {L1} {CZ} lever[face=floor,facing=north,powered=true]",
                'data modify entity @e[type=text_display,tag=train,limit=1] text set value '
                '"EXP 5: Parietal direct synapse cut.\\nRUN, TRAIN (Parietal) x3, RUN"'])

