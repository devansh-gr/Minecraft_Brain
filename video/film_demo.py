"""Filmed user demo on the hybrid brain (server/ BrainUpright, RCON 25599) while ReplayMod records.
A survival player walks to the console, writes the question on the sign by hand and presses RUN.
Keyboard and mouse go to the Minecraft client through INP (CGEvent helper). Logs timestamps."""
import os, subprocess, sys, time
sys.path.insert(0, "..")
from rcon import cmd
INP = os.environ["INP"]
log = open("../docs/video_demo_takes.txt", "a")
def say(s):
    line = time.strftime("%H:%M:%S ") + s; print(line, flush=True); log.write(line + "\n"); log.flush()
def state(): return int(cmd("scoreboard players get #state brain.st").split("has ")[1].split()[0])
def inp(*a): subprocess.run([INP, *map(str, a)], check=True)

cmd("team add cam"); cmd("team modify cam nametagVisibility never"); cmd("team join cam Camera")
for q in ([["what is seven", "times eight"]] if len(sys.argv) < 2 else [sys.argv[1:3]]):
    while state() != 0: time.sleep(1)
    cmd('data merge block 2 -59 -74 {front_text:{messages:["","","",""]}}')
    cmd("gamemode survival Camera"); cmd("tp Camera -7.5 -60 -76.5 -90 10"); time.sleep(4)
    say("WALK"); inp("key", 13, "down"); time.sleep(2.3); inp("key", 13, "up"); time.sleep(0.8)
    cmd("rotate Camera facing 2.5 -58.7 -73.5"); time.sleep(1.0)
    say("EDIT SIGN"); inp("rclick"); time.sleep(1.0)
    inp("type", q[0]); inp("key", 36); inp("type", q[1]); time.sleep(0.6); inp("key", 53); time.sleep(1.2)
    say("SIGN " + cmd("data get block 2 -59 -74 front_text.messages"))
    cmd("rotate Camera facing 4.5 -59.9 -73.5"); time.sleep(1.0)
    inp("rclick"); say("RUN pressed")
    t = time.time()
    while state() != 2 and time.time() - t < 60: time.sleep(0.5)
    say(f"COMPLETE (readout), state {state()}"); time.sleep(15)
say("done")
