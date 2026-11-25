"""Datapack generator, one module per subsystem. emit() runs them in a fixed order."""
import json, math
from types import SimpleNamespace
from .common import *
from . import barrels, persist, parser, network, pipeline, inject, memory, plasticity, experiments, debug, control, hwneuron, racetags
from .console import console, labels


def emit(w, REGIONS, col, feeds, lc, kw, feed_y):
    R = [reg[0] for reg in REGIONS]
    N = len(R)
    J = N + len(PAIRS)
    ri = {r: i for i, r in enumerate(R)}
    cx = {r: 4 * col[i] for i, r in enumerate(R)}            # board x of each region
    hx = [cx[r] for r in R] + [4 * m + 2 for m in range(len(PAIRS))]
    hname = [f"P:{NAMES[r]}" for r in R] + [f"A:{NAMES[a][:4]}+{NAMES[b][:4]}" for a, b in PAIRS]

    # baseline weights
    W = [[0] * J for _ in range(N)]
    V = [[0] * N for _ in range(J)]
    for i in range(N):
        W[i][i] = W_P
        V[i][i] = V_P
    for m, (a, b) in enumerate(PAIRS):
        W[ri[a]][N + m] = W_A; W[ri[b]][N + m] = W_A
        V[N + m][ri[a]] = V_A; V[N + m][ri[b]] = V_A

    lever_region = lambda i: f"{cx[R[i]]} {L1} -21 lever[powered=true]"
    lever_syn = lambda i: f"{cx[R[i]]} {L1} -46 lever[powered=true]"
    lever_axon = lambda i: f"{cx[R[i]]+2} {L1} 12 lever[powered=true]"
    lever = lambda name: f"{LEV[name]} {L1} {CZ} lever[powered=true]"

    def lamp(x, z, on):
        return f"setblock {x} {DESK} {z} {'redstone_block' if on else 'polished_blackstone'}"

    def status(text):
        return f'data modify entity @e[type=text_display,tag=status,limit=1] text set value {json.dumps(text)}'

    def bar(score, obj, x, y, z):
        return [f"execute store result storage brain:a s int 1 run scoreboard players get {score} {obj}",
                f"data modify storage brain:a x set value {x}", f"data modify storage brain:a y set value {y}",
                f"data modify storage brain:a z set value {z}", "function brain:fill/by with storage brain:a"]

    c = SimpleNamespace(w=w, R=R, N=N, J=J, ri=ri, cx=cx, hx=hx, hname=hname, W=W, V=V, feeds=feeds, feed_y=feed_y, col=col, lc=lc, kw=kw, lever_region=lever_region, lever_syn=lever_syn, lever_axon=lever_axon, lever=lever, lamp=lamp, status=status, bar=bar)
    barrels.emit(c)
    persist.emit(c)
    parser.emit(c)
    network.emit(c)
    pipeline.emit(c)
    inject.emit(c)
    memory.emit(c)
    plasticity.emit(c)
    experiments.emit(c)
    debug.emit(c)
    hwneuron.emit(c)
    racetags.emit(c)
    control.emit(c)
    return dict(R=R, cx=cx, hx=hx, hname=hname, W=W, V=V, J=J)
