"""Staged clock: input, hidden, output, inhibition ramp, excitation, physical readout, decay."""
import json, math
from .common import *


def emit(c):
    w, R, N, J, ri, cx, hx, hname, W, V, feeds, col, lc, kw, lever_region, lever_syn, lever_axon, lever, lamp, status, bar = (c.w, c.R, c.N, c.J, c.ri, c.cx, c.hx, c.hname, c.W, c.V, c.feeds, c.col, c.lc, c.kw, c.lever_region, c.lever_syn, c.lever_axon, c.lever, c.lamp, c.status, c.bar)
    # ---------------- stages (driven by brain:clock)
    def stage_lamps(active):
        return [lamp(2 + 2 * n, LZ, n == active) for n in range(len(STAGES))]

    w("stage/input", stage_lamps(1) + sum([bar(f"x{i}", "brain.n", cx[r], L1, -28) for i, r in enumerate(R)], [])
      + [status("COMPUTING · input layer")])
    for s, t in enumerate(T_H):
        w(f"stage/hidden{s}", stage_lamps(2) + ["function brain:net/hidden_step"]
          + sum([bar(f"h{j}", "brain.n", hx[j], L1, -48) for j in range(J)], [])
          + [status(f"COMPUTING · hidden layer {s+1}/{STEPS}")])
    w("stage/output", stage_lamps(3) + ["execute unless score #inj brain.st matches 1 run function brain:net/output"]
      + sum([bar(f"o{i}", "brain.n", cx[r], L1, -3) for i, r in enumerate(R)], [])
      + ["scoreboard players set #k brain.t 0", status("COMPUTING · output neurons compete")])
    w("stage/ramp", stage_lamps(4) + ["scoreboard players add #k brain.t 1",
                                      "execute store result storage brain:a k int 1 run scoreboard players get #k brain.t",
                                      "function brain:stage/ramp_m with storage brain:a",
                                      status("COMPUTING · lateral inhibition rising")])
    w("stage/ramp_m", [f"$execute if score o{i} brain.n matches $(k).. run function brain:fill/s$(k) "
                       f"{{x:{cx[r]},y:{L0},z:2}}" for i, r in enumerate(R)])
    w("stage/excite", stage_lamps(5) + sum([bar(f"o{i}", "brain.n", cx[r], L1, 1) for i, r in enumerate(R)], [])
      + [status("COMPUTING · winner fires down its axon")])

    # readout: what the physical circuit decided and whether it arrived
    rd = ["scoreboard players set #nwin brain.t 0", "scoreboard players set #ndel brain.t 0",
          'data modify storage brain:a win set value ""', 'data modify storage brain:a lost set value ""']
    for i, r in enumerate(R):
        fx, fz = feeds[i]
        rd += [f"execute store success score f{i} brain.n if block {cx[r]} {L1} 3 repeater[powered=true]",
               f"execute store success score d{i} brain.n unless block {fx} -58 {fz} redstone_wire[power=0]",
               f"scoreboard players operation #nwin brain.t += f{i} brain.n",
               f"execute if score f{i} brain.n matches 1 if score d{i} brain.n matches 1 run scoreboard players add #ndel brain.t 1",
               f'execute if score f{i} brain.n matches 1 run function brain:ui/addwin {{v:"{NAMES[r]} "}}',
               f'execute if score f{i} brain.n matches 1 if score d{i} brain.n matches 0 run function brain:ui/addlost {{v:"{NAMES[r]} "}}']
    rd += ["scoreboard players set #state brain.st 2", "scoreboard players set #has brain.st 1",
           lamp(IND["computing"], LZ, False), lamp(IND["complete"], LZ, True),
           f"execute if score #nwin brain.t matches 2.. run {lamp(IND['tie'], LZ, True)}",
           f"execute if score #nwin brain.t matches 0 run {lamp(IND['nowinner'], LZ, True)}",
           f"execute if score #ndel brain.t matches 1.. run {lamp(IND['delivered'], LZ, True)}",
           f"execute unless data storage brain:a {{lost:\"\"}} run {lamp(IND['blocked'], LZ, True)}",
           "function brain:ui/status_done with storage brain:a",
           "function brain:mem/record",
           "execute if block %s run function brain:dbg/print" % lever("debug")]
    w("stage/readout", stage_lamps(5) + rd)
    for k in ("win", "lost"):
        w(f"ui/add{k}", ['$data modify storage brain:a v set value "$(v)"', f"function brain:ui/cat_{k} with storage brain:a"])
        w(f"ui/cat_{k}", [f'$data modify storage brain:a {k} set value "$({k})$(v)"'])
    w("stage/decay", stage_lamps(6) + ["function brain:clear_barrels", status("decaying...")])
    w("stage/idle", stage_lamps(-1) + ["scoreboard players set #state brain.st 0", lamp(IND["complete"], LZ, False),
                                       lamp(IND["ready"], LZ, True), status("READY · write a question, press RUN")])
    w("ui/status_done", [
        'execute if score #nwin brain.t matches 0 run ' + status("COMPLETE · NO WINNER (no recognised features)"),
        '$execute if score #nwin brain.t matches 1 run data modify entity @e[type=text_display,tag=status,limit=1] text set value "COMPLETE · $(win)"',
        '$execute if score #nwin brain.t matches 2.. run data modify entity @e[type=text_display,tag=status,limit=1] text set value "COMPLETE · TIE: $(win)"',
        '$execute unless data storage brain:a {lost:""} run data modify entity @e[type=text_display,tag=status,limit=1] text set value "COMPUTED $(win)· AXON CUT, signal blocked"'])

    clock = ["scoreboard players add #t brain.st 1",
             f"execute if score #t brain.st matches {T_IN} run function brain:stage/input"]
    clock += [f"execute if score #t brain.st matches {t} run function brain:stage/hidden{s}" for s, t in enumerate(T_H)]
    clock += [f"execute if score #t brain.st matches {T_OUT} run function brain:stage/output"]
    clock += [f"execute if score #t brain.st matches {T_RAMP0 + RAMP_DT * k} run function brain:stage/ramp" for k in range(1, 16)]
    clock += [f"execute if score #t brain.st matches {T_EXC} run function brain:stage/excite",
              f"execute if score #t brain.st matches {T_READ} run function brain:stage/readout",
              f"execute if score #t brain.st matches {T_DECAY} run function brain:stage/decay",
              f"execute if score #t brain.st matches {T_IDLE} run function brain:stage/idle"]
    w("clock", clock)

    # start a computation: from the sign (run), from memory (replay) or from a vector (inject)
    begin = ["function brain:clear_barrels", "scoreboard players set #state brain.st 1",
             "scoreboard players set #t brain.st 0", "scoreboard players set #inj brain.st 0"]
    begin += [lamp(IND[k], LZ, k == "computing") for k in IND]
    begin += [f"scoreboard players set u{j} brain.n 0" for j in range(J)]
    begin += [f"scoreboard players set h{j} brain.n 0" for j in range(J)]
    begin += stage_lamps(0) + [status("COMPUTING · stimulus received"),
                               "playsound minecraft:block.beacon.activate master @a ~ ~ ~ 0.6 1.6"]
    w("begin", begin)
    w("ui/run", ["execute if score #state brain.st matches 1 run return 0", "function brain:p/parse",
                 "function brain:net/encode", "data modify storage brain:a q set from storage brain:p qn",
                 "scoreboard players set #replay brain.st -1", "function brain:begin"])
    w("ui/reset", ["scoreboard players set #state brain.st 0", "function brain:clear_barrels",
                   "function brain:stage/idle"] + [lamp(IND[k], LZ, k == "ready") for k in IND])

