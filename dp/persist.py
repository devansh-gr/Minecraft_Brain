"""Scoreboards, storage maps and first-load weight initialisation."""
import json, math
from .common import *


def emit(c):
    w, R, N, J, ri, cx, hx, hname, W, V, feeds, feed_y, col, lc, kw, lever_region, lever_syn, lever_axon, lever, lamp, status, bar = (c.w, c.R, c.N, c.J, c.ri, c.cx, c.hx, c.hname, c.W, c.V, c.feeds, c.feed_y, c.col, c.lc, c.kw, c.lever_region, c.lever_syn, c.lever_axon, c.lever, c.lamp, c.status, c.bar)
    # ---------------- load / persistent state
    snbt = lambda d: "{" + ",".join(f'"{k}":' + (json.dumps(v) if not isinstance(v, dict) else snbt(v))
                                    for k, v in d.items()) + "}"
    reset_w = [f"scoreboard players set W{i}_{j} brain.w {W[i][j]}" for i in range(N) for j in range(J)]
    reset_w += [f"scoreboard players set b{j} brain.w 0" for j in range(J)]
    reset_v = [f"scoreboard players set V{j}_{k} brain.w {V[j][k]}" for j in range(J) for k in range(N)]
    reset_v += [f"scoreboard players set c{k} brain.w 0" for k in range(N)]
    w("net/reset_weights", reset_w + reset_v + ["scoreboard players set #trains brain.st 0"])
    w("load", ["scoreboard objectives add brain.s dummy", "scoreboard objectives add brain.n dummy",
               "scoreboard objectives add brain.w dummy", "scoreboard objectives add brain.t dummy",
               "scoreboard objectives add brain.st dummy", "scoreboard objectives add brain.ui dummy",
               f"data modify storage brain:lc m set value {snbt(lc)}",
               f"data modify storage brain:kw m set value {snbt(kw)}",
               "execute unless score #init brain.w matches 1 run function brain:net/reset_weights",
               "execute unless score #init brain.w matches 1 run data modify storage brain:mem list set value []",
               "execute unless score #init brain.w matches 1 run scoreboard players set #target brain.st -1",
               "execute unless score #init brain.w matches 1 run scoreboard players set #state brain.st 0",
               "scoreboard players set #init brain.w 1"])

