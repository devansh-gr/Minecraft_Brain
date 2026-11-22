"""Minimal redstone placement and in-game probing over RCON for the hardware prototype (HW server)."""
import os, time
os.environ.setdefault("RCON_PORT", "25597")
import sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from rcon import cmd

FACE = {(0, 1): "north", (0, -1): "south", (1, 0): "west", (-1, 0): "east"}   # flow dir -> facing


def place(blocks):
    """blocks: {(x, y, z): blockstate}. Supports first, then wires and repeaters, then (after the circuit
    has settled) torches, so no torch flickers often enough during the build to burn out."""
    rank = lambda b: 2 if "torch" in b else 1 if any(t in b for t in ("wire", "repeater", "comparator")) else 0
    for r in (0, 1, 2):
        for (x, y, z), b in sorted(blocks.items(), key=lambda kv: kv[0][1]):
            if rank(b) == r:
                cmd(f"setblock {x} {y} {z} {b}")
        time.sleep(2)


def relight(blocks):
    """Re-place every torch (a block update clears burnout)."""
    for (x, y, z), b in blocks.items():
        if "torch" in b:
            cmd(f"setblock {x} {y} {z} air"); cmd(f"setblock {x} {y} {z} {b}")


def clear(x0, z0, x1, z1, y0=-60, y1=-52):
    for y in range(y1, y0 - 1, -1):
        for z in range(z0, z1 + 1, 128):
            cmd(f"fill {x0} {y} {z} {x1} {y} {min(z + 127, z1)} air")


def power(x, y, z):
    """Redstone power level of dust at a position (or -1 if not dust)."""
    for p in range(16):
        if "passed" in cmd(f"execute if block {x} {y} {z} redstone_wire[power={p}]"):
            return p
    return -1


def lit(x, y, z, block="redstone_lamp"):
    return "passed" in cmd(f"execute if block {x} {y} {z} {block}[lit=true]")


def settle(ticks=20):
    time.sleep(ticks / 20 + 0.1)
