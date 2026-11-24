"""Filmed user demo on the hybrid brain (server/ BrainUpright, RCON 25599) while ReplayMod records.
A survival player walks to the console, writes the question on the sign by hand and presses RUN; the
recording player then follows the run to the redstone neuron (1000, 1300) and back, so every stage is in the replay.
Keyboard and mouse go to the Minecraft client through INP (CGEvent helper). Logs timestamps."""
import math, os, subprocess, sys, time
sys.path.insert(0, "..")
from rcon import cmd
INP = os.environ["INP"]
log = open("../docs/video_demo_takes.txt", "a")
def say(s):
    line = time.strftime("%H:%M:%S ") + s; print(line, flush=True); log.write(line + "\n"); log.flush()
def state(): return int(cmd("scoreboard players get #state brain.st").split("has ")[1].split()[0])
def hw(): return int(cmd("scoreboard players get #hw brain.st").split("has ")[1].split()[0])
def face(x, y, z):                    # aim from the eyes (rotate ... facing aims from the feet)
    p = [float(v.rstrip("d")) for v in cmd("data get entity Camera Pos").split("data: [")[1].rstrip("]").split(", ")]
    dx, dy, dz = x - p[0], y - p[1] - 1.62, z - p[2]
    cmd(f"rotate Camera {math.degrees(math.atan2(-dx, dz)):.2f} {-math.degrees(math.atan2(dy, math.hypot(dx, dz))):.2f}")
def inp(*a): subprocess.run([INP, *map(str, a)], check=True)

cmd("team add cam"); cmd("team modify cam nametagVisibility never"); cmd("team join cam Camera")
for q in ([["what is seven", "times eight"]] if len(sys.argv) < 2 else [sys.argv[1:3]]):
    while state() != 0: time.sleep(1)
    cmd('data merge block 2 -59 -74 {front_text:{messages:["","","",""]}}')
    cmd("gamemode survival Camera"); cmd("tp Camera -7.5 -60 -76.5 -90 10"); time.sleep(4)
    say("WALK"); inp("key", 13, "down"); time.sleep(2.3); inp("key", 13, "up"); time.sleep(0.8)
    face(2.5, -58.45, -73.5); time.sleep(1.0)
    say("EDIT SIGN"); inp("key", 15); time.sleep(1.0)
    inp("type", q[0]); inp("key", 36); inp("type", q[1]); time.sleep(0.6); inp("key", 53); time.sleep(1.2)
    say("SIGN " + cmd("data get block 2 -59 -74 front_text.messages"))
    face(4.5, -58.97, -73.5); time.sleep(1.0)
    inp("key", 15); say("RUN pressed")
    t = time.time(); time.sleep(4)                    # input lamps light at the console
    cmd("gamemode spectator Camera"); cmd("tp Camera 930 -20 1290 0 90"); say("TP NEURON")   # follow it to the neuron
    while hw() == 1 and time.time() - t < 400: time.sleep(0.5)
    say(f"NEURON DONE, hwy {cmd('scoreboard players get hwy brain.n').split('has ')[-1]}"); time.sleep(1.5)
    cmd("tp Camera 16 -40 -60 180 60"); say("TP BRAIN")
    while state() != 2 and time.time() - t < 600: time.sleep(0.5)
    say(f"COMPLETE (readout), state {state()}"); time.sleep(15)
say("done")
