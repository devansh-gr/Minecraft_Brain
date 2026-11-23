"""In-game MAC robustness + wall-clock cycle sweep. Exit 1 on any wrong result."""
import random, sys, time
from mac import expected
import macio as m
from rs import cmd
fails = 0
def check(name, got, want):
    global fails; ok = got == want; fails += not ok
    print(f"{name:44s} A={got:6d} want {want:6d} {'OK' if ok else 'WRONG'}", flush=True)
corners = [m.at(p) for p in [(-351, 0, -31), (120, 0, -31), (-351, 0, 200), (120, 0, 200)]]
print("forceload corners:", [("marked" in cmd(f"forceload query {x} {z}")) for x, _, z in corners])
m.setin(0, 0); m.reset(); acc = 0; check("physical reset", m.A(), 0)
m.setin(9, -7); time.sleep(20); m.go(); time.sleep(20); acc = expected(acc, 9, -7); check("one op", m.A(), acc)
for x, w in [(15, 15), (3, -16), (12, 5)]:                       # inputs change, no clock
    m.setin(x, w); time.sleep(20)
check("3 input changes, no GO (state retained)", m.A(), acc)
m.setin(5, 3); time.sleep(20)
for _ in range(3): m.go(); time.sleep(20); acc = expected(acc, 5, 3)
check("3 GO pulses, same inputs (3 MACs)", m.A(), acc)
m.setin(15, -16); time.sleep(3); m.src(m.P["rst"], 1); time.sleep(1); m.go(); time.sleep(20); m.src(m.P["rst"], 0); acc = 0
check("reset asserted mid-computation", m.A(), acc)
time.sleep(30); check("retained after 30 s idle", m.A(), acc)
# wall-clock cycle sweep: per op = setin, wait D, GO (1 s hold), next op. Read A only at the end of each batch.
r = random.Random(11)
for D in [int(a) for a in (sys.argv[1:] or ["14", "10", "7", "5"])]:
    m.reset(); acc = 0; ops = [(r.randrange(16), r.randrange(-16, 16)) for _ in range(6)]
    t0 = time.time(); p99 = []
    for x, w in ops:
        m.setin(x, w); time.sleep(D); m.go(); acc = expected(acc, x, w); p99.append(m.tickstats())
    time.sleep(D); per = (time.time() - t0) / len(ops)
    got = m.A(); fails += got != acc
    print(f"cycle D={D:2d}s  wall {per:5.1f} s/op  A={got:6d} want {acc:6d} {'OK' if got == acc else 'WRONG'}  "
          f"MSPT P95 max {max(p[1] for p in p99):.1f} P99 max {max(p[2] for p in p99):.1f} ms", flush=True)
raise SystemExit(fails != 0)
