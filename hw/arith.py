"""Two's-complement arithmetic on bit lists (LSB first) built from NOR gates."""


def ext(a, n):
    return a + [a[-1]] * (n - len(a)) if len(a) < n else a[:n]


def add(net, a, b, n, cin="0"):
    """n-bit signed sum of signed a and b (sign-extended)."""
    a, b, out, c = ext(a, n), ext(b, n), [], cin
    for i in range(n):
        s, c = net.fa(a[i], b[i], c)
        out.append(s)
    return out


def neg_bits(net, a):
    return [net.NOT(x) for x in a]


def sub(net, a, b, n):
    return add(net, a, neg_bits(net, ext(b, n)), n, "1")


def mul_us(net, x, w, n):
    """unsigned x (bits) times signed w (bits): n-bit signed product."""
    acc = ["0"] * n
    for k, xk in enumerate(x):
        row = ["0"] * k + [net.AND(xk, wb) for wb in ext(w, n - k)]
        acc = add(net, acc, row[:n], n)
    return acc


def clamp15(net, t):
    """signed t -> 4-bit clamp(t, 0, 15)."""
    neg = t[-1]
    big = net.OR(*t[4:-1]) if len(t) > 5 else "0"
    return [net.nor(net.nor(t[b], big), neg) for b in range(4)]


def gate(net, bits, on):
    """bits AND on."""
    return [net.AND(b, on) for b in bits]


def unsigned(a):
    return a + ["0"]
