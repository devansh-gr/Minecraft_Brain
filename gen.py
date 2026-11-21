"""Redstone Cortex v2 generator (Minecraft 26.3).

Only the sign reader is commands. Everything after the barrels is redstone:
comparator winner-take-all, lamp axons, and dust meshes on a flat lamp cortex
that light ring by ring through repeaters.
"""
import json, re, math, shutil
from collections import deque
from pathlib import Path
import numpy as np
import nibabel as nib
from scipy import ndimage
from nilearn import datasets, image
from lexicon import LEX
import dp as net, lab, upright

ROOT = Path(__file__).parent
DP = ROOT / "build" / "datapack" / "redstone_cortex"
FN = DP / "data" / "brain" / "function"

L0, L1 = -60, -59            # board: max layer, decision layer (tracts run on L1)
LAMP, MESH = -58, -57        # cortex map: lamp layer, dust layer
SIGN = (14, -59, -26)
MM_PER_BLOCK = 1.3
RING = 5                     # dust cells between repeater rings
RING_DELAY = 2
MAP_X0, MAP_Z0 = None, 46    # map north edge; x set to centre on the board

# id, colour, Harvard-Oxford cortical labels, note-block instrument block, note
REGIONS = [
    ("prefrontal", "light_blue", [1, 3, 4, 25, 27, 28, 29, 33], "gold_block", 12),
    ("broca", "purple", [5, 6, 41], "emerald_block", 16),
    ("motor", "red", [7, 26], "iron_block", 19),
    ("somato", "orange", [17, 42], "bone_block", 14),
    ("parietal", "yellow", [18, 19, 20, 21, 30, 31, 43], "packed_ice", 21),
    ("temporal", "lime", [2, 8, 9, 10, 11, 12, 13, 14, 15, 16, 34, 35, 37, 38, 44, 45, 46], "clay", 9),
    ("occipital", "blue", [22, 23, 24, 32, 36, 39, 40, 47, 48], "glowstone", 24),
    ("cerebellum", "pink", [], "white_wool", 7),
]
TITLES = {"prefrontal": "Prefrontal", "broca": "Broca", "motor": "Motor", "somato": "Touch",
          "parietal": "Parietal", "temporal": "Temporal", "occipital": "Visual", "cerebellum": "Cerebellum"}
N = len(REGIONS)
STEM = N
NB4 = [(1, 0), (-1, 0), (0, 1), (0, -1)]


# ---------------------------------------------------------------- atlas -> 2D map
def lateral_map():
    cort = datasets.fetch_atlas_harvard_oxford("cort-maxprob-thr0-1mm", data_dir=str(ROOT / "atlas"))
    sub = datasets.fetch_atlas_harvard_oxford("sub-maxprob-thr0-1mm", data_dir=str(ROOT / "atlas"))
    cimg = cort.maps if hasattr(cort.maps, "get_fdata") else nib.load(cort.maps)
    simg = sub.maps if hasattr(sub.maps, "get_fdata") else nib.load(sub.maps)
    c = np.asarray(cimg.get_fdata(), int)
    s = np.asarray(simg.get_fdata(), int)
    mimg = image.resample_to_img(datasets.load_mni152_brain_mask(resolution=1), cimg, interpolation="nearest")
    mask = (np.asarray(mimg.get_fdata()) > 0.5) | (c > 0) | (s > 0)
    lab = np.full(c.shape, -1, int)
    for r, reg in enumerate(REGIONS):
        for l in reg[2]:
            lab[c == l] = r
    lab[s == sub.labels.index("Brain-Stem")] = STEM
    zs = np.arange(c.shape[2])[None, None, :]
    lab[mask & (c == 0) & (s == 0) & (zs < 68)] = REGIONS.index(next(x for x in REGIONS if x[0] == "cerebellum"))
    # left hemisphere seen from the left: first brain voxel along +x
    half = c.shape[0] // 2
    m = mask[:half]
    L = lab[:half]
    hit = m.any(axis=0)
    first = np.argmax(m, axis=0)
    jj, kk = np.indices(hit.shape)
    surf = np.where(hit, L[first, jj, kk], -2)          # -2 outside
    # unlabeled surface voxels: look a few voxels deeper, then nearest label
    for depth in range(1, 8):
        miss = hit & (surf == -1)
        if not miss.any():
            break
        d = np.clip(first + depth, 0, half - 1)
        surf = np.where(miss, L[d, jj, kk], surf)
    known = surf >= 0
    _, idx = ndimage.distance_transform_edt(~known, return_indices=True)
    surf = np.where(hit, surf[tuple(idx)], -2)
    # resample to blocks: rows = superior->inferior (z), cols = anterior->posterior
    ys = np.arange(surf.shape[0] - 1, -1, -MM_PER_BLOCK)   # anterior first
    zz = np.arange(surf.shape[1] - 1, -1, -MM_PER_BLOCK)   # superior first
    iy, iz = np.round(ys).astype(int)[:, None], np.round(zz).astype(int)[None, :]
    grid = surf[iy, iz]                                        # [col, row]
    depth = first[iy, iz].astype(float)                        # mm from the left edge to the cortical surface
    keep_c = np.where((grid != -2).any(axis=1))[0]
    keep_r = np.where((grid != -2).any(axis=0))[0]
    crop = (slice(keep_c.min(), keep_c.max() + 1), slice(keep_r.min(), keep_r.max() + 1))
    grid, depth = grid[crop], depth[crop]
    # drop specks: keep the largest component of each region
    for r in range(N):
        lbl, n = ndimage.label(grid == r)
        if n > 1:
            sizes = ndimage.sum(np.ones_like(lbl), lbl, range(1, n + 1))
            big = 1 + int(np.argmax(sizes))
            for k in range(1, n + 1):
                if k != big:
                    sel = lbl == k
                    # give the speck to its most common neighbour region
                    ring = ndimage.binary_dilation(sel) & ~sel & (grid >= 0)
                    vals = grid[ring]
                    vals = vals[vals != r]
                    grid[sel] = np.bincount(vals).argmax() if vals.size else -2
    return grid, depth  # grid[x][z]


# ---------------------------------------------------------------- 3D relief from the volumetric surface
STAGGER = 5          # upright: extra axon delay per board column (redstone ticks)
MODE = "upright"      # "upright": volumetric brain (upright.py); "relief": v3.2 relief map
RELIEF = True          # (relief mode) False -> flat map (v3 fallback)
RELIEF_SCALE = 0.45    # fraction of the true lateral bulge kept (slope must stay <= 1 block per block)
HMAX = 16
TERRACE = 3


def lipschitz(h, fixed=()):
    """Lower h until 4-neighbours differ by at most 1 (outside the brain counts as 0)."""
    while True:
        p = np.pad(h, 1)
        lim = np.minimum.reduce([p[:-2, 1:-1], p[2:, 1:-1], p[1:-1, :-2], p[1:-1, 2:]]) + 1
        new = np.minimum(h, lim)
        if (new == h).all():
            return h
        h = new


def relief_heights(grid, depth, feeds):
    brain = grid != -2
    if not RELIEF:
        return np.zeros(grid.shape, int)
    bulge = np.where(brain, depth[brain].max() - depth, 0) / MM_PER_BLOCK * RELIEF_SCALE
    # terraces: quantised heights leave wide flat bands where repeaters can sit
    h = np.where(brain, np.minimum(np.floor(bulge / TERRACE) * TERRACE, HMAX), 0).astype(int)
    for _ in range(50):
        old = h.copy()
        for fx, fz in feeds:            # feeds sit on torch ladders: height multiple of 4, no higher neighbour
            h[fx, fz] -= h[fx, fz] % 4
            for a, b in NB4:
                h[fx + a, fz + b] = min(h[fx + a, fz + b], h[fx, fz])
        h = lipschitz(h)
        if (h == old).all():
            break
    assert all(h[f] % 4 == 0 for f in feeds)
    return h


def pick_feed(grid, r):
    """Deepest interior cell of region r (taxicab distance to its border)."""
    W, H = grid.shape
    cells = grid == r
    inner = cells & ~np.pad(~cells, 1, constant_values=True)[:-2, 1:-1] & ~np.pad(~cells, 1, constant_values=True)[2:, 1:-1] \
        & ~np.pad(~cells, 1, constant_values=True)[1:-1, :-2] & ~np.pad(~cells, 1, constant_values=True)[1:-1, 2:]
    dist = ndimage.distance_transform_cdt(inner, metric="taxicab")
    return tuple(int(v) for v in np.unravel_index(np.argmax(dist), dist.shape))


# ---------------------------------------------------------------- dust mesh design
GLASS_INTERIOR = False   # True: tinted glass over every cell (v3 look); False: bare lamps, coloured borders
BEAMS = 3   # beacons per region (falls back to fewer when a region has no room)


def plan_beacons(feed, inner, hgt):
    """Beam bank under a region. The torch on the feed block powers a dust line; branches feed sticky pistons
    that hold shutter blocks in the beam columns. Region fires -> torch off -> all pistons retract -> beams.
    Cells are map-grid coordinates. A piston also reads power at the space above it (quasi-connectivity), so
    where that space is in the lamp layer (height 0) its neighbours must not carry dust."""
    fx, fz = feed
    for n in range(BEAMS, 0, -1):
        for sd in (1, -1):
            for dz in (1, -1):
                zs = [fz + dz * 3 * k for k in range(n)]
                torch = (fx + sd, fz)
                line = [(fx + 2 * sd, fz + dz * t) for t in range(3 * (n - 1) + 1)]
                branches = [(fx + 3 * sd, z) for z in zs]
                pistons = [(fx + 4 * sd, z) for z in zs]
                shutters = [(fx + 5 * sd, z) for z in zs]
                columns = [(fx + 6 * sd, z) for z in zs]
                excl = set(columns)
                for c in [torch] + pistons:
                    if hgt[c] == 0:
                        excl |= {c} | {(c[0] + a, c[1] + b) for a, b in NB4}
                if excl <= inner and all(0 <= c[0] < hgt.shape[0] and 0 <= c[1] < hgt.shape[1]
                                          for c in line + branches + pistons + shutters):
                    return dict(side=sd, dz=dz, torch=torch, line=line, branches=branches, pistons=pistons,
                                shutters=shutters, columns=columns, excl=excl)
    return None


def build_bank(bank, M, feeds, r, MAP_Z0, color):
    """Blocks for a beam bank (world coordinates via M). Asserts no contact with other regions' tracts."""
    sd = bank["side"]; f = "east" if sd > 0 else "west"
    wc = lambda c: M(*c)
    mech = [bank["torch"]] + bank["line"] + bank["branches"] + bank["pistons"] + bank["shutters"] + bank["columns"]
    for r2, (ox, oz) in enumerate(feeds):
        if r2 != r:
            for c in mech:
                x, z = wc(c)
                assert not (abs(x - ox) <= 1 and MAP_Z0 <= z < oz), f"beam bank of {r} touches tract of {r2}"
    out = []
    tx, tz = wc(bank["torch"])
    out.append(f"setblock {tx} {L1} {tz} redstone_wall_torch[facing={f}]")
    for c in bank["line"] + bank["branches"]:
        x, z = wc(c)
        out += [f"setblock {x} {L0} {z} smooth_stone", f"setblock {x} {L1} {z} redstone_wire"]
    for p, sh, col in zip(bank["pistons"], bank["shutters"], bank["columns"]):
        (px, pz), (sx, sz), (bx, bz) = wc(p), wc(sh), wc(col)
        out += [f"fill {bx-1} -64 {bz-1} {bx+1} -64 {bz+1} iron_block", f"setblock {bx} -63 {bz} beacon",
                f"fill {bx} -62 {bz} {bx} -60 {bz} glass", f"setblock {bx} {L1} {bz} air",
                f"setblock {sx} {L1} {sz} black_concrete", f"setblock {px} {L1} {pz} sticky_piston[facing={f}]",
                f"setblock {bx} {lab.TOP} {bz} air"]
    return out


def design_region(grid, r, hgt, feed):
    W, H = grid.shape
    cells = {(x, z) for x, z in zip(*np.nonzero(grid == r))}
    def inb(x, z):
        return 0 <= x < W and 0 <= z < H
    boundary = {(x, z) for (x, z) in cells
                if any(not inb(x + a, z + b) or grid[x + a, z + b] != r for a, b in NB4)}
    inner = cells - boundary
    assert feed in inner
    bank = plan_beacons(feed, inner, hgt)
    assert bank, f"no room for a beacon in region {r}"
    excl = bank["excl"]
    side, column = bank["side"], bank["columns"][0]
    mesh = inner - {feed} - excl
    d = {feed: 0}
    q = deque([feed])
    while q:
        x, z = q.popleft()
        for a, b in NB4:
            n = (x + a, z + b)
            if n in mesh and n not in d:
                d[n] = d[(x, z)] + 1
                q.append(n)
    mesh = {c for c in mesh if c in d}                  # unreachable bits become plain lamps
    # circular rings: zone = floor(euclidean distance / (RING+1)); a cell is a cut cell if a 4-neighbour
    # lies in a lower zone. Zones change by at most 1 between neighbours, so cuts separate them.
    zone = {c: int(math.hypot(c[0] - feed[0], c[1] - feed[1]) // (RING + 1)) for c in mesh}
    cut = {c for c in mesh if any(zone.get((c[0] + a, c[1] + b), zone[c]) < zone[c] for a, b in NB4)}
    reps = {}
    for c in sorted(cut, key=lambda c: (zone[c], c)):
        x, z = c
        for a, b in NB4:
            back, front = (x - a, z - b), (x + a, z + b)
            if back in mesh and front in mesh and back not in cut and front not in cut \
                    and zone[back] < zone[c] and zone[front] == zone[c] \
                    and hgt[back] - hgt[c] in (0, 1) and hgt[front] - hgt[c] in (-1, 0, 1) \
                    and not any((x + p, z + s) in reps for p, s in NB4):
                reps[c] = (a, b)                        # signal flows along (a, b)
                break
    dust = mesh - cut
    # downhill front: the repeater fires into the lower cell's glass slot, so that slot holds a lamp (a
    # conductor) which then powers the dust beneath it. A capped dust cannot connect uphill.
    caps = {(c[0] + a, c[1] + b) for c, (a, b) in reps.items() if hgt[c[0] + a, c[1] + b] == hgt[c] - 1}

    def linked(a, b):
        dh = int(hgt[b]) - int(hgt[a])
        return abs(dh) <= 1 and not (dh == 1 and a in caps) and not (dh == -1 and b in caps)
    # simulate dust strength to find dark cells
    power = {}
    src = deque()
    for a, b in NB4:
        n = (feed[0] + a, feed[1] + b)
        if n in dust:
            power[n] = 14
            src.append(n)
    changed = True
    while changed:
        changed = False
        q = deque(c for c in power)
        while q:
            c = q.popleft()
            for a, b in NB4:
                n = (c[0] + a, c[1] + b)
                if n in dust and linked(c, n) and power.get(n, 0) < power[c] - 1:
                    power[n] = power[c] - 1
                    q.append(n)
        for c, (a, b) in reps.items():
            back, front = (c[0] - a, c[1] - b), (c[0] + a, c[1] + b)
            if power.get(back, 0) > 0 and power.get(front, 0) < 15:
                power[front] = 15
                changed = True
    lit = {c for c in dust if power.get(c, 0) > 0}
    return dict(cells=cells, boundary=boundary, feed=feed, dust=dust, cut=cut, reps=reps,
                lit=lit, rings=max(zone.values()), side=side, excl=excl, column=column, caps=caps, bank=bank)


# ---------------------------------------------------------------- helpers
def runs(points, y):
    pts = sorted(points, key=lambda p: (p[1], p[0]))
    res, cur = [], None
    for x, z in pts:
        if cur and cur[1] == z and cur[2] == x - 1:
            cur[2] = x
        else:
            if cur:
                res.append(tuple(cur))
            cur = [x, z, x]
    if cur:
        res.append(tuple(cur))
    return [f"fill {a} {y} {z} {b} {y} {z}" for a, z, b in res]


def fills3(points, block):
    """(x, y, z) points -> x-run fill commands."""
    byyz = {}
    for x, y, z in points:
        byyz.setdefault((y, z), []).append(x)
    out = []
    for (y, z), xs in sorted(byyz.items()):
        xs.sort()
        a = b = xs[0]
        for x in xs[1:] + [None]:
            if x is not None and x == b + 1:
                b = x
                continue
            out.append(f"fill {a} {y} {z} {b} {y} {z} {block}")
            if x is not None:
                a = b = x
    return out


def fills(points, y, block):
    return [f"{f} {block}" for f in runs(points, y)]


def w(path, lines):
    p = FN / f"{path}.mcfunction"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(lines) + "\n")


FACE = {(0, 1): "north", (0, -1): "south", (1, 0): "west", (-1, 0): "east"}  # flow dir -> repeater facing


def route(path, y_support, y, support_block, out, delay=4, every=7):
    """Lay dust along a cell path with repeaters, never on corners."""
    for k, (x, z) in enumerate(path):
        out.append(f"setblock {x} {y_support} {z} {support_block(x, z)}")
        prev = path[k - 1] if k else None
        nxt = path[k + 1] if k + 1 < len(path) else None
        straight = prev and nxt and (x - prev[0], z - prev[1]) == (nxt[0] - x, nxt[1] - z)
        if k == 0 or k == len(path) - 1 or (straight and k % every == 0 and k < len(path) - 2):
            fl = (x - prev[0], z - prev[1]) if prev else (nxt[0] - x, nxt[1] - z)
            out.append(f"setblock {x} {y} {z} repeater[facing={FACE[fl]},delay={1 if k == 0 else delay}]")
        else:
            out.append(f"setblock {x} {y} {z} redstone_wire")


# ---------------------------------------------------------------- main
def main():
    if DP.exists():
        shutil.rmtree(DP)
    (DP / "data/minecraft/tags/function").mkdir(parents=True)
    (DP / "pack.mcmeta").write_text(json.dumps({"pack": {
        "description": "Redstone Cortex v2", "min_format": 121, "max_format": 121}}))
    (DP / "data/minecraft/tags/function/load.json").write_text(json.dumps({"values": ["brain:load"]}))

    grid, depth = lateral_map()
    W, H = grid.shape
    mx0 = 16 - W // 2
    feed_cells = [pick_feed(grid, r) for r in range(N)]
    hgt = relief_heights(grid, depth, feed_cells)
    designs = [design_region(grid, r, hgt, feed_cells[r]) for r in range(N)]
    print(f"relief: max height {hgt.max()}, mean {hgt[grid != -2].mean():.1f} blocks")
    tot = sum(len(dz["dust"]) for dz in designs)
    print("beams per region:", [len(dz["bank"]["columns"]) for dz in designs])
    print(f"map {W}x{H} = {(grid >= 0).sum()} cells, dust {tot}, "
          f"lamps lit {100 * sum(len(dz['lit']) for dz in designs) / tot:.1f}%")
    for r, dz in enumerate(designs):
        print(f"  {REGIONS[r][0]:10s} cells {len(dz['cells']):5d} dust {len(dz['dust']):5d} "
              f"reps {len(dz['reps']):3d} rings {dz['rings']:2d} lit {100*len(dz['lit'])/max(1,len(dz['dust'])):.0f}%")

    M = lambda x, z: (int(mx0 + x), int(MAP_Z0 + z))  # map cell -> world x,z
    feeds = [M(*dz["feed"]) for dz in designs]
    U = None
    if MODE == "upright":
        U = upright.build(ROOT, REGIONS, STEM, fills3)
        feeds = [U["base"][r] for r in range(N)]
        print("upright:", U["stats"])
    # board column order follows feed x so tracts never cross
    order = sorted(range(N), key=lambda r: feeds[r][0])
    xs = [feeds[r][0] for r in order]
    assert all(b - a >= 3 for a, b in zip(xs, xs[1:])), xs
    col = {r: k for k, r in enumerate(order)}      # region -> board column

    # ---------------- board
    B = [f"fill -4 {L0-1} -24 36 {L1+2} 44 air", f"fill -4 {L0-1} -24 36 {L0-1} 44 polished_andesite"]
    sup = lambda x, z: B.append(f"setblock {x} {L0} {z} smooth_stone")
    cmp_ = lambda x, y, z, f: B.append(f"setblock {x} {y} {z} comparator[facing={f},mode=compare]")
    blk = lambda x, y, z, b: B.append(f"setblock {x} {y} {z} {b}")
    for k in range(N):
        x0 = 4 * k
        blk(x0, L0, 2, "barrel[facing=up]")
        cmp_(x0, L0, 1, "south")
        blk(x0, L0, 0, "light_gray_concrete")
        cmp_(x0 + 1, L0, 0, "west"); blk(x0 + 2, L0, 0, "light_gray_concrete"); cmp_(x0 + 3, L0, 0, "west")
        blk(x0, L1, 1, "barrel[facing=up]")
        cmp_(x0, L1, 2, "north")
        sup(x0 + 2, -1); cmp_(x0 + 2, L1, -1, "north"); blk(x0 + 2, L1, 0, "gray_concrete")
        sup(x0 + 2, 1); cmp_(x0 + 2, L1, 1, "north"); blk(x0 + 2, L1, 2, "gray_concrete")
        sup(x0 + 1, 2); cmp_(x0 + 1, L1, 2, "east")
        # competition display: barrel3 -> D'' (A >= M) -> lamp bar, length = surviving strength
        sup(x0 + 2, -3); cmp_(x0 + 2, L1, -3, "south"); blk(x0 + 2, L1, -4, "gray_concrete")
        sup(x0 + 1, -4); cmp_(x0 + 1, L1, -4, "east")
        blk(x0, L1, -3, "barrel[facing=up]")
        sup(x0, -4); cmp_(x0, L1, -4, "south")
        for z in range(-5, -20, -1):
            blk(x0, L0, z, "redstone_lamp"); blk(x0, L1, z, "redstone_wire")
        # lesion lever + warning lamp
        sup(x0, -21); B.append(f"setblock {x0} {L1} -21 lever[face=floor,facing=north]")
        blk(x0, L1, -22, "redstone_lamp")
    cmp_(29, L0, 0, "west"); blk(30, L0, 0, "light_gray_concrete"); cmp_(31, L0, 0, "west")
    blk(32, L0, 0, "light_gray_concrete"); cmp_(32, L0, -1, "south"); blk(32, L0, -2, "light_gray_concrete")
    B.append(f"setblock 32 {L1} -2 redstone_wire")
    for x in range(31, 1, -1):
        if x % 2:
            sup(x, -2); cmp_(x, L1, -2, "east")
        else:
            blk(x, L1, -2, "gray_concrete")

    # ---------------- tracts: board -> fan -> under the map -> feed
    T = ["# axons"]
    left = [k for k in range(N) if xs[k] < 4 * k]
    right = [k for k in range(N) if xs[k] > 4 * k]
    turn = {}
    for n, k in enumerate(left):
        turn[k] = 24 + 2 * n
    for n, k in enumerate(reversed(right)):
        turn[k] = 24 + 2 * n
    for k in range(N):
        r = order[k]
        x0, fx, fz = 4 * k, feeds[r][0], feeds[r][1]
        tz = turn.get(k, 24)
        path = [(x0, z) for z in range(3, tz + 1)]
        step = 1 if fx > x0 else -1
        path += [(x, tz) for x in range(x0 + step, fx + step, step)] if fx != x0 else []
        path += [(fx, z) for z in range(tz + 1, fz)]
        front = min(z for x, z in U["footprint"]) if U else MAP_Z0
        lampsup = lambda x, z: "redstone_lamp" if z < front else "smooth_stone"
        route(path, L0, L1, lampsup, T, delay=2)
        if U:   # stagger axons by STAGGER redstone ticks per column: tied regions climb their ladders in turn
            D = 4 + STAGGER * k
            n = -(-D // 4)
            for j, z in enumerate([10, 17, 8, 14, 19, 9, 15, 20, 11, 16, 21, 18][:n]):
                T.append(f"setblock {x0} {L1} {z} repeater[facing=north,delay={D // n + (j < D % n)}]")
        T += [f"setblock {x0} {L1} 12 comparator[facing=north,mode=subtract]",
              f"setblock {x0+1} {L0} 12 glass", f"setblock {x0+1} {L1} 12 redstone_wire",
              f"setblock {x0+2} {L0} 12 redstone_lamp", f"setblock {x0+2} {L1} 12 lever[face=floor,facing=north]"]
        T.append(f"setblock {fx} {L1} {fz} smooth_stone")       # feed block (strongly powered by the tract)
        T.append(f"setblock {fx} {L0} {fz} smooth_stone")
        if U:                                                   # upright: the ladder comes with the brain
            inst, note = REGIONS[r][3], REGIONS[r][4]
            T += [f"setblock {x0+1} {L0} 6 redstone_lamp", f"setblock {x0+1} {L1} 6 redstone_wire",
                  f"setblock {x0+2} {L0} 6 {inst}", f"setblock {x0+2} {L1} 6 note_block[note={note}]"]
            continue
        # torch ladder up to the relief: torch, block, torch, block ... each torch inverts, so a feed height
        # that is a multiple of 4 keeps the top block powered exactly when the tract is
        hf = int(hgt[feed_cells[r]])
        for j in range(1, hf + 1):
            T.append(f"setblock {fx} {L1 + j} {fz} {'redstone_torch' if j % 2 else 'smooth_stone'}")
        T.append(f"setblock {fx} {LAMP + hf} {fz} redstone_wire")
        T += build_bank(designs[r]["bank"], M, feeds, r, MAP_Z0, REGIONS[r][1])
        # note block branch: dust off the tract at z=6 into a note block
        inst, note = REGIONS[r][3], REGIONS[r][4]
        T += [f"setblock {x0+1} {L0} 6 redstone_lamp", f"setblock {x0+1} {L1} 6 redstone_wire",
              f"setblock {x0+2} {L0} 6 {inst}", f"setblock {x0+2} {L1} 6 note_block[note={note}]"]

    # ---------------- cortex (relief: every cell sits at its own height)
    def hfills(cells, base, block):
        out, byh = [], {}
        for c in cells:
            byh.setdefault(int(hgt[c]), []).append(c)
        for hh, cs in sorted(byh.items()):
            out += fills([M(*c) for c in cs], base + hh, block)
        return out
    C = ["# lamp cortex"]
    stem_cells = [(int(x), int(z)) for x, z in zip(*np.nonzero(grid == STEM))]
    C += hfills(stem_cells, LAMP, "gray_concrete")
    for r, dz in enumerate(designs):
        C += hfills(dz["boundary"], LAMP, f"{REGIONS[r][1]}_concrete")
        C += hfills(dz["excl"], LAMP, "glass")
        C += hfills(dz["cells"] - dz["boundary"] - {dz["feed"]} - dz["excl"], LAMP, "redstone_lamp")
    for r, dz in enumerate(designs):
        C += hfills(dz["dust"], MESH, "redstone_wire")
        for c, fl in dz["reps"].items():
            x, z = M(*c)
            C.append(f"setblock {x} {MESH + int(hgt[c])} {z} repeater[facing={FACE[fl]},delay={RING_DELAY}]")
    for r, dz in enumerate(designs):
        tint = dz["cells"] if GLASS_INTERIOR else dz["boundary"] | set(dz["bank"]["columns"])
        C += hfills(tint, MESH + 1, f"{REGIONS[r][1]}_stained_glass")
        C += hfills(dz["boundary"], MESH + 2, f"{REGIONS[r][1]}_stained_glass")   # raised sulci
    C += hfills(stem_cells, MESH + 1, "gray_stained_glass")
    for dz in designs:
        C += hfills(dz["caps"], MESH + 1, "redstone_lamp")

    if U:
        C = U["cmds"]
    # ---------------- datapack logic, console, lab
    lc = {ch: ch for ch in "abcdefghijklmnopqrstuvwxyz"}
    lc.update({ch.upper(): ch for ch in "abcdefghijklmnopqrstuvwxyz"})
    lc.update({d: "#" for d in "0123456789"})
    lc["'"] = ""
    kw = {}
    for rid, words in LEX.items():
        for word in words.split():
            kw.setdefault(word, {"r": rid})
    print(f"lexicon {len(kw)} words")
    if U:
        info = net.emit(w, REGIONS, col, [(U["probe"][r][0], U["probe"][r][2]) for r in range(N)], lc, kw,
                        [U["probe"][r][1] for r in range(N)])
    else:
        info = net.emit(w, REGIONS, col, feeds, lc, kw, [LAMP + int(hgt[f]) for f in feed_cells])
    colors = {reg[0]: reg[1] for reg in REGIONS}
    w("build_console", net.console(info["cx"], info["R"], colors))
    w("build_labels", net.labels(info["cx"], info["R"]))
    region_labels = []
    for r, dz in enumerate(designs):
        xs_, zs_ = zip(*dz["cells"])
        lx, lz = int(np.mean(xs_)), int(np.mean(zs_))
        region_labels.append((REGIONS[r][0], *M(lx, lz), MESH + 1 + max(int(hgt[c]) for c in dz["cells"]) + 6))
    if U:
        region_labels = []
        for r in range(N):
            pts = U["lit"][r]
            region_labels.append((REGIONS[r][0], int(np.mean([p[0] for p in pts])), min(p[2] for p in pts) - 8,
                                  int(np.mean([p[1] for p in pts]))))
        w("build_lab", lab.build_upright(U, region_labels, colors, fills3))
    else:
        w("build_lab", lab.build(mx0, W, H, MAP_Z0, grid, M, region_labels, feeds, colors, fills, hgt))
    lab.cameras(w)
    (DP / "data/minecraft/tags/function/tick.json").write_text(json.dumps({"values": ["brain:tick"]}))
    lo_x, hi_x = min(mx0, -4) - 2, max(mx0 + W, 36) + 2
    # only the two command limits the build itself needs; nothing else world-wide is changed
    w("build", ["gamerule max_command_sequence_length 10000000",
                "gamerule max_block_modifications 1000000", "kill @e[type=text_display,tag=brain]",
                "scoreboard players set #state brain.st 0",
                *([f"fill {U['stats']['bbox'][0]-2} {y} {U['stats']['bbox'][4]-2} {U['stats']['bbox'][1]+2} {min(y + 7, U['stats']['bbox'][3] + 2)} {U['stats']['bbox'][5]+2} air"
                   for y in range(-57, U['stats']['bbox'][3] + 3, 8)]
                  + [f"fill {min(U['stats']['bbox'][0], -60) - 2} -60 22 {max(U['stats']['bbox'][1], 40) + 2} -58 {U['stats']['bbox'][5] + 2} air"]
                  if U else
                  [f"fill {lo_x} {LAMP} {MAP_Z0-1} {hi_x} {LAMP + HMAX + 4} {MAP_Z0+H+1} air"]),
                "function brain:build_lab", "function brain:build_board", "function brain:build_tracts",
                "function brain:build_cortex", "function brain:build_console", "function brain:load",
                "function brain:build_labels", "function brain:ui/reset", "function brain:mem/show",
                "function brain:build_cleanup"])
    w("build_board", B); w("build_tracts", T); w("build_cortex", C)

    # cleanup: torches and dust knocked off during this build drop as items in the same tick (Age 0).
    # Only those are removed: Age 0 and inside the box spanned by the build's own fill/setblock commands.
    lo, hi = [10 ** 9] * 3, [-10 ** 9] * 3
    for f in (DP / "data/brain/function").glob("build_*.mcfunction"):
        for l in f.read_text().splitlines():
            m = re.match(r"(?:fill|setblock) (-?\d+) (-?\d+) (-?\d+)(?: (-?\d+) (-?\d+) (-?\d+))?", l)
            for i, v in enumerate(int(x) for x in (m.groups() if m else ()) if x is not None):
                lo[i % 3], hi[i % 3] = min(lo[i % 3], v), max(hi[i % 3], v)
    w("build_cleanup", [f"kill @e[type=item,x={lo[0]},y={lo[1]},z={lo[2]},dx={hi[0] - lo[0] + 1},dy={hi[1] - lo[1] + 1},"
                        f"dz={hi[2] - lo[2] + 1},nbt={{Age:0s}}]"])

    # test hook: list of lamp cells that must light per region
    if U:
        (ROOT / "build" / "expect.json").write_text(json.dumps({
            REGIONS[r][0]: {"feed": U["base"][r], "probe": U["probe"][r], "lit": U["lit"][r], "x": info["cx"][REGIONS[r][0]],
                            "idx": r} for r in range(N)}))
        return
    (ROOT / "build" / "expect.json").write_text(json.dumps({
        REGIONS[r][0]: {"feed": M(*dz["feed"]), "lit": [(M(*c)[0], LAMP + int(hgt[c]), M(*c)[1]) for c in sorted(dz["lit"])], "x": info["cx"][REGIONS[r][0]],
                        "idx": r} for r, dz in enumerate(designs)}))


if __name__ == "__main__":
    main()
