"""Zone A console blocks, zone B neuron bars, and text-display labels."""
import json
from .common import *


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

