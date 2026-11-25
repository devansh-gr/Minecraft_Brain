"""The physical redstone neuron (hw/, built at (1000, 1300) by hw/build_in_brain.py) is hidden unit P:Prefrontal (judgment) since 2026-11-25; it was P:Parietal before.
At the input stage the clock pauses: the prefrontal input is written to the neuron's input pins with w0 = 4 (all other
operands 0), START is pulsed, and when its RUN latch has been clear for 60 ticks its 4 output latches are read into
hwy. The hidden step uses hwy as that unit's drive, floor((4 x + 0) / 4), instead of computing it."""
import os, sys
from .common import *
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hw"))
from neuron import neuron, OX, OZ

X0, Z0 = 1000, 1300
UNIT = HW_UNIT
W0 = 4
TIMEOUT = 6000                       # ticks; one evaluation is 2850


def emit(c):
    w, status = c.w, c.status
    _, P = neuron()
    at = lambda p: f"{p[0] + X0} {-60 + p[1]} {p[2] + Z0}"
    pin = lambda p, on: f"setblock {at(p)} {'redstone_block' if on else 'air'}"
    run = at((OX, 0, OZ - 4))
    xi = c.ri[UNIT]

    start = [pin(p, 0) for p in P["reg"].values()]
    start += [f"scoreboard players operation #b brain.t = x{xi} brain.n", "scoreboard players set #2 brain.t 2"]
    for i in range(4):
        start += ["scoreboard players operation #r brain.t = #b brain.t", "scoreboard players operation #r brain.t %= #2 brain.t",
                  f"execute if score #r brain.t matches 1 run {pin(P['reg'][f'X0_{i}'], 1)}",
                  "scoreboard players operation #b brain.t /= #2 brain.t"]
    start += [pin(P["reg"][f"W0_{i}"], 1) for i in range(5) if W0 >> i & 1]
    start += ["scoreboard players set #hw brain.st 1", "scoreboard players set #hwt brain.st 0",
              "scoreboard players set #hwe brain.st 0", status("COMPUTING · redstone neuron (judgment detector)")]
    w("hw/start", start)

    tick = ["scoreboard players add #hwt brain.st 1",
            "execute if score #hwt brain.st matches 6 run function brain:hw/we_on",
            "execute if score #hwt brain.st matches 56 run function brain:hw/we_off",
            "execute if score #hwt brain.st matches 96 run function brain:hw/pins_off",
            f"execute if score #hwt brain.st matches 100 run {pin(P['start'], 1)}",
            f"execute if score #hwt brain.st matches 120 run {pin(P['start'], 0)}",
            f"execute if score #hwt brain.st matches 200.. if block {run} repeater[powered=true] run scoreboard players set #hwe brain.st 0",
            f"execute if score #hwt brain.st matches 200.. unless block {run} repeater[powered=true] run scoreboard players add #hwe brain.st 1",
            "execute if score #hwe brain.st matches 60.. run function brain:hw/read",
            f"execute if score #hwt brain.st matches {TIMEOUT}.. run function brain:hw/timeout"]
    w("hw/tick", tick)
    w("hw/we_on", [pin(p, 1) for p in P["we"].values()])
    w("hw/we_off", [pin(p, 0) for p in P["we"].values()])
    w("hw/pins_off", [pin(p, 0) for p in P["reg"].values()])
    w("hw/read", ["scoreboard players set hwy brain.n 0"]
      + [f"execute if block {at(p)} repeater[powered=true] run scoreboard players add hwy brain.n {1 << i}" for i, p in enumerate(P["y"])]
      + ["scoreboard players set #hw brain.st 0"])
    w("hw/timeout", ["scoreboard players set hwy brain.n 0", "scoreboard players set #hw brain.st 0",
                     'tellraw @a {"text":"Redstone neuron did not finish (chunks not loaded?). Math detector reads 0.","color":"red"}'])
