"""Upright volumetric brain (both hemispheres, cerebellum, brainstem) from the MNI152 tissue templates and the
Harvard-Oxford atlas, with region lighting driven by the existing redstone axons.

Orientation: MNI x (left->right) -> world z (left hemisphere faces the entrance, north);
MNI y (posterior->anterior) -> world x (frontal lobe east); MNI z (inferior->superior) -> world y.

Lighting: each region gets one vertical torch ladder rising from its axon. Ladder blocks every 4 levels are
powered exactly while the axon is; at those levels a horizontal plate of dust on lamps fills the region's
cross-section just behind the glass shell, with repeater rings for reach. Decorative voxels are unpowered.
"""
import heapq
import math
from collections import deque
import numpy as np
import nibabel as nib
from scipy import ndimage
from nilearn import datasets, image

SCALE = 1.5                 # mm per block
BASE_Y = -56                # lowest brain voxel (pedestal below)
CX = 16                     # world x of the brain's anterior-posterior centre
FRONT_Z = 64                # world z of the leftmost (north-facing) voxel
L0, L1 = -60, -59           # tract support / tract level (inside the pedestal)
MAX_EXPOSED = 6             # preferred max height of ladder visible below the brain (blocks)
RING = 8                    # dust cells between repeater rings on a plate
LINE = 2                    # dust on every LINE-th row (lamps between are lit by their powered neighbours)
RING_DELAY = 3              # repeater delay; odd vs the ladder's 4-tick plate spacing spreads the work
RISER_EXPOSED = 8            # a hidden feed's riser may show this much below the brain
MAX_LOSS = 0.15            # hide a stilt only if at most this share of the region's plate area is lost

SEAL = True                 # fill the interior with tinted glass (light-engine cost)
BAND_COST = 1000
BAND = 3                    # plate cells kept within this distance of the plate edge
NB4 = [(1, 0), (-1, 0), (0, 1), (0, -1)]


def volume(root, regions, stem_index):
    cort = datasets.fetch_atlas_harvard_oxford("cort-maxprob-thr0-1mm", data_dir=str(root / "atlas"))
    sub = datasets.fetch_atlas_harvard_oxford("sub-maxprob-thr0-1mm", data_dir=str(root / "atlas"))
    cimg = cort.maps if hasattr(cort.maps, "get_fdata") else nib.load(cort.maps)
    simg = sub.maps if hasattr(sub.maps, "get_fdata") else nib.load(sub.maps)
    c = np.asarray(cimg.get_fdata(), int)
    s = np.asarray(simg.get_fdata(), int)
    rs = lambda t: np.asarray(image.resample_to_img(t, cimg, interpolation="linear").get_fdata())
    tissue = (rs(datasets.load_mni152_gm_template(resolution=1)) + rs(datasets.load_mni152_wm_template(resolution=1))) > 0.5
    tissue &= rs(datasets.load_mni152_brain_mask(resolution=1)) > 0.5
    lab = np.full(c.shape, -1, int)
    for r, reg in enumerate(regions):
        for l in reg[2]:
            lab[c == l] = r
    lab[s == sub.labels.index("Brain-Stem")] = stem_index
    ks = np.arange(c.shape[2])[None, None, :]
    cereb = next(i for i, x in enumerate(regions) if x[0] == "cerebellum")
    lab[tissue & (c == 0) & (s == 0) & (ks < 68)] = cereb
    # resample to blocks (nearest), keep the largest connected piece, fill enclosed cavities
    idx = [np.round(np.arange(0, n - 1, SCALE)).astype(int) for n in c.shape]
    T = tissue[np.ix_(*idx)]
    Lb = lab[np.ix_(*idx)]
    comp, n = ndimage.label(T)
    T = comp == (1 + int(np.argmax(ndimage.sum(T, comp, range(1, n + 1)))))
    T = ndimage.binary_fill_holes(T)
    known = (Lb >= 0) & T
    _, near = ndimage.distance_transform_edt(~known, return_indices=True)
    Lb = np.where(T, Lb[tuple(near)], -1)
    mid = int(round(-cimg.affine[0, 3] / cimg.affine[0, 0] / SCALE))   # array index of MNI x = 0
    return T, Lb, mid


def shells(T):
    st = ndimage.generate_binary_structure(3, 1)
    outside = ~T
    l1 = T & ndimage.binary_dilation(outside, st, border_value=1)
    l2 = T & ~l1 & ndimage.binary_dilation(l1, st)
    return l1, l2


def design_plate(cells, feed):
    """Flat plate: every cell gets a lamp, but only the rim, the spokes and every LINE-th row carry dust.
    A lamp under powered dust is strongly powered and lights its lamp neighbours, so the rows between dust
    lines still light. Euclidean repeater rings give reach. Returns lamps, dust, reps, lit (dust-lit) cells."""
    cells = set(cells)
    rim = {q for q in cells if any((q[0] + a, q[1] + b) not in cells for a, b in NB4)}
    lines = {q for q in cells if (q[0] - feed[0]) % LINE == 0 or q[0] == feed[0] or q[1] == feed[1]}
    mesh = (rim | lines) - {feed}
    zone = {q: int(math.hypot(q[0] - feed[0], q[1] - feed[1]) // (RING + 1)) for q in mesh}
    # only the 4-connected piece reachable from the ladder
    seen, dq = set(), deque((feed[0] + a, feed[1] + b) for a, b in NB4)
    while dq:
        q = dq.popleft()
        if q in mesh and q not in seen:
            seen.add(q)
            dq.extend((q[0] + a, q[1] + b) for a, b in NB4)
    mesh = seen
    cut = {q for q in mesh if any(zone.get((q[0] + a, q[1] + b), zone[q]) < zone[q] for a, b in NB4)}
    reps = {}
    for q in sorted(cut, key=lambda q: (zone[q], q)):
        for a, b in NB4:
            back, front = (q[0] - a, q[1] - b), (q[0] + a, q[1] + b)
            if back in mesh and front in mesh and back not in cut and front not in cut \
                    and zone[back] < zone[q] and zone[front] == zone[q] \
                    and not any((q[0] + p, q[1] + t) in reps for p, t in NB4):
                reps[q] = (a, b)
                break
    dust = mesh - cut
    power = {n: 15 for n in ((feed[0] + a, feed[1] + b) for a, b in NB4) if n in dust}
    changed = True
    while changed:
        changed = False
        dq = deque(power)
        while dq:
            q = dq.popleft()
            for a, b in NB4:
                n = (q[0] + a, q[1] + b)
                if n in dust and power.get(n, 0) < power[q] - 1:
                    power[n] = power[q] - 1
                    dq.append(n)
        for q, (a, b) in reps.items():
            back, front = (q[0] - a, q[1] - b), (q[0] + a, q[1] + b)
            if power.get(back, 0) > 0 and power.get(front, 0) < 15:
                power[front] = 15
                changed = True
    lit = {q for q in dust if power.get(q, 0) > 0}
    glow = lit | {(q[0] + a, q[1] + b) for q in lit for a, b in NB4 if (q[0] + a, q[1] + b) in cells}
    return dict(lamps=cells - {feed}, mesh=mesh, dust=dust, reps=reps, lit=lit, glow=glow)


def build(root, regions, stem_index, fills3):
    T, Lb, mid = volume(root, regions, stem_index)
    l1, l2 = shells(T)
    ii, jj, kk = np.nonzero(T)
    i0, k0, jc = ii.min(), kk.min(), (jj.min() + jj.max()) // 2
    W = lambda i, j, k: (int(CX + j - jc), int(BASE_Y + k - k0), int(FRONT_Z + i - i0))   # -> (x, y, z)
    N = len(regions)
    left = np.zeros(T.shape, bool)
    left[:mid] = True
    plate_k = [k for k in range(k0 + 1, T.shape[2]) if (BASE_Y + k - k0 - L1) % 4 == 0]

    # plate masks per region and level: inside the region, left hemisphere, behind the glass shell
    def pmask(r, k):
        a = (Lb[:, :, k] == r) & left[:, :, k] & ~l1[:, :, k]
        b = (Lb[:, :, k - 1] == r) & ~l1[:, :, k - 1]
        # no cell next to another region (or brainstem): keeps neighbouring regions' dust networks apart
        other = (Lb[:, :, k] >= 0) & (Lb[:, :, k] != r)
        near = ndimage.binary_dilation(other, structure=ndimage.generate_binary_structure(2, 1))
        return a & b & ~near

    # one ladder per region: among columns whose underside is close to the floor (short exposed ladder),
    # the one whose plates (4-connected pieces through it) cover the most cells
    proj = T.any(axis=2)
    low = np.where(proj, np.argmax(T, axis=2), T.shape[2])
    ladders, taken_x = {}, []
    for r in sorted(range(N), key=lambda r: -int(((Lb == r) & left).sum())):
        score = np.zeros(T.shape[:2])
        for k in plate_k:
            m = pmask(r, k)
            comp, n = ndimage.label(m)
            if n:
                sizes = np.concatenate([[0], ndimage.sum(m, comp, range(1, n + 1))])
                score += sizes[comp] * ndimage.binary_erosion(m)        # ladder needs dust on all four sides
        cand = sorted(zip(*np.nonzero(score)), key=lambda p: -score[p])
        best = score[cand[0]]
        short = [p for p in cand if low[p] - k0 <= MAX_EXPOSED and score[p] >= 0.5 * best]
        for i, j in short + cand:
            x = W(i, j, 0)[0]
            if all(abs(x - t) >= 3 for t in taken_x):
                ladders[r] = (int(i), int(j))
                taken_x.append(x)
                break
    assert len(ladders) == N, "no ladder site for some region"
    sq = lambda li, lj: {(li + a, lj + b) for a in (-1, 0, 1) for b in (-1, 0, 1)}
    lad_cells = {r: sq(*ladders[r]) for r in ladders}

    # hidden feeds: a region whose ladder would stand exposed below the brain instead rises in a short
    # column and crosses to its ladder inside the brain on a dust line (on glass) at plate level kt
    interior = T & ~l1 & ~l2
    risers, lines, kmin = {}, {}, {}
    band_all = {}
    for k in plate_k:
        band_all[k] = np.zeros(T.shape[:2], bool)
        for o in range(N):
            m = pmask(o, k)
            band_all[k] |= m & (ndimage.distance_transform_cdt(np.pad(m, 1), metric="taxicab")[1:-1, 1:-1] <= BAND)
    band_cnt = {k: np.cumsum([band_all[q] for q in plate_k if q <= k], axis=0)[-1] for k in plate_k}   # per column, levels <= k
    hits = lambda p, kt: int(band_cnt[kt][max(p[0] - 1, 0):p[0] + 2, max(p[1] - 1, 0):p[1] + 2].sum())
    for r, (li, lj) in ladders.items():
        if low[li, lj] - k0 <= MAX_EXPOSED:
            continue
        for kt in [k for k in plate_k if k >= low[li, lj] + 2]:
            reserved = set().union(*lad_cells.values(), *[sq(*q) for q in risers.values()],
                                   *[{(a + da, b + db) for a, b in L for da, db in NB4 + [(0, 0)]} for L, k in lines.values() if k == kt])
            free = ndimage.binary_erosion(interior[:, :, kt] & interior[:, :, kt - 1])
            ok = lambda q: 0 <= q[0] < free.shape[0] and 0 <= q[1] < free.shape[1] and free[q] and \
                (q not in reserved or q in lad_cells[r])
            # cheapest path: crossing a plate band cuts that plate, so band cells cost far more than gaps
            band_k = band_all[kt]
            # states are (cell, heading): turns cost extra so the line has straight runs for its repeaters
            dist_s, prev_s, hq = {}, {}, []
            for a, b in NB4:
                q = (li + a, lj + b)
                if ok(q):
                    st = (q, (-a, -b))
                    dist_s[st], prev_s[st] = 0, None
                    heapq.heappush(hq, (0, st))
            while hq:
                d, st = heapq.heappop(hq)
                if d > dist_s[st]:
                    continue
                q, h = st
                for a, b in NB4:
                    n = (q[0] + a, q[1] + b)
                    if ok(n) and n != (li, lj) and (a, b) != h:
                        turn = 0 if (-a, -b) == h else (10 ** 6 if prev_s[st] is None else 3)   # ends stay straight
                        nd = d + (BAND_COST if band_k[n] else 1) + turn
                        ns = (n, (-a, -b))
                        if nd < dist_s.get(ns, 1e9):
                            dist_s[ns], prev_s[ns] = nd, st
                            heapq.heappush(hq, (nd, ns))
            dist, prev = {}, {}
            for (q, h), d in dist_s.items():
                # the riser must sit straight behind the line's first cell (that cell holds a repeater)
                straight_in = prev_s[(q, h)] is not None and prev_s[(q, h)][1] == h
                if straight_in and d < dist.get(q, 1e9):
                    dist[q], prev[q] = d, (q, h)
            best = None
            for p, d in dist.items():
                if d < 2 or low[p] - k0 > RISER_EXPOSED or sq(*p) & (reserved - lad_cells[r]):
                    continue
                x = W(p[0], p[1], 0)[0]
                c = d + BAND_COST * hits(p, kt)          # a riser through another plate band cuts it too
                if all(abs(x - t) >= 3 for t in taken_x if t != W(li, lj, 0)[0]) and (best is None or c < best[0]):
                    best = (c, p)
            if best:
                p = best[1]
                path, st = [], prev_s[prev[p]]
                while st:
                    path.append(st[0])
                    st = prev_s[st]
                tot = sum(int(pmask(r, k).sum()) for k in plate_k)
                lost = sum(int(pmask(r, k).sum()) for k in plate_k if k < kt)
                if lost > MAX_LOSS * tot:          # too much of the region sits below the crossing: keep the stilt
                    break
                risers[r], lines[r], kmin[r] = p, (path, kt), kt      # path runs riser -> ladder
                taken_x.remove(W(li, lj, 0)[0])                        # the axon now arrives at the riser
                taken_x.append(W(p[0], p[1], 0)[0])
                break
    line_cells = {}
    for r, (L, kt) in lines.items():
        for a, b in L:
            for da, db in NB4 + [(0, 0)]:
                line_cells.setdefault(kt, set()).add((a + da, b + db))

    blocks = {}            # (x, y, z) -> block
    for i, j, k in zip(ii, jj, kk):
        r = Lb[i, j, k]
        col = "gray" if r == stem_index else regions[r][1]
        if l1[i, j, k]:
            blocks[W(i, j, k)] = f"{col}_stained_glass"
        elif l2[i, j, k]:
            blocks[W(i, j, k)] = "black_concrete" if r != stem_index else "gray_concrete"   # dark backing: lit rows pop

    plates, lit3, probe = {}, {r: [] for r in range(N)}, {}
    top_k = {}
    for r, (li, lj) in ladders.items():
        foreign0 = set().union(*[lad_cells[o] for o in ladders if o != r])
        for k in plate_k:
            if k < kmin.get(r, 0):
                continue
            foreign = foreign0.union(*[sq(*q) for o, q in risers.items() if k <= kmin[o]])
            m = pmask(r, k)
            # keep only a band behind the surface (interior lamps are invisible but cost light updates),
            # joined to the ladder by four straight spokes
            band = m & (ndimage.distance_transform_cdt(np.pad(m, 1), metric="taxicab")[1:-1, 1:-1] <= BAND)
            for da, db in NB4:
                a_, b_ = li, lj
                while 0 <= a_ < m.shape[0] and 0 <= b_ < m.shape[1] and m[a_, b_]:
                    band[a_, b_] = True
                    a_, b_ = a_ + da, b_ + db
            cells = {(int(a), int(b)) for a, b in zip(*np.nonzero(band))} - foreign - line_cells.get(k, set())
            if (li, lj) not in cells or not all((li + a, lj + b) in cells for a, b in NB4):
                continue
            d = design_plate(cells, (li, lj))
            if len(d["lit"]) < 4:
                continue
            plates[(r, k)] = d
            top_k[r] = k
            for a, b in d["lamps"]:
                blocks[W(a, b, k - 1)] = "redstone_lamp"
            for a, b in d["mesh"]:
                blocks[W(a, b, k)] = "redstone_wire" if (a, b) in d["dust"] else blocks.get(W(a, b, k), "air")
            for (a, b), fl in d["reps"].items():
                blocks[W(a, b, k)] = ("repeater", fl)
            lit3[r] += [W(a, b, k - 1) for a, b in d["glow"]]
    # surface stripes: a lamp under dust is strongly powered and lights the lamps next to it, so shell
    # voxels touching a plate lamp become lamps (only when every plate lamp they touch is their own region's)
    owner = {}
    for (r, k), d in plates.items():
        for a, b in d["lit"]:                 # only lamps that actually carry powered dust
            owner[(a, b, k - 1)] = r
    touch = {}
    for (a, b, k), r in owner.items():
        for da, db, dk in [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, -1)]:
            n = (a + da, b + db, k + dk)
            if 0 <= n[0] < T.shape[0] and 0 <= n[1] < T.shape[1] and 0 <= n[2] < T.shape[2] and l1[n]:
                touch.setdefault(n, set()).add(r)
    near_ladder = set().union(*lad_cells.values(), *[sq(*q) for q in risers.values()])
    stripes = {n: rs.pop() for n, rs in touch.items()
               if len(rs) == 1 and Lb[n] in rs and (n[0], n[1]) not in near_ladder}
    for n, r in stripes.items():
        blocks[W(*n)] = "redstone_lamp"
        lit3[r].append(W(*n))
    # ladders: block, torch, block, ... from the tract level up to the region's top plate
    for r, (li, lj) in ladders.items():
        x, _, z = W(li, lj, 0)
        ytop = W(li, lj, top_k[r])[1]
        ybot = L1
        if r in risers:
            L, kt = lines[r]
            ybot = W(0, 0, kt)[1]
            rx, _, rz = W(*risers[r], 0)
            for y in range(L1, ybot + 1):
                blocks[(rx, y, rz)] = "redstone_torch" if (y - L1) % 2 else "smooth_stone"
            # dust on glass; repeaters at both ends (out of the riser, into the ladder) and every 14 dust
            seq = [risers[r]] + L + [(li, lj)]
            run = 0
            for n in range(1, len(seq) - 1):
                (pa, pb), (a, b), (na, nb) = seq[n - 1], seq[n], seq[n + 1]
                straight = (a - pa, b - pb) == (na - a, nb - b)
                blocks[W(a, b, kt - 1)] = "glass"
                if n in (1, len(seq) - 2) or (run >= 9 and straight):
                    blocks[W(a, b, kt)] = ("repeater", (a - pa, b - pb), 1)
                    run = 0
                else:
                    blocks[W(a, b, kt)] = "redstone_wire"
                    run += 1
                    assert run <= 14, "hidden feed line too long without a straight cell for a repeater"
        for y in range(ybot, ytop + 1):
            blocks[(x, y, z)] = "redstone_torch" if (y - L1) % 2 else "smooth_stone"
        for a, b in NB4:
            if (li + a, lj + b) in plates[(r, top_k[r])]["dust"]:
                probe[r] = W(li + a, lj + b, top_k[r])
                break
    # cradle: a dark stand under the brain, inset from the silhouette, that also encases every ladder below it
    stand = np.zeros(proj.shape, bool)
    for r, (li, lj) in ladders.items():
        li, lj = risers.get(r, (li, lj))
        stand[max(li - 1, 0):li + 2, max(lj - 1, 0):lj + 2] = True
    for i, j in zip(*np.nonzero(stand)):
        for k in range(k0, min(low[i, j], T.shape[2])):
            p = W(i, j, k)
            if p not in blocks:
                blocks[p] = "polished_blackstone"
    # light seal: every unused cell inside the brain becomes tinted glass (blocks light, conducts nothing),
    # so a switching lamp relights only its own few cells instead of the hollow interior
    if SEAL:
        for i, j, k in zip(ii, jj, kk):
            blocks.setdefault(W(i, j, k), "tinted_glass")
    # emit: everything is set from the bottom up so torches always have support
    FACE = {(0, 1): "north", (0, -1): "south", (1, 0): "west", (-1, 0): "east"}
    out = []
    by = {}
    for p, blk in blocks.items():
        if isinstance(blk, tuple):
            continue
        by.setdefault(blk, []).append(p)
    order = [b for b in by if "glass" in b or "concrete" in b or b == "polished_blackstone"] + ["redstone_lamp", "smooth_stone", "redstone_torch", "redstone_wire"]
    for blk in order:
        out += fills3(by.get(blk, []), blk)
    for p, blk in blocks.items():
        if isinstance(blk, tuple):
            # plate axes: plate cell (a, b) = (i, j) -> world (z, x); flow along +a is +z, along +b is +x
            a, b = blk[1]
            flow = (b, a)            # world (dx, dz)
            out.append(f"setblock {p[0]} {p[1]} {p[2]} repeater[facing={FACE[flow]},delay={blk[2] if len(blk) > 2 else RING_DELAY}]")
    base = {r: W(*risers.get(r, q), 0)[0::2] for r, q in ladders.items()}            # (x, z) where each axon arrives
    xs = [x for x, y, z in blocks]; zs = [z for x, y, z in blocks]; ys = [y for x, y, z in blocks]
    # ambient: invisible light blocks in the air shell 2 blocks outside the surface, every 5th cell
    halo = ndimage.binary_dilation(T, iterations=2) & ~ndimage.binary_dilation(T, iterations=1)
    hi, hj, hk = np.nonzero(halo)
    sel = ((hi + hj + hk) % 5 == 0)
    ladder_cols = {W(li, lj, 0)[0::2] for li, lj in list(ladders.values()) + list(risers.values())}
    halo_pts = [W(a, b, c) for a, b, c in zip(hi[sel], hj[sel], hk[sel])
                if W(a, b, c)[1] > -56 and W(a, b, c) not in blocks and W(a, b, c)[0::2] not in ladder_cols]
    out += fills3(halo_pts, "light[level=8]")
    exposed = {regions[r][0]: int(low[risers.get(r, q)] - k0) for r, q in ladders.items()}
    stats_lines = {regions[r][0]: (len(L), int(BASE_Y + kt - k0), W(*risers[r], kt), [W(*q, kt) for q in L], W(*ladders[r], kt)) for r, (L, kt) in lines.items()}
    stats = dict(exposed=exposed, lines=stats_lines, voxels=int(T.sum()), plates=len(plates), stripes=len(stripes), dust=sum(len(d["dust"]) for d in plates.values()),
                 lit=sum(len(v) for v in lit3.values()), bbox=(min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))
    return dict(cmds=out, base=base, probe=probe, lit=lit3, stats=stats,
                footprint={(x, z) for x, y, z in blocks if y <= BASE_Y + 2})
