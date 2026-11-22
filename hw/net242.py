"""2-4-2 network as a NOR netlist, same equations as the 8-16-8 (reference.py), checked in Python."""
import random, sys
sys.path.insert(0, "..")
from nor import Net, simulate
from arith import *

N, J, STEPS, WB, BB = 2, 4, 4, 5, 6       # weights 5-bit signed, biases 6-bit signed


def build():
    net = Net()
    X = [[f"x{i}_{b}" for b in range(4)] for i in range(N)]
    W = [[[f"W{i}_{j}_{b}" for b in range(WB)] for j in range(J)] for i in range(N)]
    V = [[[f"V{j}_{k}_{b}" for b in range(WB)] for k in range(N)] for j in range(J)]
    Bj = [[f"b{j}_{b}" for b in range(BB)] for j in range(J)]
    Ck = [[f"c{k}_{b}" for b in range(BB)] for k in range(N)]
    keep = [f"alive{k}" for k in range(N)]          # region lesion lever OFF = alive (1)
    synk = [f"syn{k}" for k in range(N)]            # synaptic lesion lever OFF = connected (1)
    inputs = [s for L in (X, Bj, Ck) for v in L for s in v] + [s for M in (W, V) for r in M for v in r for s in v] + keep + synk
    A = []
    for j in range(J):
        s = Bj[j]
        for i in range(N):
            s = add(net, s, mul_us(net, X[i], W[i][j], 10), 11)
        A.append(s[2:])                               # floor(s / 4)
    u = [["0"] * 4 for _ in range(J)]
    for _ in range(STEPS):
        tot = ["0"] * 6
        for j in range(J):
            tot = add(net, tot, unsigned(u[j]), 6)
        I = tot[4:6] + ["0"]                           # floor(sum / 16), 0..3
        new = []
        for j in range(J):
            d = clamp15(net, sub(net, A[j], I, 10))
            s = add(net, unsigned(d), unsigned(u[j]), 5, "1")
            nu = s[1:5]                                # floor((d + u + 1) / 2)
            new.append(gate(net, nu, keep[j]) if j < N else nu)
        u = new
    o = []
    for k in range(N):
        s = Ck[k]
        for j in range(J):
            p = mul_us(net, u[j], V[j][k], 10)
            if j == k:
                p = gate(net, p, synk[k])
            s = add(net, s, p, 12)
        o.append(gate(net, clamp15(net, s[2:]), keep[k]))
    return net, inputs, dict(X=X, W=W, V=V, B=Bj, C=Ck, keep=keep, syn=synk, h=u, o=o)


def bits(v, n):
    return [(v >> b) & 1 for b in range(n)]


def val(sig, v, signed=False):
    r = sum(v[s] << b for b, s in enumerate(sig))
    return r - (1 << len(sig)) if signed and v[sig[-1]] else r


def ref(x, W, b, V, c, rl=(), sl=()):
    u = [0] * J
    for _ in range(STEPS):
        I = sum(u) // 16
        new = []
        for j in range(J):
            d = max(0, min(15, (sum(W[i][j] * x[i] for i in range(N)) + b[j]) // 4 - I))
            new.append(u[j] + (d - u[j] + 1) // 2)
        u = new
        for k in rl:
            u[k] = 0
    o = [0 if k in rl else max(0, min(15, (c[k] + sum(V[j][k] * u[j] for j in range(J) if not (j == k and k in sl))) // 4)) for k in range(N)]
    return u, o


def assign(io, x, W, b, V, c, rl, sl):
    a = {}
    for i in range(N):
        a.update(zip(io["X"][i], bits(x[i], 4)))
        for j in range(J):
            a.update(zip(io["W"][i][j], bits(W[i][j] & 31, WB)))
    for j in range(J):
        a.update(zip(io["B"][j], bits(b[j] & 63, BB)))
        for k in range(N):
            a.update(zip(io["V"][j][k], bits(V[j][k] & 31, WB)))
    for k in range(N):
        a.update(zip(io["C"][k], bits(c[k] & 63, BB)))
        a[io["keep"][k]] = 0 if k in rl else 1
        a[io["syn"][k]] = 0 if k in sl else 1
    return a


def rand_case(r):
    x = [r.randint(0, 15) for _ in range(N)]
    W = [[r.randint(-16, 15) for _ in range(J)] for _ in range(N)]
    V = [[r.randint(-16, 15) for _ in range(N)] for _ in range(J)]
    b = [r.randint(-32, 31) for _ in range(J)]
    c = [r.randint(-32, 31) for _ in range(N)]
    rl = [k for k in range(N) if r.random() < 0.15]
    sl = [k for k in range(N) if r.random() < 0.15]
    return x, W, b, V, c, rl, sl


if __name__ == "__main__":
    net, inputs, io = build()
    print(f"gates {len(net.gates)}, inputs {len(inputs)}")
    r = random.Random(1); bad = 0
    for t in range(3000):
        case = rand_case(r)
        v = simulate(net.gates, assign(io, *case))
        h = [val(s, v) for s in io["h"]]; o = [val(s, v) for s in io["o"]]
        rh, ro = ref(*case)
        if (h, o) != (rh, ro):
            bad += 1
            if bad < 4: print("MISMATCH", case, h, o, rh, ro)
    print("python NOR-sim vs reference: %d/3000 mismatches" % bad)
