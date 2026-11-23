"""Validate rsim against cells already verified in game (xor 4/4, fa 8/8, pre-fix fa 4/8 with s ignoring c)."""
import itertools
from rsim import Sim
from cells import xor_cell, fa_cell, at, Y

def run(B, feed, outs, n):
    W = at(B, 0, 0); res = []
    for bits in itertools.product([0, 1], repeat=n):
        S = Sim(W)
        for (k, (dx, l, dz)), v in zip(feed.items(), bits):
            if l == 2: S.set((dx, Y[1], dz), "glass")
            if v: S.set((dx, Y[l], dz), "redstone_block")
        t = S.settle()
        res.append((bits, tuple(int(S.power((o[0], Y[o[1]], o[2])) > 0) for o in outs), t))
    return res

B, f, o = xor_cell()
r = run(B, f, [o], 2); x_ok = sum(out[0] == (b[0] ^ b[1]) for b, out, _ in r)
B, f, o = fa_cell()
r = run(B, f, list(o.values()), 3)
fa_ok = sum(out == ((sum(b) & 1), sum(b) >> 1) for b, out, _ in r)
Bp = dict(B); del Bp[(7, 1, 7)]; del Bp[(7, 2, 7)]
rp = run(Bp, f, list(o.values()), 3)
pre = [out for _, out, _ in rp]; pre_ok = sum(out == ((sum(b) & 1), sum(b) >> 1) for b, out, _ in rp)
s_ignores_c = all(out[0] == (b[0] ^ b[1]) for b, out, _ in rp)
print(f"xor {x_ok}/4, fa {fa_ok}/8 (ticks max {max(t for *_, t in r)}), pre-fix fa {pre_ok}/8, s ignores c: {s_ignores_c}")
raise SystemExit(not (x_ok == 4 and fa_ok == 8 and pre_ok == 4 and s_ignores_c))
