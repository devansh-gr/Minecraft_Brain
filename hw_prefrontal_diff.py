"""Blocks that change when the prefrontal gets dust on every plate row (upright.LINE_BY), as setblock commands
in a safe order (solids and lamps, then dust, then repeaters). Writes build/prefrontal_diff.txt."""
import upright, gen

def blocks(line_by):
    upright.LINE_BY = line_by
    return upright.build(gen.ROOT, gen.REGIONS, gen.STEM, gen.fills3)["blocks"]

FACE = {(0, 1): "north", (0, -1): "south", (1, 0): "west", (-1, 0): "east"}
def state(b):
    if isinstance(b, tuple):
        a, c = b[1]
        return f"repeater[facing={FACE[(c, a)]},delay={b[2] if len(b) > 2 else upright.RING_DELAY}]"
    return b

old, new = blocks({}), blocks({"prefrontal": 1})
diff = {p: state(new.get(p, "air")) for p in set(old) | set(new) if state(old.get(p, "air")) != state(new.get(p, "air"))}
rank = lambda s: 2 if s.startswith("repeater") else 1 if s == "redstone_wire" else 0
cmds = [f"setblock {x} {y} {z} {s}" for (x, y, z), s in sorted(diff.items(), key=lambda kv: (rank(kv[1]), kv[0][1]))]
open("build/prefrontal_diff.txt", "w").write("\n".join(cmds) + "\n")
from collections import Counter
print(len(cmds), Counter(s.split("[")[0] for s in diff.values()), "old->", Counter(state(old.get(p, "air")).split("[")[0] for p in diff))
