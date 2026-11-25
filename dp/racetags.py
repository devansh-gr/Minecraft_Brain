"""Floating tags over the 8 competition lamp bars (z -5..-19): the region's plain name and how many of its
15 lamps are lit right now, counted from the lamp blocks every 4 ticks while a run is in progress."""
import json
from .common import *

PLAIN = {"prefrontal": "Judgment", "broca": "Speech", "motor": "Movement", "somato": "Touch",
         "parietal": "Math", "temporal": "Memory", "occipital": "Vision", "cerebellum": "Balance"}


def emit(c):
    w, R, cx = c.w, c.R, c.cx
    init = ["kill @e[type=text_display,tag=race]"]
    for r in R:
        init.append(f'summon text_display {cx[r] + 0.5} {L0 + 1.6} -12.5 {{billboard:"center",line_width:120,'
                    f'background:1342177280,text:{json.dumps(PLAIN[r] + chr(10) + "0 lamps")},'
                    f'Tags:["ui","race","race_{r}"],transformation:{{left_rotation:[0f,0f,0f,1f],'
                    f'right_rotation:[0f,0f,0f,1f],translation:[0f,0f,0f],scale:[0.9f,0.9f,0.9f]}}}}')
    w("race/init", init)
    upd = []
    for r in R:
        upd.append("scoreboard players set #c brain.t 0")
        upd += [f"execute if block {cx[r]} {L0} {z} redstone_lamp[lit=true] run scoreboard players add #c brain.t 1"
                for z in range(-5, -20, -1)]
        upd += [f"execute if score #c brain.t matches {n} run data modify entity @e[type=text_display,tag=race_{r},limit=1] "
                f"text set value {json.dumps(PLAIN[r] + chr(10) + (f'{n} lamp' if n == 1 else f'{n} lamps'))}"
                for n in range(16)]
    w("race/update", upd)
    w("race/tick", ["scoreboard players add #rt brain.t 1",
                    "execute if score #rt brain.t matches 4.. run function brain:race/update",
                    "execute if score #rt brain.t matches 4.. run scoreboard players set #rt brain.t 0"])
