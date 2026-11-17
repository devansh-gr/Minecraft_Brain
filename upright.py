"""Upright volumetric brain (both hemispheres, cerebellum, brainstem) from the MNI152 tissue templates and the
Harvard-Oxford atlas, with region lighting driven by the existing redstone axons.

Orientation: MNI x (left->right) -> world z (left hemisphere faces the entrance, north);
MNI y (posterior->anterior) -> world x (frontal lobe east); MNI z (inferior->superior) -> world y.

Lighting: each region gets one vertical torch ladder rising from its axon. Ladder blocks every 4 levels are
powered exactly while the axon is; at those levels a horizontal plate of dust on lamps fills the region's
cross-section just behind the glass shell, with repeater rings for reach. Decorative voxels are unpowered.
"""
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
RING = 9                    # dust cells between repeater rings on a plate
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
    """Flat dust plate: Euclidean repeater rings around the ladder; returns dust, reps, lit (all (a, b) cells)."""
    mesh = set(cells) - {feed}
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
    return dict(mesh=mesh, dust=dust, reps=reps, lit={q for q in dust if power.get(q, 0) > 0})


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

    # one ladder per region: the column whose plates (4-connected pieces through it) cover the most cells
    ladders, taken_x = {}, []
    for r in sorted(range(N), key=lambda r: -int(((Lb == r) & left).sum())):
        score = np.zeros(T.shape[:2])
        for k in plate_k:
            m = pmask(r, k)
            comp, n = ndimage.label(m)
            if n:
                sizes = np.concatenate([[0], ndimage.sum(m, comp, range(1, n + 1))])
                score += sizes[comp] * ndimage.binary_erosion(m)        # ladder needs dust on all four sides
        for i, j in sorted(zip(*np.nonzero(score)), key=lambda p: -score[p]):
            x = W(i, j, 0)[0]
            if all(abs(x - t) >= 3 for t in taken_x):
                ladders[r] = (int(i), int(j))
                taken_x.append(x)
                break
    assert len(ladders) == N, "no ladder site for some region"
    lad_cells = {r: {(li + a, lj + b) for a in (-1, 0, 1) for b in (-1, 0, 1)} for r, (li, lj) in ladders.items()}

    blocks = {}            # (x, y, z) -> block
    for i, j, k in zip(ii, jj, kk):
        r = Lb[i, j, k]
        col = "gray" if r == stem_index else regions[r][1]
        if l1[i, j, k]:
            blocks[W(i, j, k)] = f"{col}_stained_glass"
        elif l2[i, j, k]:
            blocks[W(i, j, k)] = f"{col}_concrete" if r != stem_index else "gray_concrete"

    plates, lit3, probe = {}, {r: [] for r in range(N)}, {}
    top_k = {}
    for r, (li, lj) in ladders.items():
        foreign = set().union(*[lad_cells[o] for o in ladders if o != r])
        for k in plate_k:
            m = pmask(r, k)
            cells = {(int(a), int(b)) for a, b in zip(*np.nonzero(m))} - foreign
            if (li, lj) not in cells or not all((li + a, lj + b) in cells for a, b in NB4):
                continue
            d = design_plate(cells, (li, lj))
            if len(d["lit"]) < 4:
                continue
            plates[(r, k)] = d
            top_k[r] = k
            for a, b in d["mesh"]:
                blocks[W(a, b, k - 1)] = "redstone_lamp"
                blocks[W(a, b, k)] = "redstone_wire" if (a, b) in d["dust"] else blocks.get(W(a, b, k), "air")
            for (a, b), fl in d["reps"].items():
                blocks[W(a, b, k)] = ("repeater", fl)
            lit3[r] += [W(a, b, k - 1) for a, b in d["lit"]]
    # ladders: block, torch, block, ... from the tract level up to the region's top plate
    for r, (li, lj) in ladders.items():
        x, _, z = W(li, lj, 0)
        ytop = W(li, lj, top_k[r])[1]
        for y in range(L1, ytop + 1):
            blocks[(x, y, z)] = "redstone_torch" if (y - L1) % 2 else "smooth_stone"
        for a, b in NB4:
            if (li + a, lj + b) in plates[(r, top_k[r])]["dust"]:
                probe[r] = W(li + a, lj + b, top_k[r])
                break
    # emit: everything is set from the bottom up so torches always have support
    FACE = {(0, 1): "north", (0, -1): "south", (1, 0): "west", (-1, 0): "east"}
    out = []
    by = {}
    for p, blk in blocks.items():
        if isinstance(blk, tuple):
            continue
        by.setdefault(blk, []).append(p)
    order = [b for b in by if "glass" in b or "concrete" in b] + ["redstone_lamp", "smooth_stone", "redstone_torch", "redstone_wire"]
    for blk in order:
        out += fills3(by.get(blk, []), blk)
    for p, blk in blocks.items():
        if isinstance(blk, tuple):
            # plate axes: plate cell (a, b) = (i, j) -> world (z, x); flow along +a is +z, along +b is +x
            a, b = blk[1]
            flow = (b, a)            # world (dx, dz)
            out.append(f"setblock {p[0]} {p[1]} {p[2]} repeater[facing={FACE[flow]},delay=2]")
    base = {r: W(li, lj, 0)[0::2] for r, (li, lj) in ladders.items()}            # (x, z) of each ladder
    xs = [x for x, y, z in blocks]; zs = [z for x, y, z in blocks]; ys = [y for x, y, z in blocks]
    stats = dict(voxels=int(T.sum()), plates=len(plates), dust=sum(len(d["dust"]) for d in plates.values()),
                 lit=sum(len(v) for v in lit3.values()), bbox=(min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))
    return dict(cmds=out, base=base, probe=probe, lit=lit3, stats=stats,
                footprint={(x, z) for x, y, z in blocks if y <= BASE_Y + 2})
