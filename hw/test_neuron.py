"""Neuron in the simulator: write registers through WE, pulse START, let the physical sequencer run, read the output latch.
y must equal clamp((w0*x0 + w1*x1 + b) // 4, 0, 15). Commands here only place pin blocks."""
import random, sys, time
from rsim import Sim
from neuron import neuron, ref
from mac import NB, PX
Y = {l: -60 + l for l in range(6)}
L, P = neuron()
S = Sim({(x, Y[l], z): b for (x, l, z), b in L.B.items()})
at = lambda p: (p[0], Y[p[1]], p[2])
def blk(p, on): S.set(at(p), "redstone_block" if on else "air")
def run(n):
    for _ in range(n): S.step()
def write(row, bits):
    """bits: {register name: 0/1}; WE pulse on crossbar row `row`."""
    for n, v in bits.items(): blk(P["reg"][n], v)
    run(4); blk(P["we"][row], 1); run(20); blk(P["we"][row], 0); run(16)
    for n in bits: blk(P["reg"][n], 0)
def load(x0, x1, w0, w1, b):
    write(1, {**{"X0_%d" % i: x0 >> i & 1 for i in range(4)}, **{"W0_%d" % i: (w0 & 31) >> i & 1 for i in range(5)}})
    write(2, {**{"X1_%d" % i: x1 >> i & 1 for i in range(4)}, **{"W1_%d" % i: (w1 & 31) >> i & 1 for i in range(5)}})
    write(3, {"B_%d" % i: (b & 63) >> i & 1 for i in range(1, 6)})
    write(4, {"B_0": b & 1})
def y(): return sum((S.out[at(p)] > 0) << i for i, p in enumerate(P["y"]))
def acc():
    v = sum(int(S.out[(1 - PX * j, Y[0], -7)] > 0) << j for j in range(NB)); return v - (1 << NB) * (v >= 1 << (NB - 1))
def carry(): return sum(int(S.out[(6 - PX * j, Y[0], -7)] > 0) << j for j in range(4, NB))
def infer(T=1500):
    blk(P["start"], 1); run(10); blk(P["start"], 0)
    gp = at(P["go"]); ev = []; last = 0
    for t in range(T):
        S.step(); g = S.out[gp] > 0
        if g and not last: ev.append(t)
        last = g
    return ev
if __name__ == "__main__":
    sys.argv = [a for a in sys.argv if a != "--game"] + (["--game"] if "--game" in sys.argv else [])
    r = random.Random(int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 1)
    cases = [(15, 15, 15, 15, 31), (7, 3, -16, 5, 0), (0, 0, 0, 0, 0), (9, 12, 3, -2, -7)]
    cases += [(r.randrange(16), r.randrange(16), r.randrange(-16, 16), r.randrange(-16, 16), r.randrange(-32, 32)) for _ in range(int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 0)]
    if "--game" in sys.argv:
        from test_neuron_game import CASES; cases = CASES
    ok = 0; log = []
    for c in cases:
        t0 = time.time(); load(*c); ev = infer()
        want = ref(*c); got = y(); s = c[0] * c[2] + c[1] * c[3] + c[4]
        ok += got == want; log.append(dict(case=c, A=acc(), C=carry(), y=got, want=want))
        print(f"x={c[:2]} w={c[2:4]} b={c[4]:3d}  sum={s:5d} A={acc():5d} C={carry()}  y={got:2d} want {want:2d} {'OK' if got == want else 'WRONG'}  GO rises {ev}  ({time.time()-t0:.0f}s)", flush=True)
    if "--game" in sys.argv:
        import json; json.dump(log, open("../docs/hw_neuron_sim.json", "w"), indent=1)
    print(f"{ok}/{len(cases)}"); raise SystemExit(ok != len(cases))
