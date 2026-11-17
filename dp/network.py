"""8-16-8 integer network: encoding, leaky hidden step, output layer, synaptic lesions."""
import json, math
from .common import *


def emit(c):
    w, R, N, J, ri, cx, hx, hname, W, V, feeds, col, lc, kw, lever_region, lever_syn, lever_axon, lever, lamp, status, bar = (c.w, c.R, c.N, c.J, c.ri, c.cx, c.hx, c.hname, c.W, c.V, c.feeds, c.col, c.lc, c.kw, c.lever_region, c.lever_syn, c.lever_axon, c.lever, c.lamp, c.status, c.bar)
    # ---------------- network
    enc = []
    for i, r in enumerate(R):
        enc += [f"scoreboard players operation x{i} brain.n = {r} brain.s",
                f"scoreboard players operation x{i} brain.n *= #3 brain.t",
                f"execute if score x{i} brain.n matches 16.. run scoreboard players set x{i} brain.n 15"]
    w("net/encode", ["scoreboard players set #3 brain.t 3"] + enc)

    step = ["scoreboard players set #I brain.t 0"]
    step += [f"scoreboard players operation #I brain.t += u{j} brain.n" for j in range(J)]
    step += ["scoreboard players set #16 brain.t 16", "scoreboard players operation #I brain.t /= #16 brain.t",
             f"scoreboard players set #hd brain.t {H_DIV}", "scoreboard players set #2 brain.t 2"]
    for j in range(J):
        step.append(f"scoreboard players operation #d brain.t = b{j} brain.w")
        for i in range(N):
            if W[i][j]:
                step += [f"scoreboard players operation #m brain.t = W{i}_{j} brain.w",
                         f"scoreboard players operation #m brain.t *= x{i} brain.n",
                         "scoreboard players operation #d brain.t += #m brain.t"]
        step += ["scoreboard players operation #d brain.t /= #hd brain.t",
                 "scoreboard players operation #d brain.t -= #I brain.t",
                 "execute if score #d brain.t matches ..-1 run scoreboard players set #d brain.t 0",
                 "execute if score #d brain.t matches 16.. run scoreboard players set #d brain.t 15",
                 # u += ceil((d - u) / 2)
                 "scoreboard players operation #d brain.t -= u%d brain.n" % j,
                 "scoreboard players add #d brain.t 1",
                 "scoreboard players operation #d brain.t /= #2 brain.t",
                 f"scoreboard players operation u{j} brain.n += #d brain.t"]
    for i in range(N):
        step.append(f"execute if block {lever_region(i)} run scoreboard players set u{i} brain.n 0")
    step += [f"scoreboard players operation h{j} brain.n = u{j} brain.n" for j in range(J)]
    w("net/hidden_step", step)

    out = [f"scoreboard players set #od brain.t {O_DIV}"]
    for k in range(N):
        out.append(f"scoreboard players operation o{k} brain.n = c{k} brain.w")
        for j in range(J):
            out += [f"scoreboard players operation #m brain.t = V{j}_{k} brain.w",
                    f"scoreboard players operation #m brain.t *= h{j} brain.n",
                    f"scoreboard players operation o{k} brain.n += #m brain.t"]
        # synaptic lesion: the direct P_k -> o_k connection stops contributing
        out.append(f"execute if block {lever_syn(k)} run function brain:net/syn_cut{k}")
        out += [f"scoreboard players operation o{k} brain.n /= #od brain.t",
                f"execute if score o{k} brain.n matches ..-1 run scoreboard players set o{k} brain.n 0",
                f"execute if score o{k} brain.n matches 16.. run scoreboard players set o{k} brain.n 15",
                f"execute if block {lever_region(k)} run scoreboard players set o{k} brain.n 0"]
        w(f"net/syn_cut{k}", [f"scoreboard players operation #m brain.t = V{k}_{k} brain.w",
                              f"scoreboard players operation #m brain.t *= h{k} brain.n",
                              f"scoreboard players operation o{k} brain.n -= #m brain.t"])
    w("net/output", out)

