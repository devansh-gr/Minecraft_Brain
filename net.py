"""Redstone Cortex v3: datapack side.

Language front end, 8-16-8 integer neural network with leaky hidden units,
working memory, supervised plasticity on hidden->output synapses, lesions,
the tick-driven state machine and the console. The winner-take-all decision
and all transmission stay physical (see gen.py).
"""
import json, math

L0, L1 = -60, -59
DESK = -60
NAMES = {"prefrontal": "Prefrontal", "broca": "Broca", "motor": "Motor", "somato": "Touch",
         "parietal": "Parietal", "temporal": "Temporal", "occipital": "Visual", "cerebellum": "Cerebellum"}

# association units: pairs of regions that share a hidden neuron
PAIRS = [("prefrontal", "temporal"), ("broca", "temporal"), ("motor", "cerebellum"), ("motor", "somato"),
         ("somato", "parietal"), ("parietal", "occipital"), ("temporal", "occipital"), ("prefrontal", "parietal")]
W_P, W_A, V_P, V_A = 4, 2, 4, 1          # baseline weights
V_MIN, V_MAX = -8, 12                    # plasticity bounds
H_DIV, O_DIV = 4, 4                      # integer scaling of weighted sums
STEPS = 4                                # leaky integration steps

# console layout (y = -59 on a desk at y = -60)
CZ = -74                                 # main desk row
SIGN = (2, L1, CZ)
BTN = {"run": 4, "reset": 6, "train": 8, "reset_learning": 12, "demo": 14, "repair": 16, "memory": 20,
       "e1": 22, "e2": 24, "e3": 26, "e4": 28, "e5": 30}
LEV = {"learn": 10, "debug": 18}
REPLAY_X = [-14, -12, -10, -8, -6]
TZ = -78                                 # target-selection row
LZ = -70                                 # indicator lamp row
STAGES = ["stimulus", "input", "hidden", "output", "inhibition", "transmission", "decay"]
IND = {"ready": 18, "computing": 20, "complete": 22, "tie": 24, "nowinner": 26, "delivered": 28, "blocked": 30}

DEMO_QS = [["what is seven", "times eight?"], ["what colors are", "in a rainbow?"],
           ["how do i keep", "my balance on", "a skateboard"], ["how do you say", "hello in", "spanish"],
           ["should i quit", "my job?"]]
E3_Q = ["can you hear", "and see it?"]
E4_Q = ["what is seven", "times eight?"]
INJ = {"a": [2, 5, 11, 4, 7, 3, 1, 6], "b": [2, 11, 11, 4, 7, 3, 1, 6]}

# clock (game ticks after RUN)
T_IN, T_H, T_OUT, T_RAMP0, RAMP_DT, T_EXC, T_READ, T_DECAY, T_IDLE = 1, [12, 24, 36, 48], 60, 70, 6, 250, 380, 560, 580


def emit(w, REGIONS, col, feeds, lc, kw):
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

    # ---------------- barrel fills: comparator strength s from a 27-slot barrel
    for s in range(16):
        t = 0 if s == 0 else math.ceil(1728 * (s - 1) / 14) or 1
        assert s == (0 if t == 0 else 1 + int(14 * t / 1728)), s
        lines = []
        for slot in range(27):
            c = min(64, t); t -= c
            lines.append(f"$item replace block $(x) $(y) $(z) container.{slot} with "
                         + (f"minecraft:glowstone_dust {c}" if c else "minecraft:air"))
        w(f"fill/s{s}", lines)
    w("fill/by", ["$function brain:fill/s$(s) {x:$(x),y:$(y),z:$(z)}"])

    def bar(score, obj, x, y, z):
        return [f"execute store result storage brain:a s int 1 run scoreboard players get {score} {obj}",
                f"data modify storage brain:a x set value {x}", f"data modify storage brain:a y set value {y}",
                f"data modify storage brain:a z set value {z}", "function brain:fill/by with storage brain:a"]

    BARRELS = ([(cx[r], L1, -28) for r in R] + [(x, L1, -48) for x in hx] +
               [(cx[r], L1, -3) for r in R] + [(cx[r], L0, 2) for r in R] + [(cx[r], L1, 1) for r in R])
    w("clear_barrels", [f"function brain:fill/s0 {{x:{x},y:{y},z:{z}}}" for x, y, z in BARRELS])

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

    # ---------------- language front end -> region keyword hits
    parse = ["data modify storage brain:p lines set from block %d %d %d front_text.messages" % SIGN,
             "data modify storage brain:p l set value {}"]
    parse += [f"data modify storage brain:p l.{c} set string storage brain:p lines[{n}]" for n, c in enumerate("abcd")]
    parse += ["function brain:p/join with storage brain:p l",
              'data modify storage brain:p w set value ""', 'data modify storage brain:p qn set value ""',
              "scoreboard players set #i brain.t 0",
              "execute store result score #len brain.t run data get storage brain:p q"]
    parse += [f"scoreboard players set {r} brain.s 0" for r in R]
    parse += ["function brain:p/loop"]
    w("p/parse", parse)
    w("p/join", ['$data modify storage brain:p q set value "$(a) $(b) $(c) $(d) "'])
    w("p/loop", ["execute if score #i brain.t >= #len brain.t run return 0",
                 "execute store result storage brain:p i int 1 run scoreboard players get #i brain.t",
                 "scoreboard players add #i brain.t 1",
                 "execute store result storage brain:p j int 1 run scoreboard players get #i brain.t",
                 "function brain:p/char with storage brain:p",
                 'data modify storage brain:p n set value " "',
                 "function brain:p/norm with storage brain:p",
                 'execute if data storage brain:p {n:" "} unless data storage brain:p {w:""} run function brain:p/word',
                 'execute if data storage brain:p {n:" "} run data modify storage brain:p w set value ""',
                 'execute unless data storage brain:p {n:" "} run function brain:p/app with storage brain:p',
                 "function brain:p/loop"])
    w("p/char", ["$data modify storage brain:p c set string storage brain:p q $(i) $(j)"])
    w("p/norm", ['$data modify storage brain:p n set from storage brain:lc m."$(c)"'])
    w("p/app", ['$data modify storage brain:p w set value "$(w)$(n)"'])
    w("p/qn", ['$data modify storage brain:p qn set value "$(qn)$(w) "'])
    w("p/word", ["execute store result score #ql brain.t run data get storage brain:p qn",
                 "execute if score #ql brain.t matches ..40 run function brain:p/qn with storage brain:p",
                 "data modify storage brain:p s set from storage brain:p w",
                 "execute if function brain:p/try run return 1",
                 "execute store result score #wl brain.t run data get storage brain:p w",
                 "execute if score #wl brain.t matches ..3 run return 0",
                 "data modify storage brain:p e1 set string storage brain:p w -1",
                 "data modify storage brain:p e2 set string storage brain:p w -2",
                 "data modify storage brain:p e3 set string storage brain:p w -3"] +
      [f'execute if data storage brain:p {{e{len(suf)}:"{suf}"}} if function brain:p/st_{suf} run return 1'
       for suf in ["ing", "ies", "ed", "es", "ly", "er", "s"]])
    w("p/try", ["return run function brain:p/try_m with storage brain:p"])
    w("p/try_m", ['$execute if data storage brain:kw m."$(s)" run return run function brain:p/hit with storage brain:kw m."$(s)"',
                  "return fail"])
    w("p/hit", ["$scoreboard players add $(r) brain.s 1", "return 1"])
    cut = lambda n: f"data modify storage brain:p s set string storage brain:p w 0 -{n}"
    tr = "execute if function brain:p/try run return 1"
    w("p/st_ing", [cut(3), tr, "function brain:p/add_e with storage brain:p", tr, "return fail"])
    w("p/st_ies", [cut(3), "function brain:p/add_y with storage brain:p", tr, "return fail"])
    w("p/st_ed", [cut(2), tr, cut(1), tr, "return fail"])
    for suf, n in [("es", 2), ("ly", 2), ("er", 2), ("s", 1)]:
        w(f"p/st_{suf}", [cut(n), tr, "return fail"])
    w("p/add_e", ['$data modify storage brain:p s set value "$(s)e"'])
    w("p/add_y", ['$data modify storage brain:p s set value "$(s)y"'])

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

    # ---------------- repair, demo, experiments
    rep = []
    for i in range(N):
        rep += [f"setblock {cx[R[i]]} {L1} -21 lever[face=floor,facing=north,powered=false]",
                f"setblock {cx[R[i]]} {L1} -46 lever[face=floor,facing=north,powered=false]",
                f"setblock {cx[R[i]]+2} {L1} 12 lever[face=floor,facing=north,powered=false]"]
    w("ui/repair", rep + ['data modify entity @e[type=text_display,tag=train,limit=1] text set value "ALL LESIONS REPAIRED"'])
    def setq(q):
        lines = (q + ["", "", "", ""])[:4]
        return "data merge block %d %d %d {front_text:{messages:%s}}" % (*SIGN, json.dumps(lines))
    demo = ["execute if score #state brain.st matches 1 run return 0", "scoreboard players add #demo brain.st 1",
            f"execute if score #demo brain.st matches {len(DEMO_QS)}.. run scoreboard players set #demo brain.st 0"]
    demo += [f"execute if score #demo brain.st matches {n} run {setq(q)}" for n, q in enumerate(DEMO_QS)]
    w("ui/demo", demo + ["function brain:ui/run"])
    w("ui/e1", ["function brain:ui/demo"])
    w("ui/e2", ["execute if score #state brain.st matches 1 run return 0", "scoreboard players add #e2 brain.st 1",
                "execute if score #e2 brain.st matches 2.. run scoreboard players set #e2 brain.st 0",
                "execute if score #e2 brain.st matches 1 run function brain:dbg/inject_a",
                "execute if score #e2 brain.st matches 0 run function brain:dbg/inject_b"])
    occ = R.index("occipital")
    w("ui/e3", [setq(E3_Q), f"function brain:ui/target{occ}",
                f"setblock {LEV['learn']} {L1} {CZ} lever[face=floor,facing=north,powered=true]",
                'data modify entity @e[type=text_display,tag=train,limit=1] text set value '
                '"EXP 3 READY: RUN, then TRAIN\\n(target Visual), then RUN again"'])
    w("ui/e4", [setq(E4_Q), "function brain:ui/repair",
                'data modify entity @e[type=text_display,tag=train,limit=1] text set value '
                '"EXP 4: RUN, then pull the\\nParietal AXON lever, RUN again,\\nrepair it, RUN again"'])
    par = R.index("parietal")
    w("ui/e5", [setq(E4_Q), "function brain:ui/repair",
                f"setblock {cx['parietal']} {L1} -46 lever[face=floor,facing=north,powered=true]",
                f"function brain:ui/target{par}",
                f"setblock {LEV['learn']} {L1} {CZ} lever[face=floor,facing=north,powered=true]",
                'data modify entity @e[type=text_display,tag=train,limit=1] text set value '
                '"EXP 5: Parietal direct synapse cut.\\nRUN, TRAIN (Parietal) x3, RUN"'])

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
    return dict(R=R, cx=cx, hx=hx, hname=hname, W=W, V=V, J=J)


def console(cx, R, colors):
    REGION_COLOR.update(colors)
    """Blocks + labels for zone A and the neural processor bars (zone B)."""
    C = [f"fill -18 {DESK} -82 34 {L1+3} -26 air"]
    N = len(R)
    J = N + len(PAIRS)
    hx = [cx[r] for r in R] + [4 * m + 2 for m in range(len(PAIRS))]
    # zone B: input neuron bars (z -28..-44) and hidden neuron bars (z -48..-64)
    for x in [cx[r] for r in R]:
        C += [f"setblock {x} {L1} -28 barrel[facing=up]", f"setblock {x} {L0} -29 polished_blackstone",
              f"setblock {x} {L1} -29 comparator[facing=south]",
              f"fill {x} {L0} -44 {x} {L0} -30 redstone_lamp", f"fill {x} {L1} -44 {x} {L1} -30 redstone_wire",
              f"setblock {x} {L0} -46 polished_blackstone", f"setblock {x} {L1} -46 lever[face=floor,facing=north]",
              f"setblock {x} {L1} -47 redstone_lamp"]
    for x in hx:
        C += [f"setblock {x} {L1} -48 barrel[facing=up]", f"setblock {x} {L0} -49 polished_blackstone",
              f"setblock {x} {L1} -49 comparator[facing=south]",
              f"fill {x} {L0} -64 {x} {L0} -50 redstone_lamp", f"fill {x} {L1} -64 {x} {L1} -50 redstone_wire"]
    # desks
    C += [f"fill -16 {DESK} {CZ} 32 {DESK} {CZ} polished_deepslate",
          f"fill 0 {DESK} {TZ} 30 {DESK} {TZ - 1} polished_deepslate",
          f"fill 0 {DESK} {LZ} 32 {DESK} {LZ} polished_blackstone"]
    C += [f"setblock {SIGN[0]} {SIGN[1]} {SIGN[2]} oak_sign[rotation=8]",
          'data merge block %d %d %d {front_text:{messages:["what is seven","times eight?","",""]}}' % SIGN]
    for n, x in BTN.items():
        C.append(f"setblock {x} {L1} {CZ} polished_blackstone_button[face=floor,facing=north]")
    for x in REPLAY_X:
        C.append(f"setblock {x} {L1} {CZ} polished_blackstone_button[face=floor,facing=north]")
    for n, x in LEV.items():
        C += [f"setblock {x} {L1} {CZ} lever[face=floor,facing=north]", f"setblock {x} {L1} {CZ+1} redstone_lamp"]
    for t, r in enumerate(R):
        x = cx[r]
        C += [f"setblock {x} {DESK} {TZ} {REGION_COLOR[r]}_concrete",
              f"setblock {x} {L1} {TZ} stone_button[face=floor,facing=north]",
              f"setblock {x} {L1} {TZ-1} redstone_lamp"]
    for n in range(len(STAGES)):
        C.append(f"setblock {2+2*n} {L1} {LZ} redstone_lamp")
    for k, x in IND.items():
        C.append(f"setblock {x} {L1} {LZ} redstone_lamp")
    return C


REGION_COLOR = {}


def labels(cx, R):
    """text_display labels (summon lines)."""
    out = ["kill @e[type=text_display,tag=ui]"]
    def td(x, y, z, text, scale=0.6, tags=(), color="white", bb="vertical", width=200):
        tg = ",".join(json.dumps(t) for t in ("ui",) + tuple(tags))
        out.append(f'summon text_display {x} {y} {z} {{billboard:"{bb}",line_width:{width},background:1342177280,'
                   f'text:{{text:{json.dumps(text)},color:"{color}"}},Tags:[{tg}],'
                   f'transformation:{{left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],'
                   f'translation:[0f,0f,0f],scale:[{scale}f,{scale}f,{scale}f]}}}}')
    lab = {"run": "RUN", "reset": "RESET", "train": "TRAIN", "reset_learning": "RESET\nLEARNING", "demo": "DEMO",
           "repair": "REPAIR\nALL", "memory": "MEMORY", "e1": "EXP 1\nclassify", "e2": "EXP 2\ninhibition",
           "e3": "EXP 3\nlearning", "e4": "EXP 4\naxon lesion", "e5": "EXP 5\nsynapse lesion"}
    for n, x in BTN.items():
        td(x + 0.5, L1 + 1.0, CZ + 0.5, lab[n], 0.45)
    td(10.5, L1 + 1.0, CZ + 0.5, "LEARN\non/off", 0.45)
    td(18.5, L1 + 1.0, CZ + 0.5, "DEBUG\non/off", 0.45)
    td(SIGN[0] + 0.5, L1 + 1.9, SIGN[2] + 0.5, "QUESTION", 0.5)
    for s, x in enumerate(REPLAY_X):
        td(x + 0.5, L1 + 1.0, CZ + 0.5, f"REPLAY\n{s+1}", 0.45)
    for s in range(5):
        td(-10, L1 + 5.6 - 0.55 * s, CZ + 0.5, f"{s+1}. (empty)", 0.5, (f"mem{s}",), "gray", width=400)
    td(-10, L1 + 6.4, CZ + 0.5, "WORKING MEMORY", 0.7, (), "aqua")
    for t, r in enumerate(R):
        td(cx[r] + 0.5, L1 + 1.0, TZ + 0.5, NAMES[r], 0.4)
    td(16, L1 + 2.0, TZ + 0.5, "TRAINING TARGET", 0.6, (), "aqua")
    td(36, L1 + 3.5, CZ + 0.5, "pick a target, then TRAIN", 0.6, ("train",), "yellow", width=300)
    for n, s in enumerate(STAGES):
        td(2 + 2 * n + 0.5, L1 + 1.0, LZ + 0.5, s, 0.35)
    for k, x in IND.items():
        td(x + 0.5, L1 + 1.0, LZ + 0.5, k.upper(), 0.35)
    td(16, L1 + 8, LZ, "READY · write a question, press RUN", 1.6, ("status",), "white", width=600)
    td(16, L1 + 5, -46, "B · NEURAL PROCESSOR\ninput layer (8)  ·  hidden layer (16, leaky)", 1.2, (), "aqua", width=500)
    td(16, L1 + 4, -12, "C · INHIBITORY COMPUTER\noutput neurons compete (comparator winner-take-all)", 1.2, (), "aqua", width=500)
    td(16, L1 + 4, 14, "D · AXONS\nlever on each line = axon lesion", 1.2, (), "aqua", width=500)
    td(16, L1 + 4, CZ - 4, "A · INPUT TERMINAL", 1.4, (), "aqua", width=500)
    for i, r in enumerate(R):
        td(cx[r] + 0.5, L1 + 1.2, -26.5, NAMES[r], 0.4)
    td(50, L1 + 5, CZ + 0.5, EXPERIMENTS, 0.7, (), "white", width=520)
    td(-26, L1 + 5, -60, HOWTO, 0.7, (), "white", width=420)
    return out


EXPERIMENTS = """EXPERIMENTS (buttons EXP 1-5 on the console)
1  CLASSIFY: press EXP 1 again and again. Each preset question lands in a different region.
2  INHIBITION: EXP 2 injects [2,5,11,4,7,3,1,6] straight into the comparator circuit: only channel 3 survives. Press again: [2,11,11,4,7,3,1,6] gives a TIE (channels 2 and 3).
3  LEARNING: EXP 3, RUN (Temporal/Visual tie), TRAIN, RUN again: Visual now wins. RESET LEARNING undoes it.
4  AXON LESION: EXP 4, RUN (Parietal lights). Pull the Parietal lever in zone D, RUN: computed but BLOCKED. Push it back, RUN: delivered again.
5  SYNAPSE LESION: EXP 5 cuts Parietal's direct synapse. RUN (weak), TRAIN x3, RUN: output recovers through association neurons."""

HOWTO = """HOW TO READ THIS MACHINE
A  write a question on the sign, press RUN
B  lamp bars = neuron activations (bar length 0-15). Top rows: 8 input neurons. Bottom rows: 16 hidden neurons (8 primary, 8 association)
C  8 output bars compete. Inhibition (gray comparator line) rises; weaker bars go dark; the survivor fires
D  the winning spike runs down its lamp axon. Levers: region lesion (-21), synapse lesion (-46), axon lesion (on the axon)
E  the spike enters the cortex and spreads ring by ring
Datapack: text reading, network arithmetic, memory, learning. Redstone: winner-take-all, transmission, cortex lighting."""
