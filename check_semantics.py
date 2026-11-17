"""Prove from the generated hidden_step that the 16 hidden updates are order-independent (synchronous)."""
import re, random
from reference import forward
L = open("build/datapack/redstone_cortex/data/brain/function/net/hidden_step.mcfunction").read().splitlines()
first_write = next(i for i, l in enumerate(L) if re.search(r"operation u\d+ brain.n \+=", l))
i_reads = [i for i, l in enumerate(L) if "#I brain.t += u" in l]
print("1. inhibition term I sums u0..u15 on lines", i_reads[0] + 1, "to", i_reads[-1] + 1,
      "; first write to any u is line", first_write + 1, "->", all(i < first_write for i in i_reads))
tail_start = next(i for i, l in enumerate(L) if "lever" in l)
blocks, cur = {}, None
for i, l in enumerate(L):
    m = re.search(r"#d brain.t = b(\d+) brain.w", l)
    if m: cur = int(m.group(1)); blocks[cur] = []
    if cur is not None and i < tail_start: blocks[cur].append(l)
foreign = {j: sorted({int(u) for l in b for u in re.findall(r"\bu(\d+) brain.n", l)} - {j}) for j, b in blocks.items()}
print("2. each unit block reads/writes only its own u:", len(blocks) == 16 and all(not v for v in foreign.values()),
      "| lesion + h copy start at line", tail_start + 1, "after every update")
# 3. numerical: reference with synchronous updates == reference with sequential updates in random order
def forward_seq(x, W, b, V, c, order):
    N, J = 8, 16; u = [0] * J
    for _ in range(4):
        I = sum(u) // 16
        for j in order:
            d = max(0, min(15, (sum(W[i][j] * x[i] for i in range(N)) + b[j]) // 4 - I))
            u[j] += (d - u[j] + 1) // 2
    return u
import dp, gen
W = [[0]*16 for _ in range(8)]; 
for i in range(8): W[i][i] = 4
ri = {r: i for i, r in enumerate([x[0] for x in gen.REGIONS])}
for m, (a, bb) in enumerate(dp.common.PAIRS): W[ri[a]][8+m] = 2; W[ri[bb]][8+m] = 2
same = 0
for t in range(2000):
    x = [random.choice([0, 3, 6, 9, 12, 15]) for _ in range(8)]
    sync, _ = forward(x, W, [0]*16, [[0]*8 for _ in range(16)], [0]*8)
    order = list(range(16)); random.shuffle(order)
    same += forward_seq(x, W, [0]*16, None, None, order) == sync
print("3. 2000 random inputs: sequential (random order) == synchronous:", same, "/ 2000")
