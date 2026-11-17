"""Supervised bounded update of hidden->output synapses."""
import json, math
from .common import *


def emit(c):
    w, R, N, J, ri, cx, hx, hname, W, V, feeds, col, lc, kw, lever_region, lever_syn, lever_axon, lever, lamp, status, bar = (c.w, c.R, c.N, c.J, c.ri, c.cx, c.hx, c.hname, c.W, c.V, c.feeds, c.col, c.lc, c.kw, c.lever_region, c.lever_syn, c.lever_axon, c.lever, c.lamp, c.status, c.bar)
    # ---------------- plasticity (hidden -> output synapses only)
    for t in range(N):
        tl = ["scoreboard players set #up brain.t 0", "scoreboard players set #dn brain.t 0",
              "scoreboard players set #4 brain.t 4"]
        for j in range(J):
            tl += [f"scoreboard players operation #dl brain.t = h{j} brain.n", "scoreboard players add #dl brain.t 3",
                   "scoreboard players operation #dl brain.t /= #4 brain.t",
                   f"execute if score h{j} brain.n matches 1.. run scoreboard players operation V{j}_{t} brain.w += #dl brain.t",
                   f"execute if score h{j} brain.n matches 1.. run scoreboard players add #up brain.t 1",
                   f"execute if score V{j}_{t} brain.w matches {V_MAX+1}.. run scoreboard players set V{j}_{t} brain.w {V_MAX}"]
            for k in range(N):
                if k == t:
                    continue
                tl += [f"execute if score h{j} brain.n matches 1.. if score o{k} brain.n >= o{t} brain.n "
                       f"if score o{k} brain.n matches 1.. run function brain:learn/dep {{j:{j},k:{k}}}"]
        tl += ["scoreboard players add #trains brain.st 1",
               'data modify storage brain:mem list[0].tr set value " [trained]"', "function brain:mem/show",
               f'data modify storage brain:a tname set value "{NAMES[R[t]]}"', "function brain:learn/report"]
        w(f"learn/t{t}", tl)
    w("learn/dep", [f"$scoreboard players operation V$(j)_$(k) brain.w -= #dl brain.t",
                    f"$execute if score V$(j)_$(k) brain.w matches ..{V_MIN-1} run scoreboard players set V$(j)_$(k) brain.w {V_MIN}",
                    "scoreboard players add #dn brain.t 1"])
    w("learn/report", ["execute store result storage brain:a up int 1 run scoreboard players get #up brain.t",
                       "execute store result storage brain:a dn int 1 run scoreboard players get #dn brain.t",
                       "execute store result storage brain:a n int 1 run scoreboard players get #trains brain.st",
                       "function brain:learn/report_m with storage brain:a"])
    w("learn/report_m", ['$data modify entity @e[type=text_display,tag=train,limit=1] text set value '
                         '"TRAINED -> $(tname)\\n+ $(up) synapses strengthened\\n- $(dn) weakened\\n$(n) updates since reset"'])
    train = ["execute if score #state brain.st matches 1 run return 0",
             "execute unless score #has brain.st matches 1 run return 0",
             f"execute unless block {lever('learn')} run return run "
             'data modify entity @e[type=text_display,tag=train,limit=1] text set value "LEARNING IS OFF\\nflip the LEARN lever"',
             "execute if score #target brain.st matches -1 run return run "
             'data modify entity @e[type=text_display,tag=train,limit=1] text set value "PICK A TARGET REGION\\n(colored buttons)"']
    train += [f"execute if score #target brain.st matches {t} run function brain:learn/t{t}" for t in range(N)]
    train += ["playsound minecraft:block.amethyst_block.chime master @a ~ ~ ~ 1 1.2"]
    w("ui/train", train)
    w("ui/reset_learning", ["function brain:net/reset_weights",
                            'data modify entity @e[type=text_display,tag=train,limit=1] text set value "WEIGHTS RESET\\nto baseline"'])
    for t in range(N):
        w(f"ui/target{t}", [f"scoreboard players set #target brain.st {t}"]
          + [lamp(cx[R[k]], TZ - 1, k == t) for k in range(N)]
          + [f'data modify entity @e[type=text_display,tag=train,limit=1] text set value "TARGET: {NAMES[R[t]]}\\npress TRAIN"'])

