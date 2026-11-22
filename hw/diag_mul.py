import sys, time
from rs import *
from nor import Net, compile2, simulate
from arith import mul_us
import nor
net = Net(); X = [f"x{b}" for b in range(4)]; Wb = [f"w{b}" for b in range(5)]
P = mul_us(net, X, Wb, 9)
B, src, probe = compile2(net.gates, X + Wb, set(P)); level = compile2.level
x, w = int(sys.argv[1]), int(sys.argv[2])
inp = {**{X[b]: (x >> b) & 1 for b in range(4)}, **{Wb[b]: ((w & 31) >> b) & 1 for b in range(5)}}
for k, v in inp.items(): cmd("setblock %d %d %d %s" % (*src[k], "redstone_block" if v else "stone"))
time.sleep(int(sys.argv[3]))
v = simulate(net.gates, inp)
bad = []
for name, ins in net.gates:
    got = power(*probe[name]) > 0
    if got != bool(v[name]):
        bad.append((level[name], name, ins, int(got), v[name], probe[name], [(i, v[i], probe.get(i) or src.get(i)) for i in ins]))
bad.sort()
print(len(bad), "wrong gates of", len(net.gates))
for b in bad[:5]: print(b)
