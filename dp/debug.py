"""Debug printouts of activations and changed weights."""
import json, math
from .common import *


def emit(c):
    w, R, N, J, ri, cx, hx, hname, W, V, feeds, feed_y, col, lc, kw, lever_region, lever_syn, lever_axon, lever, lamp, status, bar = (c.w, c.R, c.N, c.J, c.ri, c.cx, c.hx, c.hname, c.W, c.V, c.feeds, c.feed_y, c.col, c.lc, c.kw, c.lever_region, c.lever_syn, c.lever_axon, c.lever, c.lamp, c.status, c.bar)
    # ---------------- debug
    pr = ['tellraw @p ["",{"text":"x ","color":"aqua"}' +
          "".join(f',{{"score":{{"name":"x{i}","objective":"brain.n"}}}},{{"text":" "}}' for i in range(N)) + "]",
          'tellraw @p ["",{"text":"h ","color":"aqua"}' +
          "".join(f',{{"score":{{"name":"h{j}","objective":"brain.n"}}}},{{"text":" "}}' for j in range(J)) + "]",
          'tellraw @p ["",{"text":"o ","color":"aqua"}' +
          "".join(f',{{"score":{{"name":"o{i}","objective":"brain.n"}}}},{{"text":" "}}' for i in range(N)) + "]"]
    w("dbg/print", pr)
    wt = ['tellraw @p {"text":"V weights that differ from baseline (hidden -> output):","color":"aqua"}']
    for j in range(J):
        for k in range(N):
            wt.append(f'execute unless score V{j}_{k} brain.w matches {V[j][k]} run tellraw @p '
                      f'["",{{"text":"{hname[j]} -> {NAMES[R[k]]}: "}},{{"score":{{"name":"V{j}_{k}","objective":"brain.w"}},"color":"yellow"}},'
                      f'{{"text":" (base {V[j][k]})","color":"gray"}}]')
    w("dbg/weights", wt)

