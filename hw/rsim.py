"""Offline redstone simulator for the hw/ block subset, in redstone ticks.
Blocks: redstone_wire, repeater[facing=..,delay=..], comparator[facing=..,mode=..], redstone_block,
stone/smooth_stone (conductors), glass (not a conductor). facing = side the input comes from (MC convention).
Used to check layouts before building them; in-game tests stay the ground truth."""
import re
from collections import deque

D = {"north": (0, 0, -1), "south": (0, 0, 1), "west": (-1, 0, 0), "east": (1, 0, 0)}
H = list(D.values())
UP, DOWN = (0, 1, 0), (0, -1, 0)
CONDUCTOR = {"stone", "smooth_stone", "redstone_lamp"}         # a lamp is a solid block: a repeater facing it powers adjacent dust
SUPPORT = CONDUCTOR | {"glass", "redstone_block"}


def add(p, d, k=1): return (p[0] + k * d[0], p[1] + k * d[1], p[2] + k * d[2])


def parse(b):
    m = re.match(r"([a-z_]+)(?:\[(.*)\])?", b)
    props = dict(kv.split("=") for kv in m.group(2).split(",")) if m.group(2) else {}
    return m.group(1), props


class Sim:
    def __init__(self, blocks):
        self.B = {}
        for p, b in blocks.items():
            self.B[p] = parse(b)
        self.kind = {p: k for p, (k, _) in self.B.items()}
        self.diodes = {p: pr for p, (k, pr) in self.B.items() if k in ("repeater", "comparator")}
        self.out = {p: 0 for p in self.diodes}
        self.hist = {p: deque([0] * 4, maxlen=4) for p in self.diodes}
        self.locked = {p: False for p in self.diodes}
        self._wire_graph()

    def k(self, p): return self.kind.get(p, "air")

    def set(self, p, b):
        if b == "air": self.B.pop(p, None); self.kind.pop(p, None)
        else: self.B[p] = parse(b); self.kind[p] = self.B[p][0]
        self._wire_graph()

    # ---------- dust connectivity ----------
    def _wire_graph(self):
        self.wires = [p for p, k in self.kind.items() if k == "redstone_wire"]
        # recv[p]: dust that p takes power from (MC calculateTargetStrength): same level; up-diagonal only
        # through a conductor neighbour with no conductor above p; down-diagonal only past a non-conductor
        self.recv = {p: [] for p in self.wires}
        for p in self.wires:
            above_c = self.k(add(p, UP)) in CONDUCTOR
            for d in H:
                n = add(p, d); kn = self.k(n)
                if kn == "redstone_wire": self.recv[p].append(n)
                if kn in CONDUCTOR and not above_c:
                    if self.k(add(n, UP)) == "redstone_wire": self.recv[p].append(add(n, UP))
                elif kn not in CONDUCTOR and self.k(add(n, DOWN)) == "redstone_wire":
                    self.recv[p].append(add(n, DOWN))
        self.adj = {p: [] for p in self.wires}
        self.points = {}
        for p in self.wires:
            dirs = []
            above_open = self.k(add(p, UP)) not in CONDUCTOR
            for d in H:
                n = add(p, d); kn = self.k(n)
                if above_open and kn in SUPPORT and self.k(add(n, UP)) == "redstone_wire":
                    self.adj[p].append(add(n, UP)); dirs.append(d); continue
                if kn == "redstone_wire":
                    self.adj[p].append(n); dirs.append(d); continue
                if kn == "repeater":
                    f = D[self.B[n][1]["facing"]]
                    if f[0] == d[0] and f[2] == d[2] or f[0] == -d[0] and f[2] == -d[2]: dirs.append(d)
                    continue
                if kn in ("comparator", "redstone_block"):
                    dirs.append(d); continue
                if kn not in CONDUCTOR and self.k(add(n, DOWN)) == "redstone_wire":
                    self.adj[p].append(add(n, DOWN)); dirs.append(d)
            if not dirs: pts = list(H)
            elif len(dirs) == 1: pts = dirs + [(-dirs[0][0], 0, -dirs[0][2])]
            else: pts = dirs
            self.points[p] = pts

    def front(self, p):
        f = D[self.diodes[p]["facing"]]
        return add(p, f, -1)

    def behind(self, p): return add(p, D[self.diodes[p]["facing"]])

    # ---------- power ----------
    def _powers(self):
        strong = {}
        for p in self.diodes:
            if self.out[p] > 0:
                q = self.front(p)
                if self.k(q) in CONDUCTOR: strong[q] = max(strong.get(q, 0), self.out[p])
        lvl = {}
        for w in self.wires:
            s = 0
            for d in H + [UP, DOWN]:
                n = add(w, d); kn = self.k(n)
                if kn == "redstone_block": s = 15
                elif n in strong: s = max(s, strong[n])
                elif kn in ("repeater", "comparator") and self.front(n) == w: s = max(s, self.out[n])
            lvl[w] = s
        # max-propagation along dust with decay 1
        send = {w: [] for w in self.wires}
        for w, rs in self.recv.items():
            for r in rs: send[r].append(w)
        q = deque(w for w in self.wires if lvl[w] > 0)
        while q:
            w = q.popleft()
            for n in send[w]:
                if lvl[w] - 1 > lvl[n]: lvl[n] = lvl[w] - 1; q.append(n)
        weak = {}
        for w in self.wires:
            if lvl[w] == 0: continue
            for t in [add(w, DOWN)] + [add(w, d) for d in self.points[w]]:
                if self.k(t) in CONDUCTOR: weak[t] = max(weak.get(t, 0), lvl[w])
        return lvl, strong, weak

    def _signal_into(self, src, dst, lvl, strong, weak):
        """Power that block at src delivers to a diode at dst (rear input)."""
        ks = self.k(src)
        if ks == "redstone_wire":
            d = (dst[0] - src[0], 0, dst[2] - src[2])
            return lvl[src] if d in self.points[src] else 0
        if ks == "redstone_block": return 15
        if ks in ("repeater", "comparator"): return self.out[src] if self.front(src) == dst else 0
        if ks in CONDUCTOR: return max(strong.get(src, 0), weak.get(src, 0))
        return 0

    def _side(self, src, dst, lvl):
        ks = self.k(src)
        if ks == "redstone_wire": return lvl[src]
        if ks == "redstone_block": return 15
        if ks in ("repeater", "comparator"): return self.out[src] if self.front(src) == dst else 0
        return 0

    def step(self):
        lvl, strong, weak = self._powers()
        new = {}
        for p, pr in self.diodes.items():
            rear = self._signal_into(self.behind(p), p, lvl, strong, weak)
            f = D[pr["facing"]]
            sides = [add(p, (f[2], 0, f[0])), add(p, (-f[2], 0, -f[0]))]
            if self.k(p) == "repeater":
                lock = any(self.k(s) in ("repeater", "comparator") and self.front(s) == p and self.out[s] > 0 for s in sides)
                delay = int(pr.get("delay", 1))
                h = self.hist[p]; h.append(15 if rear > 0 else 0)
                if lock: new[p] = self.out[p]
                else: new[p] = h[-delay]
            else:
                side = max(self._side(s, p, lvl) for s in sides)
                if pr.get("mode", "compare") == "subtract": new[p] = max(rear - side, 0)
                else: new[p] = rear if rear >= side else 0
        changed = new != self.out
        self.out = new
        self.lvl = lvl
        return changed

    def settle(self, max_ticks=400):
        """Run until stable; returns ticks taken (None if never stable)."""
        for t in range(max_ticks):
            if not self.step():
                # confirm stable for 4 ticks (repeater delay lines)
                if all(not self.step() for _ in range(4)): return t
        return None

    def power(self, p):
        lvl, strong, weak = self._powers()
        if self.k(p) == "redstone_wire": return lvl[p]
        if p in self.diodes: return self.out[p]
        return max(strong.get(p, 0), weak.get(p, 0))
