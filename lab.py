"""Laboratory shell, brain plinth, observation balcony, legend and camera presets."""
import json
import numpy as np
from scipy import ndimage

X0, X1, Z0, Z1 = -76, 106, -96, 186       # interior bounds
FLOOR, TOP = -61, 0
NAMES = {"prefrontal": "Prefrontal · planning, emotion", "broca": "Broca · speech, grammar",
         "motor": "Motor · movement", "somato": "Somatosensory · touch, pain",
         "parietal": "Parietal · number, space", "temporal": "Temporal · sound, memory, meaning",
         "occipital": "Occipital · vision", "cerebellum": "Cerebellum · balance, timing"}
TEXT_COLOR = {"light_blue": "aqua", "purple": "light_purple", "red": "red", "orange": "gold",
              "yellow": "yellow", "lime": "green", "blue": "blue", "pink": "light_purple"}

CAMERAS = {  # name: (x, y, z, yaw, pitch); spectator mode so the camera stays put
    "1_reveal": (16, -28, 18, 0, 30), "2_input": (8, -57.4, -79, 0, 25), "3_processor": (16, -40, -70, 0, 62),
    "4_decision": (16, -44, -28, 0, 58), "5_axons": (16, -48, -8, 0, 28), "6_brain_top": (16, -4, 107, 180, 90),
    "7_wide": (16, -14, -92, 0, 24)}


def td(x, y, z, text, scale, color="white", tag="lab", bb="vertical", width=400):
    return (f'summon text_display {x} {y} {z} {{billboard:"{bb}",line_width:{width},background:1342177280,'
            f'text:{{text:{json.dumps(text)},color:"{color}"}},Tags:["{tag}"],'
            f'transformation:{{left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],'
            f'translation:[0f,0f,0f],scale:[{scale}f,{scale}f,{scale}f]}}}}')


def build(mx0, W, H, MAP_Z0, grid, M, region_labels, feeds, colors, fills, hgt):
    L = ["kill @e[type=text_display,tag=lab]"]
    # floor, walls, roof
    L += [f"fill {X0} {FLOOR} {Z0} {X1} {FLOOR} {Z1} polished_deepslate replace grass_block"]
    for x in range(X0, X1 + 1, 24):                        # floor light lines
        L.append(f"fill {x} {FLOOR} {Z0} {x} {FLOOR} {Z1} deepslate_tiles replace polished_deepslate")
    for (a, b, c, d) in [(X0 - 1, Z0 - 1, X1 + 1, Z0 - 1), (X0 - 1, Z1 + 1, X1 + 1, Z1 + 1),
                         (X0 - 1, Z0 - 1, X0 - 1, Z1 + 1), (X1 + 1, Z0 - 1, X1 + 1, Z1 + 1)]:
        L += [f"fill {a} {FLOOR} {b} {c} {TOP} {d} polished_blackstone_bricks",
              f"fill {a} -50 {b} {c} -46 {d} tinted_glass",
              f"fill {a} -58 {b} {c} -58 {d} waxed_oxidized_cut_copper"]
    for x in range(X0, X1 + 1, 16):                        # wall pillars with light cores
        for z in (Z0, Z1):
            L += [f"fill {x} {FLOOR+1} {z} {x} {TOP-1} {z} deepslate_tiles", f"fill {x} -52 {z} {x} -44 {z} sea_lantern"]
    for z in range(Z0, Z1 + 1, 16):
        for x in (X0, X1):
            L += [f"fill {x} {FLOOR+1} {z} {x} {TOP-1} {z} deepslate_tiles", f"fill {x} -52 {z} {x} -44 {z} sea_lantern"]
    L.append(f"fill {X0-1} -36 {Z0-1} {X1+1} -36 {Z1+1} air replace black_stained_glass")   # v3.1 roof height
    L.append(f"fill {X0-1} {TOP} {Z0-1} {X1+1} {TOP} {Z1+1} black_stained_glass")

    # brain plinth: 2-block ring around the cortex, skipping tract entries
    brain = grid != -2
    ring = ndimage.binary_dilation(brain, iterations=2) & ~brain
    fx = [f[0] for f in feeds]
    pts = []
    for x, z in zip(*np.nonzero(ring)):
        wx, wz = M(x, z)
        if wz < MAP_Z0 + 2 and any(abs(wx - f) <= 1 for f in fx):
            continue
        pts.append((wx, wz))
    L += fills(pts, -60, "polished_blackstone") + fills(pts, -59, "polished_blackstone")
    L += fills(pts, -58, "polished_blackstone") + fills(pts, -57, "waxed_oxidized_cut_copper")
    L += fills(pts, -56, "tinted_glass")

    # soft ambient light over the cortex so idle anatomy reads (invisible light blocks)
    for x in range(0, W, 7):
        for z in range(0, H, 7):
            if brain[x, z]:
                wx, wz = M(x, z)
                L.append(f"setblock {wx} {-52 + int(hgt[x, z])} {wz} light[level=6]")
    # (an observation balcony was removed after in-client screenshots showed it hiding the brain)
    L.append("fill -44 -48 34 76 -46 40 air")
    for x in range(-44, 77, 12):
        L.append(f"fill {x} {FLOOR+1} 37 {x} -49 37 air replace deepslate_tiles")
    L += composition(ring_outer=ndimage.binary_dilation(brain, iterations=5) & ~ndimage.binary_dilation(brain, iterations=4),
                     M=M, fills=fills)
    # titles, legend, region labels
    L.append(td(16, -42, 44, "E · ANATOMICAL BRAIN\nleft hemisphere, Harvard-Oxford atlas, 12,856 lamp neurons", 3, "aqua", width=600))
    legend = "\n".join(NAMES[r] for r in NAMES)
    L.append(td(mx0 - 8, -48, MAP_Z0 + 20, "REGIONS\n" + legend, 1.6, "white", width=400))
    for rid, x, z, y in region_labels:
        L.append(td(x, y, z, NAMES[rid].split(" · ")[0], 4, TEXT_COLOR.get(colors[rid], "white"), bb="center"))
    L.append(td(16, -40, -88, "REDSTONE CORTEX\na neuroscience-inspired circuit model in vanilla Minecraft", 3, "white", width=700))
    return L


def cameras(w):
    for name, (x, y, z, yaw, pitch) in CAMERAS.items():
        w(f"cam/{name}", ["gamemode spectator @p", f"tp @p {x} {y} {z} {yaw} {pitch}"])


def composition(ring_outer, M, fills):
    """Lighting hierarchy: lit walkway A->E, glowing zone outlines, brain halo, wall light bands, soft ambient."""
    L = []
    flo = lambda x1, z1, x2, z2, blk: f"fill {x1} {FLOOR} {z1} {x2} {FLOOR} {z2} {blk} replace polished_deepslate"
    L += [flo(12, Z0, 20, 44, "polished_blackstone_bricks"),               # central walkway
          flo(11, Z0, 11, 44, "sea_lantern"), flo(21, Z0, 21, 44, "sea_lantern")]
    for (x1, z1, x2, z2) in [(-20, -86, 36, -68), (-4, -66, 36, -26), (-6, -24, 38, 46)]:   # zones A, B, C+D
        L += [flo(x1, z1, x2, z1, "sea_lantern"), flo(x1, z2, x2, z2, "sea_lantern"),
              flo(x1, z1, x1, z2, "sea_lantern"), flo(x2, z1, x2, z2, "sea_lantern")]
    pts = [M(x, z) for x, z in zip(*np.nonzero(ring_outer))]
    L += [f"{c} replace polished_deepslate" for c in fills(pts, FLOOR, "sea_lantern")]   # halo around the brain
    for (a, b, c, d) in [(X0, Z0, X1, Z0), (X0, Z1, X1, Z1), (X0, Z0, X0, Z1), (X1, Z0, X1, Z1)]:
        L += [f"fill {a} -40 {b} {c} -40 {d} sea_lantern", f"fill {a} -20 {b} {c} -20 {d} sea_lantern"]
    for x in range(X0 + 6, X1, 14):                                        # soft ambient above the floor
        for z in range(Z0 + 6, Z1, 14):
            L.append(f"setblock {x} -48 {z} light[level=9]")
    return L
