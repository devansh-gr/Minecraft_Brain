"""Single MAC cell in the simulator: 16 cases of (a, w, x, c) -> s, cout; plus a net lint."""
import itertools, sys
from rsim import Sim
from mac import cell
from cells import Y

def world(L, ox=0, oz=0):
    return {(x + ox, Y[l], z + oz): b for (x, l, z), b in L.B.items()}

def lint(L, S):
    comp = {}; bad = set()
    seen = set()
    for w in S.wires:
        if w in seen: continue
        st = [w]; grp = []; seen.add(w)
        while st:
            u = st.pop(); grp.append(u)
            for v in S.adj[u]:
                if v not in seen: seen.add(v); st.append(v)
        nets = {L.net.get((x, l, z)) for (x, y, z) in grp for l in [k for k, v in Y.items() if v == y]} - {None}
        if len(nets) > 1: bad.add(tuple(sorted(nets)))
    return bad

L = cell()
S0 = Sim(world(L)); bad = lint(L, S0)
print("lint merged nets:", bad or "none")
ok = 0
for a, w, x, c in itertools.product([0, 1], repeat=4):
    S = Sim(world(L))
    def src(px, l, pz):
        if l == 2: S.set((px, Y[1], pz), "glass")
        S.set((px, Y[l], pz), "redstone_block")
    if a: src(1, 0, -2)
    if w: src(11, 0, -2)
    if not x: src(13, 2, 0)
    if c: src(13, 2, 4)
    t = S.settle()
    s = int(S.power((29, Y[0], 31)) > 0); co = int(S.power((-15, Y[2], 4)) > 0)
    b = w & x; want = ((a + b + c) & 1, (a + b + c) >> 1)
    ok += (s, co) == want
    if (s, co) != want: print("a w x c", a, w, x, c, "-> s", s, "cout", co, "want", want, "ticks", t)
print(f"{ok}/16 cell cases, blocks {len(L.B)}")
raise SystemExit(ok != 16 or bool(bad))
