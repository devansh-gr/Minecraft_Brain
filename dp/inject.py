"""Debug injection of a score vector straight into the physical circuit."""
import json, math
from .common import *


def emit(c):
    w, R, N, J, ri, cx, hx, hname, W, V, feeds, feed_y, col, lc, kw, lever_region, lever_syn, lever_axon, lever, lamp, status, bar = (c.w, c.R, c.N, c.J, c.ri, c.cx, c.hx, c.hname, c.W, c.V, c.feeds, c.feed_y, c.col, c.lc, c.kw, c.lever_region, c.lever_syn, c.lever_axon, c.lever, c.lamp, c.status, c.bar)
    # ---------------- inject (debug + experiment 2): physical WTA test from a known score vector
    inj = ["execute if score #state brain.st matches 1 run return 0", "function brain:begin",
           "scoreboard players set #inj brain.st 1", 'data modify storage brain:a q set value "(injected vector)"',
           f"scoreboard players set #t brain.st {T_OUT - 1}"]
    inj += [f"scoreboard players set x{i} brain.n 0" for i in range(N)]
    for i, r in enumerate(R):
        inj.append(f"$scoreboard players set o{i} brain.n $(c{col[i]})")      # vector is in physical channel order
    w("dbg/inject", inj)
    for key, vec in INJ.items():
        args = ",".join(f"c{c}:{v}" for c, v in enumerate(vec))
        w(f"dbg/inject_{key}", [f"function brain:dbg/inject {{{args}}}"])

