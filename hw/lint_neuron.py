"""Neuron layout lint: dust groups that join different nets (allowed: glass-climb ORs sat -> q0..q3)."""
from rsim import Sim
from neuron import neuron
from mac import system
Y = {l: -60 + l for l in range(6)}
inv = {v: k for k, v in Y.items()}
OK = [{"sat", "q%d" % i} for i in range(4)]
def merges(L):
  S = Sim({(x, Y[l], z): b for (x, l, z), b in L.B.items()}); seen = set(); bad = {}
  for w in S.wires:
    if w in seen: continue
    st = [w]; grp = []; seen.add(w)
    while st:
        u = st.pop(); grp.append(u)
        for v in S.adj[u]:
            if v not in seen: seen.add(v); st.append(v)
    nets = {L.net.get((x, inv[y], z)) for (x, y, z) in grp} - {None}
    if len(nets) > 1 and not nets <= {"sat", "q0", "q1", "q2", "q3"} and nets != {"rst", "sel0"}: bad[tuple(sorted(nets))[:6]] = [(x, inv[y], z) for (x, y, z) in grp if L.net.get((x, inv[y], z))][:2]
  return bad
L, P = neuron(); base = merges(system(True)[0])
bad = {k: v for k, v in merges(L).items() if k not in base}
print(len(L.B), "blocks; merged:", len(bad))
for k, v in list(bad.items())[:15]: print(k, v)
raise SystemExit(bool(bad))
