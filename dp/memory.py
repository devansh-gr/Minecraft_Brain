"""Working memory: record, display, replay."""
import json, math
from .common import *


def emit(c):
    w, R, N, J, ri, cx, hx, hname, W, V, feeds, col, lc, kw, lever_region, lever_syn, lever_axon, lever, lamp, status, bar = (c.w, c.R, c.N, c.J, c.ri, c.cx, c.hx, c.hname, c.W, c.V, c.feeds, c.col, c.lc, c.kw, c.lever_region, c.lever_syn, c.lever_axon, c.lever, c.lamp, c.status, c.bar)
    # ---------------- working memory (5 most recent)
    rec = ["data modify storage brain:a rec set value {x:[0,0,0,0,0,0,0,0],o:[0,0,0,0,0,0,0,0],tr:\"\",les:\"\"}",
           "data modify storage brain:a rec.q set from storage brain:a q",
           "data modify storage brain:a rec.win set from storage brain:a win",
           'execute if score #nwin brain.t matches 0 run data modify storage brain:a rec.win set value "none"']
    for i in range(N):
        rec += [f"execute store result storage brain:a rec.x[{i}] int 1 run scoreboard players get x{i} brain.n",
                f"execute store result storage brain:a rec.o[{i}] int 1 run scoreboard players get o{i} brain.n"]
    for i in range(N):
        for kind, f in [("region", lever_region), ("synapse", lever_syn), ("axon", lever_axon)]:
            rec.append(f'execute if block {f(i)} run data modify storage brain:a rec.les set value " [lesion]"')
    rec += ["execute unless score #inj brain.st matches 1 run data modify storage brain:mem list prepend from storage brain:a rec",
            "data remove storage brain:mem list[5]", "function brain:mem/show"]
    w("mem/record", rec)
    show = []
    for s in range(5):
        show += [f'data modify entity @e[type=text_display,tag=mem{s},limit=1] text set value "{s+1}. (empty)"',
                 f"function brain:mem/l{s} with storage brain:mem list[{s}]"]
        w(f"mem/l{s}", [f'$data modify entity @e[type=text_display,tag=mem{s},limit=1] text set value '
                        f'"{s+1}. $(q)-> $(win)$(les)$(tr)"'])
    w("mem/show", show)
    for s in range(5):
        w(f"ui/replay{s}", ["execute if score #state brain.st matches 1 run return 0",
                            f"execute unless data storage brain:mem list[{s}] run return 0",
                            f"data modify storage brain:a q set from storage brain:mem list[{s}].q"]
          + [f"execute store result score x{i} brain.n run data get storage brain:mem list[{s}].x[{i}]" for i in range(N)]
          + [f"scoreboard players set #replay brain.st {s}", "function brain:begin"])
    w("ui/memory", ['tellraw @p {"text":"WORKING MEMORY (newest first): q, input x[8], output o[8], winner","color":"aqua"}']
      + [f'tellraw @p {{"storage":"brain:mem","nbt":"list[{s}]","color":"gray"}}' for s in range(5)])

