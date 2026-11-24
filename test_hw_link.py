"""Brain + physical neuron link (server/ BrainUpright, RCON 25599). Asks questions through the sign + RUN path and
checks that the run waits for the redstone neuron, that its output latch equals floor((4 x_parietal + 0) / 4), and
which region wins. Logs to docs/hw_brain_link.txt."""
import json, time
from rcon import cmd
from test import score, CZ

YS = [(1060, 1268), (1064, 1268), (1068, 1268), (1072, 1268)]       # neuron output latches, world x, z (y -60)
log = open("docs/hw_brain_link.txt", "a")
def say(s):
    line = time.strftime("%H:%M:%S ") + s; print(line, flush=True); log.write(line + "\n"); log.flush()
def lamps(): return sum(("passed" in cmd(f"execute if block {x} -60 {z} repeater[powered=true]")) << i for i, (x, z) in enumerate(YS))


def run(lines, want_winner):
    while score("#state", "brain.st") not in (0, None): time.sleep(1)
    cmd("data merge block 2 -59 %d {front_text:{messages:%s}}" % (CZ, json.dumps((lines + ["", "", "", ""])[:4])))
    t0 = time.time(); cmd("function brain:ui/run")
    while score("#hw", "brain.st") != 1 and time.time() - t0 < 10: time.sleep(0.2)
    waited = score("#hw", "brain.st") == 1; ticks0 = score("#t", "brain.st")
    while score("#hw", "brain.st") == 1 and time.time() - t0 < 400: time.sleep(1)
    t_hw = time.time() - t0; x4, hwy, y = score("x4"), score("hwy"), lamps()
    while score("#state", "brain.st") != 2 and time.time() - t0 < 600: time.sleep(1)
    o = [score(f"o{k}") for k in range(8)]; rec = cmd("data get storage brain:mem list[0]")
    ok = waited and ticks0 == 1 and hwy == y == min(15, x4) and want_winner in rec
    say(f"{' / '.join(l for l in lines if l)!r}: paused at clock tick {ticks0}, neuron {t_hw:.0f} s, x_parietal={x4} "
        f"latch={y:04b} ({y}) hwy={hwy} o={o} -> {'OK' if ok else 'FAIL'}")
    say("  memory: " + rec.split("data: ")[-1][:300])
    return ok


if __name__ == "__main__":
    say("--- link test, tick rate: " + cmd("tick query").split("Target tick rate: ")[1].split(" ")[0])
    res = [run(["what is seven", "times eight"], "Parietal"), run(["what colors are", "in a rainbow?"], "Visual")]
    say(f"{sum(res)}/{len(res)}"); raise SystemExit(not all(res))
