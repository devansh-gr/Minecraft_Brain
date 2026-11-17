"""Independent reference forward pass, written from the equations (docs/NOTEBOOK.md 11.2), not from dp/.

Used only to check numbers the game produced. Integer floor division matches Minecraft's scoreboard /= (floorDiv).
"""
N, J, STEPS, H_DIV, O_DIV = 8, 16, 4, 4, 4
clamp = lambda v, lo, hi: max(lo, min(hi, v))


def forward(x, W, b, V, c, region_lesion=(), syn_lesion=()):
    u = [0] * J
    for _ in range(STEPS):
        I = sum(u) // 16
        new = []
        for j in range(J):
            d = clamp((sum(W[i][j] * x[i] for i in range(N)) + b[j]) // H_DIV - I, 0, 15)
            new.append(u[j] + (d - u[j] + 1) // 2)
        u = new
        for k in region_lesion:
            u[k] = 0
    h = u
    o = []
    for k in range(N):
        s = c[k] + sum(V[j][k] * h[j] for j in range(J) if not (j == k and k in syn_lesion))
        o.append(0 if k in region_lesion else clamp(s // O_DIV, 0, 15))
    return h, o
