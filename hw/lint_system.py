from rsim import Sim
from mac import system
Y = {l: -60 + l for l in range(6)}
L, P = system(); S = Sim({(x, Y[l], z): b for (x, l, z), b in L.B.items()})
inv = {v: k for k, v in Y.items()}
seen = set(); bad = {}
for w in S.wires:
    if w in seen: continue
    st = [w]; grp = []; seen.add(w)
    while st:
        u = st.pop(); grp.append(u)
        for v in S.adj[u]:
            if v not in seen: seen.add(v); st.append(v)
    nets = {L.net.get((x, inv[y], z)) for (x, y, z) in grp} - {None}
    if len(nets) > 1: bad[tuple(sorted(nets))] = [(x, inv[y], z) for (x, y, z) in grp if L.net.get((x, inv[y], z))][:3]
print(len(L.B), "blocks; merged:", bad or "none")
