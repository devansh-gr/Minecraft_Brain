"""Filmed run of the hybrid 8-16-8 brain (server/ BrainUpright, RCON 25599) while ReplayMod records.
Idle hold for hook/reveal/hero shots, then real questions through the normal UI path. Logs timestamps."""
import json, sys, time
sys.path.insert(0, "..")
from rcon import cmd
log = open("../docs/video_brain_takes.txt", "a")
def say(s):
    line = time.strftime("%H:%M:%S ") + s; print(line, flush=True); log.write(line + "\n"); log.flush()
def state(): return int(cmd("scoreboard players get #state brain.st").split("has ")[1].split()[0])

cmd("gamemode spectator Camera"); cmd("tp Camera -60 -44 30 -45 -13.6")
say("idle hold 60 s (night, time frozen)"); time.sleep(60)
for q in (["what is seven", "times eight"], ["can you hear", "the music?"]):
    while state() != 0: time.sleep(1)
    cmd("data merge block 2 -59 -74 {front_text:{messages:%s}}" % json.dumps((q + ["", "", "", ""])[:4]))
    say(f"RUN {' '.join(q)!r}"); cmd("function brain:ui/run")
    while state() != 2: time.sleep(0.5)
    say("COMPLETE (readout)"); time.sleep(15)
say("done")
