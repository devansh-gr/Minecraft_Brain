"""Minimal redstone placement and in-game probing over RCON for the hardware prototype (HW server)."""
import os, time
os.environ.setdefault("RCON_PORT", "25597")
import sys; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from rcon import cmd

FACE = {(0, 1): "north", (0, -1): "south", (1, 0): "west", (-1, 0): "east"}   # flow dir -> facing


def place(blocks):
    """blocks: {(x, y, z): blockstate}. Places supports first (non-redstone), then redstone parts."""
    order = sorted(blocks.items(), key=lambda kv: (any(t in kv[1] for t in ("wire", "repeater", "comparator", "torch")), kv[0][1]))
    for (x, y, z), b in order:
        cmd(f"setblock {x} {y} {z} {b}")


def clear(x0, z0, x1, z1, y0=-60, y1=-52):
    for y in range(y1, y0 - 1, -1):
        cmd(f"fill {x0} {y} {z0} {x1} {y} {z1} air")


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
