"""Tick-rate benchmark of the physical neuron (isolated HW server only). Every harness wait is in game ticks
(scaled by the requested rate); achieved TPS comes from /time query gametime over each run. Output is read only
after the strobe pulse is seen at the output-latch lock (an observed block state), never from a fixed delay.
Usage: python3 test_neuron_tps.py 20 30 40 60 80 100"""
import json, re, sys, time
import test_neuron_game as G
from rs import cmd
from neuron import ref
P = G.P
STB = (104, 0, -30)                                  # strobe repeater feeding the output LOCK comparator
CASES = [(15, 15, 15, 15, 31), (5, 3, 4, -2, 3), (5, 3, 8, -2, 3), (7, 3, -16, 5, 0)]   # high, w0=4, w0=8, low
RUN_GT = 2870                                        # START -> RUN clear at 20 TPS (143.3 s), game ticks


def gt(): return int(re.search(r"(\d+)", cmd("time query gametime")).group(1))
def wait_gt(n):
    """Sleep until n game ticks have passed (works at any achieved rate)."""
    t = gt() + n
    while gt() < t: time.sleep(0.05)
def pct():
    t = cmd("tick query"); f = lambda k: float(re.search(k + r":\s*([\d.]+)ms", t).group(1))
    return f("P50"), f("P95"), f("P99")


def load(c):
    for n, v in G.bits(*c).items(): G.blk(P["reg"][n], v)
    wait_gt(6)
    for r in (1, 2, 3, 4): G.blk(P["we"][r], 1)
    wait_gt(50)                                      # WE held 25 rt (LOCK row needs ~10 rt across the crossbar)
    for r in (1, 2, 3, 4): G.blk(P["we"][r], 0)
    wait_gt(40)                                      # LOCK re-asserts before the pins clear
    for n in P["reg"]: G.blk(P["reg"][n], 0)
    wait_gt(10)


def infer():
    g0 = gt(); w0 = time.time()
    G.blk(P["start"], 1); wait_gt(20); G.blk(P["start"], 0)
    ms = []; seen_on = seen_off = False; g_clear = None
    while gt() - g0 < 2 * RUN_GT:
        if gt() - g0 < RUN_GT - 200:
            time.sleep(1.0); ms.append(pct()); continue
        s = G.rep_on(STB)                            # fast poll near the end: catch the strobe pulse itself
        seen_on |= s; seen_off |= seen_on and not s
        if g_clear is None and not G.rep_on(G.RUN): g_clear = gt(); w_clear = time.time()
        if g_clear is not None and seen_off: break
    w_done = time.time(); g_done = gt()
    return dict(run_gt=(g_clear or g_done) - g0, run_s=round((w_clear if g_clear else w_done) - w0, 1),
                done_s=round(w_done - w0, 1), tps=round((g_done - g0) / (w_done - w0), 1), strobe=seen_off,
                p50=max(m[0] for m in ms), p95=max(m[1] for m in ms), p99=max(m[2] for m in ms))


if __name__ == "__main__":
    rates = [int(a) for a in sys.argv[1:]] or [20, 30, 40, 60, 80, 100]
    out = []
    try:
        for N in rates:
            cmd(f"tick rate {N}"); wait_gt(40)
            for c in CASES:
                wl = time.time(); load(c); tl = time.time() - wl; st = G.stored()
                r = infer(); yv = G.y(); want = ref(*c)
                wait_gt(400)                         # delay line drains (> one 320-game-tick slot) before the next START
                r.update(rate=N, case=c, stored_ok=st == c, y=yv, want=want, A=G.acc(), C=G.carry(), load_s=round(tl, 1),
                         ok=st == c and yv == want and r["strobe"])
                out.append(r)
                print(f"rate {N:3d} achieved {r['tps']:5.1f} TPS  case {c} y={yv:2d} want {want:2d} A={r['A']:4d} C={r['C']} "
                      f"{'OK' if r['ok'] else 'WRONG'}  run {r['run_s']:5.1f}s ({r['run_gt']} gt) done {r['done_s']:5.1f}s "
                      f"load {r['load_s']}s  P50/95/99 {r['p50']}/{r['p95']}/{r['p99']} ms", flush=True)
                json.dump(out, open("../docs/hw_neuron_tps.json", "w"), indent=1)
    finally:
        cmd("tick rate 20"); print("tick rate restored to 20", flush=True)
    bad = [r for r in out if not r["ok"]]
    print(f"{len(out) - len(bad)}/{len(out)} correct"); raise SystemExit(bool(bad))
