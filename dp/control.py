"""Tick function: console button polling and the clock."""
import json, math
from .common import *


def emit(c):
    w, R, N, J, ri, cx, hx, hname, W, V, feeds, col, lc, kw, lever_region, lever_syn, lever_axon, lever, lamp, status, bar = (c.w, c.R, c.N, c.J, c.ri, c.cx, c.hx, c.hname, c.W, c.V, c.feeds, c.col, c.lc, c.kw, c.lever_region, c.lever_syn, c.lever_axon, c.lever, c.lamp, c.status, c.bar)
    # ---------------- tick: console polling (rising edge) + clock
    tick = ["execute if score #state brain.st matches 1..2 run function brain:clock"]
    controls = [(f"{x} {L1} {CZ}", f"ui/{n}") for n, x in BTN.items()]
    controls += [(f"{x} {L1} {CZ}", f"ui/replay{s}") for s, x in enumerate(REPLAY_X)]
    controls += [(f"{cx[R[t]]} {L1} {TZ}", f"ui/target{t}") for t in range(N)]
    for n, (pos, fn) in enumerate(controls):
        tick += [f"execute store success score #b{n} brain.ui if block {pos} #minecraft:buttons[powered=true]",
                 f"execute if score #b{n} brain.ui matches 1 unless score #p{n} brain.ui matches 1 run function brain:{fn}",
                 f"scoreboard players operation #p{n} brain.ui = #b{n} brain.ui"]
    tick += ["execute if block %s run function brain:dbg/weights_if_new" % lever("debug")]
    w("tick", tick)
    w("dbg/weights_if_new", ["execute unless score #lastdbg brain.st = #trains brain.st run function brain:dbg/weights",
                             "scoreboard players operation #lastdbg brain.st = #trains brain.st"])
