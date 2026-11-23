"""Filmed demo: same inputs and bias, only the stored weight w0 changes (4 -> 8); the physical output goes 4 -> 9.
Logs wall-clock timestamps so replay footage can be matched to each step. Reads only observed block states."""
import time
import test_neuron_tps as T
from neuron import ref
G = T.G
log = open("../docs/hw_demo_weight_change.txt", "a")
def say(s):
    line = time.strftime("%H:%M:%S ") + s; print(line, flush=True); log.write(line + "\n"); log.flush()
say(f"tick rate {T.cmd('tick query').split('Target tick rate:')[1].split('per')[0].strip()} TPS")
for w0 in (4, 8):
    c = (5, 3, w0, -2, 3)
    say(f"load x0=5 x1=3 w0={w0} w1=-2 b=3"); T.load(c); say(f"stored (read from latches) {G.stored()}")
    say("START"); r = T.infer()
    say(f"strobe seen={r['strobe']} run {r['run_s']} s ({r['run_gt']} game ticks); output latch y={G.y()} (reference {ref(*c)}); A={G.acc()} C={G.carry()}")
    T.wait_gt(400)
