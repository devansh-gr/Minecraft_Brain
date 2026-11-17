"""Generate the Redstone Cortex datapack for Minecraft 26.3."""
import json, math, shutil
from pathlib import Path
import numpy as np
import nibabel as nib
from scipy import ndimage
from nilearn import datasets, image

ROOT = Path(__file__).parent
DP = ROOT / "build" / "datapack" / "redstone_cortex"
FN = DP / "data" / "brain" / "function"

L0, L1 = -60, -59            # board levels: max layer, decision layer
SIGN = (14, -59, -8)         # question sign
ANS = (12, -59, -8)          # answer sign
BTN_CMD = (15, -59, -6)

# id, title, what it does, glass color, Harvard-Oxford cortical labels, keywords
REGIONS = [
    ("prefrontal", "PREFRONTAL CORTEX", "planning, decisions, emotion control", "light_blue",
     [1, 3, 4, 25, 27, 28, 29, 33],
     "should plan decide decision choose choice why think idea future goal best better worse opinion believe "
     "happy sad angry love hate fear scared afraid worried mood emotion emotions feeling feelings lonely excited "
     "anxious nervous stress focus attention solve puzzle strategy smart rule moral good bad"),
    ("broca", "BROCA'S AREA", "producing speech and grammar", "purple", [5, 6, 41],
     "say said speak spoken talk talking tell pronounce pronunciation sentence grammar translate spell spelling "
     "write writing rhyme language languages"),
    ("motor", "MOTOR CORTEX", "planning and sending movement commands", "red", [7, 26],
     "move moving run running jump walk throw kick dance swim lift push pull climb catch hit punch wave grab "
     "draw sport sports soccer football basketball exercise"),
    ("somato", "SOMATOSENSORY CORTEX", "touch, temperature, pain", "orange", [17, 42],
     "feel feels touch hot cold warm pain hurt hurts itch itchy soft rough smooth texture tickle burn sharp "
     "pressure temperature sore skin numb"),
    ("parietal", "PARIETAL LOBE", "numbers, math, space and direction", "yellow", [18, 19, 20, 21, 30, 31, 43],
     "plus minus times divided add subtract multiply divide math number numbers count many equals sum total "
     "half double percent fraction where direction left map distance far near size bigger smaller angle "
     "calculate geometry one two three four five six seven eight nine ten hundred thousand # ## ### ####"),
    ("temporal", "TEMPORAL LOBE", "hearing, word meaning, memory, faces", "lime",
     [2, 8, 9, 10, 11, 12, 13, 14, 15, 16, 34, 35, 37, 38, 44, 45, 46],
     "hear heard sound sounds music song sing listen loud quiet noise voice word words mean meaning means define "
     "definition name remember memory forget yesterday history when story understand who face faces recognize "
     "person friend"),
    ("occipital", "OCCIPITAL LOBE", "vision: color, shape, motion, reading", "blue", [22, 23, 24, 32, 36, 39, 40, 47, 48],
     "see seen look looks watch color colour red blue green yellow purple orange black white bright dark light "
     "picture image shape read reading sky eye eyes vision glow shiny pattern rainbow"),
    ("cerebellum", "CEREBELLUM", "balance, coordination, timing", "pink", [],
     "balance coordination ride bike bicycle skate skateboard surf ski juggle tightrope timing rhythm fall dizzy "
     "steady practice skill piano guitar"),
]
N = len(REGIONS)
BRAINSTEM = N


def build_volume():
    cort = datasets.fetch_atlas_harvard_oxford("cort-maxprob-thr0-2mm", data_dir=str(ROOT / "atlas"))
    sub = datasets.fetch_atlas_harvard_oxford("sub-maxprob-thr0-2mm", data_dir=str(ROOT / "atlas"))
    cimg = cort.maps if hasattr(cort.maps, "get_fdata") else nib.load(cort.maps)
    simg = sub.maps if hasattr(sub.maps, "get_fdata") else nib.load(sub.maps)
    c = np.asarray(cimg.get_fdata(), int)
    s = np.asarray(simg.get_fdata(), int)
    mask_img = image.resample_to_img(datasets.load_mni152_brain_mask(), cimg, interpolation="nearest")
    mask = np.asarray(mask_img.get_fdata()) > 0.5
    mask |= (c > 0) | (s > 0)

    lab = np.full(c.shape, -1, int)                      # -1 = interior / unlabeled
    for r, reg in enumerate(REGIONS):
        for l in reg[4]:
            lab[c == l] = r
    sub_names = sub.labels
    stem = sub_names.index("Brain-Stem")
    lab[s == stem] = BRAINSTEM
    # cerebellum: in brain mask, no cerebral label, low and posterior
    cereb = mask & (c == 0) & (s == 0)
    zs = np.arange(c.shape[2])[None, None, :]
    cereb &= zs < 34                                     # below ~ -4 mm MNI
    lab[cereb] = REGIONS.index(next(x for x in REGIONS if x[0] == "cerebellum"))

    # downsample 2mm -> 4mm
    shp = tuple(d // 2 for d in c.shape)
    m4 = np.zeros(shp, bool)
    l4 = np.full(shp, -1, int)
    for i in range(shp[0]):
        for j in range(shp[1]):
            for k in range(shp[2]):
                bm = mask[2*i:2*i+2, 2*j:2*j+2, 2*k:2*k+2]
                if bm.sum() >= 4:
                    m4[i, j, k] = True
                    bl = lab[2*i:2*i+2, 2*j:2*j+2, 2*k:2*k+2]
                    bl = bl[bl >= 0]
                    if bl.size:
                        l4[i, j, k] = np.bincount(bl).argmax()
    m4 = ndimage.binary_fill_holes(m4)
    # unlabeled brain voxels take the nearest label (only matters for the shell)
    known = l4 >= 0
    _, idx = ndimage.distance_transform_edt(~known, return_indices=True)
    l4 = np.where(m4, l4[tuple(idx)], -1)
    return m4, l4


def layers(m):
    out = np.pad(~m, 1, constant_values=True)
    st = ndimage.generate_binary_structure(3, 1)
    d1 = ndimage.binary_dilation(out, st)[1:-1, 1:-1, 1:-1] & m
    rem = m & ~d1
    d2 = ndimage.binary_dilation(np.pad(~rem, 1, constant_values=True), st)[1:-1, 1:-1, 1:-1] & rem
    rem2 = rem & ~d2
    d3 = ndimage.binary_dilation(np.pad(~rem2, 1, constant_values=True), st)[1:-1, 1:-1, 1:-1] & rem2
    return d1, d2, d3  # glass, lamps, trigger


def runs(points):
    """Group (x,y,z) block coords into x-runs -> list of (x1,y,z,x2)."""
    pts = sorted(points, key=lambda p: (p[1], p[2], p[0]))
    res, cur = [], None
    for x, y, z in pts:
        if cur and cur[1] == y and cur[2] == z and cur[3] == x - 1:
            cur[3] = x
        else:
            if cur:
                res.append(tuple(cur))
            cur = [x, y, z, x]
    if cur:
        res.append(tuple(cur))
    return res


def fills(points, block):
    return [f"fill {a} {y} {z} {b} {y} {z} {block}" for a, y, z, b in runs(points)]


def w(path, lines):
    p = FN / f"{path}.mcfunction"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(lines) + "\n")


def main():
    if DP.exists():
        shutil.rmtree(DP)
    (DP / "data/minecraft/tags/function").mkdir(parents=True)
    (DP / "pack.mcmeta").write_text(json.dumps({"pack": {
        "description": "Redstone Cortex: a question lands in the brain", "min_format": 121, "max_format": 121}}))
    (DP / "data/minecraft/tags/function/load.json").write_text(json.dumps({"values": ["brain:load"]}))

    m, lab = build_volume()
    glass, lamp, trig = layers(m)
    # MNI voxel (i=x left->right, j=post->ant, k=inf->sup) -> MC block
    ii, jj, kk = np.nonzero(m)
    X0 = 14 - (ii.min() + ii.max()) // 2
    Z0 = 30 + jj.max()          # anterior end faces the board (north)
    Y0 = -60 - kk.min()

    def mc(i, j, k):
        return (int(X0 + i), int(Y0 + k), int(Z0 - j))

    build = ["# brain sculpture"]
    trig_pts = {r: [] for r in range(N)}
    per_block = {}
    for i, j, k in zip(ii, jj, kk):
        r = lab[i, j, k]
        p = mc(i, j, k)
        if glass[i, j, k]:
            per_block.setdefault("gray_stained_glass" if r == BRAINSTEM else f"{REGIONS[r][3]}_stained_glass", []).append(p)
        elif lamp[i, j, k]:
            per_block.setdefault("gray_concrete" if r == BRAINSTEM else "redstone_lamp", []).append(p)
        else:
            per_block.setdefault("white_concrete", []).append(p)
            if trig[i, j, k] and r != BRAINSTEM and r >= 0:
                trig_pts[r].append(p)
    for blk in ["white_concrete", "gray_concrete", "redstone_lamp"] + [b for b in per_block if b.endswith("glass")]:
        build += fills(per_block.get(blk, []), blk)

    # lamp coverage check: lamps with a same-region trigger neighbour
    tset = {(i, j, k) for r in range(N) for (i, j, k) in zip(*np.nonzero(trig & (lab == r)))}
    li = list(zip(*np.nonzero(lamp & (lab >= 0) & (lab < N))))
    lit = sum(any((i+a, j+b, k+c) in tset for a, b, c in
                  [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]) for i, j, k in li)
    print(f"brain {np.ptp(ii)+1}x{np.ptp(kk)+1}x{np.ptp(jj)+1} blocks, {m.sum()} voxels, "
          f"lamps {len(li)} ({100*lit/len(li):.0f}% wired), fill cmds {len(build)}")
    print({REGIONS[r][0]: len(trig_pts[r]) for r in range(N)})

    # ---- redstone board ----
    B = ["# redstone board", f"fill -2 {L0-1} -10 34 {L1+1} 26 air",
         f"fill -2 {L0-1} -10 34 {L0-1} 26 polished_andesite"]
    sup = lambda x, z: B.append(f"setblock {x} {L0} {z} smooth_stone")
    cmp_ = lambda x, y, z, f: B.append(f"setblock {x} {y} {z} comparator[facing={f},mode=compare]")
    blk = lambda x, y, z, b="target": B.append(f"setblock {x} {y} {z} {b}")
    for i in range(N):
        x0 = 4 * i
        blk(x0, L0, 2, "barrel[facing=up]")                 # vesicle pool, inhibitory copy
        cmp_(x0, L0, 1, "south")                            # Cm: reads pool -> max chain
        blk(x0, L0, 0, "light_gray_concrete")               # max chain node
        cmp_(x0 + 1, L0, 0, "west"); blk(x0 + 2, L0, 0, "light_gray_concrete"); cmp_(x0 + 3, L0, 0, "west")
        blk(x0, L1, 1, "barrel[facing=up]")                 # vesicle pool, excitatory copy
        cmp_(x0, L1, 2, "north")                            # D: decision synapse (A >= M)
        # spur from broadcast line to D's side input
        sup(x0 + 2, -1); cmp_(x0 + 2, L1, -1, "north"); blk(x0 + 2, L1, 0, "gray_concrete")
        sup(x0 + 2, 1); cmp_(x0 + 2, L1, 1, "north"); blk(x0 + 2, L1, 2, "gray_concrete")
        sup(x0 + 1, 2); cmp_(x0 + 1, L1, 2, "east")
        # axon: all-or-none repeater, then dust with repeaters
        for z in range(3, 22):
            sup(x0, z)
            if z in (3, 9, 15, 21):
                B.append(f"setblock {x0} {L1} {z} repeater[facing=north,delay={1 if z == 3 else 4}]")
            else:
                B.append(f"setblock {x0} {L1} {z} redstone_wire")
        sup(x0, 22); sup(x0 + 1, 22); sup(x0 + 2, 22); sup(x0, 23)
        blk(x0, L1, 22, f"{REGIONS[i][3]}_concrete")        # relay nucleus
        B.append(f"setblock {x0+1} {L1} 22 redstone_wall_torch[facing=east]")
        rid = REGIONS[i][0]
        B.append(f'setblock {x0} {L1} 23 command_block[facing=south]{{Command:"function brain:cortex/{rid}_on"}}')
        B.append(f'setblock {x0+2} {L1} 22 command_block[facing=east]{{Command:"function brain:cortex/{rid}_off"}}')
    # max chain tail, climb, broadcast line
    cmp_(29, L0, 0, "west"); blk(30, L0, 0, "light_gray_concrete"); cmp_(31, L0, 0, "west")
    blk(32, L0, 0, "light_gray_concrete"); cmp_(32, L0, -1, "south"); blk(32, L0, -2, "light_gray_concrete")
    B.append(f"setblock 32 {L1} -2 redstone_wire")
    for x in range(31, 1, -1):
        if x % 2:
            sup(x, -2); cmp_(x, L1, -2, "east")
        else:
            blk(x, L1, -2, "gray_concrete")
    # input station
    sx, sy, sz = SIGN
    B += [f"fill 11 {L0} -7 17 {L0} -7 polished_deepslate", f"fill 11 {L1} -7 16 {L1} -7 polished_deepslate",
          f"setblock {sx} {sy} {sz} oak_wall_sign[facing=north]",
          f'data merge block {sx} {sy} {sz} {{front_text:{{messages:["what is seven","times eight?","",""]}}}}',
          f"setblock 15 {L1} -8 stone_button[face=wall,facing=north]",
          f'setblock {BTN_CMD[0]} {BTN_CMD[1]} {BTN_CMD[2]} command_block[facing=south]{{Command:"function brain:read"}}',
          f"setblock {ANS[0]} {ANS[1]} {ANS[2]} oak_wall_sign[facing=north]",
          f'data merge block {ANS[0]} {ANS[1]} {ANS[2]} {{is_waxed:1b,front_text:{{messages:["","Ask a question","on the left sign",""]}}}}']
    B += labels()
    w("build", ["gamerule command_block_output false", "gamerule max_block_modifications 1000000",
                "function brain:build_board", "function brain:build_brain", "function brain:load",
                'tellraw @a {"text":"Redstone Cortex built.","color":"green"}'])
    w("build_board", B)
    w("build_brain", build)

    # ---- cortex on/off ----
    for r, (rid, title, desc, color, _, _) in enumerate(REGIONS):
        on = fills(trig_pts[r], "redstone_block") + [
            f'tellraw @a [{{"text":"[cortex] ","color":"gray"}},{{"text":"{title}","color":"gold","bold":true}},'
            f'{{"text":" lit up: {desc}","color":"white"}}]',
            f'data modify block {ANS[0]} {ANS[1]} {ANS[2]} front_text.messages set value '
            f'["Signal landed in:","{title[:15]}","{desc[:15]}","{desc[15:30]}"]',
            "playsound minecraft:block.amethyst_block.resonate master @a ~ ~ ~ 1 1.4"]
        w(f"cortex/{rid}_on", on)
        w(f"cortex/{rid}_off", fills(trig_pts[r], "white_concrete"))

    # ---- vesicle fills: comparator strength s from a 27-slot barrel ----
    for s in range(16):
        tot = 0 if s == 0 else math.ceil(1728 * (s - 1) / 14) or 1
        assert s == (0 if tot == 0 else 1 + int(14 * tot / 1728)), s
        lines = []
        for slot in range(27):
            c = min(64, tot); tot -= c
            item = f"minecraft:glowstone_dust {c}" if c else "minecraft:air"
            lines.append(f"$item replace block $(x) $(y) $(z) container.{slot} with {item}")
        w(f"fill/s{s}", lines)

    def pools(level, zz, mode):
        out = []
        for i, (rid, *_rest) in enumerate(REGIONS):
            arg = f"{{x:{4*i},y:{level},z:{zz}}}"
            if mode == "clear":
                out.append(f"function brain:fill/s0 {arg}")
            else:
                out += [f"execute if score {rid} brain.sig matches {s} run function brain:fill/s{s} {arg}"
                        for s in range(1, 16)]
        return out

    w("inhibit", pools(L0, 2, "set") + [
        'tellraw @a {"text":"[thalamus] inhibitory pool charging: every column learns the strongest signal...","color":"dark_aqua"}'])
    w("excite", pools(L1, 1, "set") + [
        'tellraw @a {"text":"[thalamus] excitation released: only the winner beats inhibition","color":"aqua"}',
        "schedule function brain:clear 200t"])
    w("clear", pools(L1, 1, "clear") + pools(L0, 2, "clear"))

    # ---- language parser (Wernicke stage) ----
    lc = {ch: ch for ch in "abcdefghijklmnopqrstuvwxyz"}
    lc.update({ch.upper(): ch for ch in "abcdefghijklmnopqrstuvwxyz"})
    lc.update({d: "#" for d in "0123456789"})
    lc["'"] = ""
    kw = {}
    for r, reg in enumerate(REGIONS):
        for word in reg[5].split():
            kw[word] = {"r": reg[0]}
    snbt = lambda d: "{" + ",".join(f'"{k}":' + (json.dumps(v) if not isinstance(v, dict) else snbt(v)) for k, v in d.items()) + "}"
    w("load", ["scoreboard objectives add brain.s dummy", "scoreboard objectives add brain.sig dummy",
               "scoreboard objectives add brain.t dummy",
               f"data modify storage brain:lc m set value {snbt(lc)}",
               f"data modify storage brain:kw m set value {snbt(kw)}"])
    sx, sy, sz = SIGN
    read = ["schedule clear brain:inhibit", "schedule clear brain:excite", "schedule clear brain:clear",
            "function brain:clear",
            f"data modify storage brain:p lines set from block {sx} {sy} {sz} front_text.messages",
            "function brain:lines with storage brain:p",
            "data modify storage brain:p w set value \"\"", "data modify storage brain:p hits set value []",
            "scoreboard players set #i brain.t 0",
            "execute store result score #len brain.t run data get storage brain:p q"]
    read += [f"scoreboard players set {reg[0]} brain.s 0" for reg in REGIONS]
    read += ["function brain:loop"]
    read += [f"scoreboard players set {reg[0]} brain.sig 0" for reg in REGIONS]
    read += [f"execute if score {reg[0]} brain.s matches 1.. run scoreboard players operation {reg[0]} brain.sig = {reg[0]} brain.s"
             for reg in REGIONS]
    read += ["scoreboard players set #two brain.t 2"]
    for reg in REGIONS:
        rid = reg[0]
        read += [f"scoreboard players operation {rid} brain.sig *= #two brain.t",
                 f"execute if score {rid} brain.s matches 1.. run scoreboard players add {rid} brain.sig 1",
                 f"execute if score {rid} brain.sig matches 16.. run scoreboard players set {rid} brain.sig 15"]
    allzero = " ".join(f"if score {reg[0]} brain.sig matches 0" for reg in REGIONS)
    read += [f"execute {allzero} run scoreboard players set temporal brain.sig 1",
             'tellraw @a [{"text":"[wernicke] keywords: ","color":"dark_green"},{"storage":"brain:p","nbt":"hits","color":"green"}]',
             "tellraw @a [" + ",".join(
                 f'{{"text":"{reg[0]} "}},{{"score":{{"name":"{reg[0]}","objective":"brain.sig"}},"color":"yellow"}},{{"text":"  "}}'
                 for reg in REGIONS) + "]",
             "playsound minecraft:block.note_block.chime master @a ~ ~ ~ 1 0.7",
             "schedule function brain:inhibit 10t", "schedule function brain:excite 130t"]
    w("read", read)
    w("lines", ["data modify storage brain:p l set value {}",
                "data modify storage brain:p l.a set string storage brain:p lines[0]",
                "data modify storage brain:p l.b set string storage brain:p lines[1]",
                "data modify storage brain:p l.c set string storage brain:p lines[2]",
                "data modify storage brain:p l.d set string storage brain:p lines[3]",
                "function brain:join with storage brain:p l"])
    w("join", ['$data modify storage brain:p q set value "$(a) $(b) $(c) $(d) "'])
    w("loop", ["execute if score #i brain.t >= #len brain.t run return 0",
               "execute store result storage brain:p i int 1 run scoreboard players get #i brain.t",
               "scoreboard players add #i brain.t 1",
               "execute store result storage brain:p j int 1 run scoreboard players get #i brain.t",
               "function brain:char with storage brain:p",
               'data modify storage brain:p n set value " "',
               "function brain:norm with storage brain:p",
               'execute if data storage brain:p {n:" "} unless data storage brain:p {w:""} run function brain:check with storage brain:p',
               'execute if data storage brain:p {n:" "} run data modify storage brain:p w set value ""',
               'execute unless data storage brain:p {n:" "} run function brain:app with storage brain:p',
               "function brain:loop"])
    w("char", ["$data modify storage brain:p c set string storage brain:p q $(i) $(j)"])
    w("norm", ['$data modify storage brain:p n set from storage brain:lc m."$(c)"'])
    w("app", ['$data modify storage brain:p w set value "$(w)$(n)"'])
    w("check", ['$execute if data storage brain:kw m."$(w)" run data modify storage brain:p hits append value "$(w)"',
                '$execute if data storage brain:kw m."$(w)" run function brain:hit with storage brain:kw m."$(w)"'])
    w("hit", ["$scoreboard players add $(r) brain.s 1"])


def labels():
    """Wall signs that explain each part, placed along the board."""
    S = []
    def sign(x, z, lines, facing="north", y=L1 + 1):
        S.append(f"setblock {x} {y-1} {z} polished_andesite")
        S.append(f"setblock {x} {y} {z} oak_sign[rotation={ {'south':0,'west':4,'north':8,'east':12}[facing] }]")
        msgs = ",".join(json.dumps(l[:15]) for l in (lines + ["", "", "", ""])[:4])
        S.append(f"data merge block {x} {y} {z} {{is_waxed:1b,front_text:{{messages:[{msgs}]}}}}")
    sign(-2, 2, facing="west", lines=["BARREL", "= vesicle pool", "items = amount", "of transmitter"])
    sign(-2, 0, facing="west", lines=["COMPARATOR", "= synapse", "passes graded", "strength 0-15"])
    sign(-2, -2, facing="west", lines=["GRAY LINE", "= inhibitory", "interneurons", "carry the MAX"])
    sign(-2, 4, facing="west", lines=["REPEATER", "= axon hillock", "all-or-none", "spike (15)"])
    sign(-2, 12, facing="west", lines=["DUST + REPEATER", "= myelinated", "axon, repeater", "= Ranvier node"])
    sign(-2, 22, facing="west", lines=["TORCH = NOT", "= inhibitory", "inverter, turns", "region off"])
    sign(-2, 24, facing="west", lines=["COMMAND BLOCK", "= thalamic", "relay into", "the cortex"])
    sign(18, -8, lines=["SIGN = stimulus", "BUTTON =", "sensory receptor", "-> parser"])
    return S


if __name__ == "__main__":
    main()
