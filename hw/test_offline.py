"""Server-free regression: compilers run and netlists simulate correctly. Exit 1 on any failure."""
import itertools
from nor import Net, compile, compile2, simulate
from cells import fa_cell, xor_cell
n = Net(); s, c = n.fa("a", "b", "cin")
B, src, probe = compile(n.gates, ["a", "b", "cin"])
assert B and set(src) == {"a", "b", "cin"} and s in probe and c in probe
B2, src2, probe2 = compile2(n.gates, ["a", "b", "cin"], [s, c])
assert B2 and s in compile2.level
for a, b, ci in itertools.product([0, 1], repeat=3):
    v = simulate(n.gates, {"a": a, "b": b, "cin": ci})
    assert (v[s], v[c]) == ((a + b + ci) & 1, (a + b + ci) >> 1), (a, b, ci)
assert len(xor_cell()[0]) == 48 and len(fa_cell()[0]) == 235
print("offline regression OK")
