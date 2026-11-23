"""In-game carry-save MAC: build, physical reset, cycle sweep with physical carry flush before each readout."""
import os, random, sys, time
os.environ["MAC_CSA"] = "1"
import macio as m
from mac import expected
if "--build" in sys.argv:
    n, wx, wz = m.build(); print(f"built {n} blocks, footprint {wx} x {wz}", flush=True); time.sleep(5)
fails = 0; r = random.Random(13)
for D in [int(a) for a in sys.argv[1:] if a.isdigit()] or [12, 9, 7, 5]:
    m.setin(0, 0); m.reset(); acc = 0
    ops = [(15, -16), (15, 15)] + [(r.randrange(16), r.randrange(-16, 16)) for _ in range(6)]
    t0 = time.time(); ts = []
    for x, w in ops:
        m.setin(x, w); time.sleep(D); m.go(); acc = expected(acc, x, w); ts.append(m.tickstats())
    per = (time.time() - t0) / len(ops)
    m.flush(); got = m.A(); c = m.C(); ok = got == acc and c == 0; fails += not ok
    print(f"cycle D={D:2d}s  wall {per:5.1f} s/op over {len(ops)} ops  A={got:6d} want {acc:6d} C={c} {'OK' if ok else 'WRONG'}  "
          f"MSPT P95 max {max(t[1] for t in ts):.1f} P99 max {max(t[2] for t in ts):.1f}", flush=True)
raise SystemExit(fails != 0)
