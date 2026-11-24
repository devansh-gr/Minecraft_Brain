"""Build the physical neuron into the brain world (server/ BrainUpright, RCON 25599) at (1000, 1300), the same spot
as on the HW server, then check it in place. There it is the brain's math detector (hidden unit P:Parietal):
x0 = parietal input, w0 = 4, everything else 0. Usage: RCON_PORT=25599 python3 build_in_brain.py [--build]"""
import os, sys, time
os.environ.setdefault("RCON_PORT", "25599")
import macio
import test_neuron_game as g
from neuron import ref

if "--build" in sys.argv:
    t = time.time(); n, wx, wz = macio.build(g.L, g.X0, g.Z0)
    print(f"built {n} blocks, footprint {wx} x {wz}, {time.time() - t:.0f} s", flush=True); time.sleep(10)
ok = 0
cases = [(9, 0, 4, 0, 0), (0, 0, 4, 0, 0), (15, 0, 4, 0, 0), (5, 3, 4, -2, 3), (5, 3, 8, -2, 3)]
for c in cases:
    g.load(c); st = g.stored(); tr, p99 = g.infer(); got = g.y(); want = ref(*c); good = got == want and st == c; ok += good
    print(f"case {c} stored {'ok' if st == c else st} y={got} want {want} {'OK' if good else 'WRONG'} run {tr:.0f} s P99 {p99} ms", flush=True)
print(f"{ok}/{len(cases)}"); raise SystemExit(ok != len(cases))
