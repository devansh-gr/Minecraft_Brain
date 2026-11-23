"""In-game physical neuron at (X0, Z0): build, load registers through WE, pulse START, wait for the physical
sequencer to finish (RUN latch falls), read the output latch. Commands only place pin blocks and read block states."""
import json, random, sys, time
import macio
from rs import cmd
from neuron import neuron, ref, OX, OZ
from mac import NB, PX
X0, Z0 = 1000, 1300
Y = {l: -60 + l for l in range(6)}
L, P = neuron()
at = lambda p: (p[0] + X0, Y[p[1]], p[2] + Z0)
def blk(p, on):
    x, y, z = at(p); cmd(f"setblock {x} {y} {z} {'redstone_block' if on else 'air'}")
def rep_on(p):
    x, y, z = at(p); return "passed" in cmd(f"execute if block {x} {y} {z} repeater[powered=true]")
def bits(x0, x1, w0, w1, b):
    d = {"X0_%d" % i: x0 >> i & 1 for i in range(4)}; d.update({"X1_%d" % i: x1 >> i & 1 for i in range(4)})
    d.update({"W0_%d" % i: (w0 & 31) >> i & 1 for i in range(5)}); d.update({"W1_%d" % i: (w1 & 31) >> i & 1 for i in range(5)})
    d.update({"B_%d" % i: (b & 63) >> i & 1 for i in range(6)}); return d
def load(c, rows=(1, 2, 3, 4)):
    t0 = time.time()
    for n, v in bits(*c).items(): blk(P["reg"][n], v)
    time.sleep(0.3)
    for r in rows: blk(P["we"][r], 1)
    time.sleep(2.5)
    for r in rows: blk(P["we"][r], 0)
    time.sleep(2.0)                                   # LOCK row re-asserts west to east, ~1 s across 9 tiles
    for n in P["reg"]: blk(P["reg"][n], 0)
    return time.time() - t0
def stored():
    """Register latch states (read only), as the values they hold."""
    v = {n: rep_on((p[0] - 1, 0, p[2])) for n, p in P["reg"].items()}
    g = lambda pre, k: sum(v["%s_%d" % (pre, i)] << i for i in range(k))
    s = lambda u, k: u - (1 << k) * (u >= 1 << (k - 1))
    return g("X0", 4), g("X1", 4), s(g("W0", 5), 5), s(g("W1", 5), 5), s(g("B", 6), 6)
def y(): return sum(rep_on(p) << i for i, p in enumerate(P["y"]))
def acc():
    v = sum(rep_on((1 - PX * j, 0, -7)) << j for j in range(NB)); return v - (1 << NB) * (v >= 1 << (NB - 1))
def carry(): return sum(rep_on((6 - PX * j, 0, -7)) << j for j in range(4, NB))
RUN = (OX, 0, OZ - 4)
CASES = [(15, 15, 15, 15, 31), (7, 3, -16, 5, 0), (0, 0, 0, 0, 0), (9, 12, 3, -2, -7), (5, 3, 4, -2, 3), (5, 3, 8, -2, 3),
         (15, 15, -16, -16, -32), (10, 6, 3, 2, -1), (1, 1, 1, 1, 2), (3, 0, 5, 0, -1)]
LAST = [0.0]
GAP = 20.0                                           # delay line drains behind RUN; next START needs > one slot (16 s)
def infer(timeout=200):
    time.sleep(max(0.0, LAST[0] + GAP - time.time()))
    blk(P["start"], 1); t0 = time.time(); time.sleep(1.0); blk(P["start"], 0)
    ms = []
    while time.time() - t0 < timeout:
        time.sleep(2); t = cmd("tick query")
        try: ms.append(float(t.split("P99:")[1].split("ms")[0]))
        except Exception: pass
        if not rep_on(RUN): break
    t_run = time.time() - t0; LAST[0] = time.time()
    time.sleep(3.0)                                  # output latch strobe lands ~0.6 s after RUN clears (measured)
    return t_run, max(ms) if ms else None
if __name__ == "__main__":
    if "--build" in sys.argv:
        n, wx, wz = macio.build(L, X0, Z0); print(f"built {n} blocks, footprint {wx} x {wz}", flush=True); time.sleep(10)
    r = random.Random(7)
    cases = list(CASES)
    cases += [(r.randrange(16), r.randrange(16), r.randrange(-16, 16), r.randrange(-16, 16), r.randrange(-32, 32)) for _ in range(int(sys.argv[-1]) if sys.argv[-1].isdigit() else 0)]
    ok = 0; log = []
    for c in cases:
        tl = load(c); st = stored(); tr, p99 = infer()
        got = y(); want = ref(*c); a = acc(); cc = carry(); s = c[0] * c[2] + c[1] * c[3] + c[4]
        good = got == want and st == c; ok += good
        log.append(dict(case=c, stored=st, sum=s, A=a, C=cc, y=got, want=want, load_s=round(tl, 1), run_s=round(tr, 1), p99=p99))
        print(f"x={c[:2]} w={c[2:4]} b={c[4]:3d} stored={'ok' if st == c else st} sum={s:5d} A={a:5d} C={cc} y={got:2d} want {want:2d} "
              f"{'OK' if good else 'WRONG'}  load {tl:.1f}s run(START->RUN clear) {tr:.1f}s P99 {p99}ms", flush=True)
    json.dump(log, open("../docs/hw_neuron_game.json", "w"), indent=1)
    print(f"{ok}/{len(cases)}"); raise SystemExit(ok != len(cases))
