"""Barrel item counts that make a comparator read 0..15."""
import json, math
from .common import *


def emit(c):
    w, R, N, J, ri, cx, hx, hname, W, V, feeds, col, lc, kw, lever_region, lever_syn, lever_axon, lever, lamp, status, bar = (c.w, c.R, c.N, c.J, c.ri, c.cx, c.hx, c.hname, c.W, c.V, c.feeds, c.col, c.lc, c.kw, c.lever_region, c.lever_syn, c.lever_axon, c.lever, c.lamp, c.status, c.bar)
    # ---------------- barrel fills: comparator strength s from a 27-slot barrel
    for s in range(16):
        t = 0 if s == 0 else math.ceil(1728 * (s - 1) / 14) or 1
        assert s == (0 if t == 0 else 1 + int(14 * t / 1728)), s
        lines = []
        for slot in range(27):
            c = min(64, t); t -= c
            lines.append(f"$item replace block $(x) $(y) $(z) container.{slot} with "
                         + (f"minecraft:glowstone_dust {c}" if c else "minecraft:air"))
        w(f"fill/s{s}", lines)
    w("fill/by", ["$function brain:fill/s$(s) {x:$(x),y:$(y),z:$(z)}"])

    BARRELS = ([(cx[r], L1, -28) for r in R] + [(x, L1, -48) for x in hx] +
               [(cx[r], L1, -3) for r in R] + [(cx[r], L0, 2) for r in R] + [(cx[r], L1, 1) for r in R])
    w("clear_barrels", [f"function brain:fill/s0 {{x:{x},y:{y},z:{z}}}" for x, y, z in BARRELS])

