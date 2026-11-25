# Release: Redstone Cortex launch

Demonstrated version: commit `87bf3de` (redstone neuron linked into the brain as its judgment detector, hidden unit P:Prefrontal; neuron hardware unchanged since the 10/10 run). Video, shot timings and docs: the commit after it.

## Files

- Video: `release/redstone_cortex.mp4` (local, not in git: GitHub caps files at 100 MB). 53.4 s, 2560 x 1440, 60 FPS, H.264 + AAC, 211 MB, sha256 `cf1364eba09ae49e...`. Fits X (under 512 MB and 140 s). The earlier math cut is kept as `release/redstone_cortex_math.mp4`.
- Cover: `docs/img/launch/cover.jpg`. Screenshots: `docs/img/launch/` (from the math cut).
- Camera paths: `video/shots.py`. Edit: `video/edit.py`. Replays: `clienttest/replay_recordings/neuron_link_fight2.mcpr` and `brain_takes.mcpr` (local).
- Render settings: ReplayMod default rendering, MP4 custom bitrate 40 Mbps, 2560 x 1440, 60 FPS. Final encode: x264 CRF 17, AAC 192k.
- Audio: original track synthesized by `video/music.py` (Am-F-C-G pad, arpeggio, soft kick), no samples or third-party music. Placeholder; may be replaced in post.

## What the video shows

| Time | Caption | Content | Speed |
|---|---|---|---|
| 0 to 4.5 s | I built a brain in Minecraft | Upright brain, close-up | 1x |
| 4.5 to 8 s | You can ask it anything | A player walks to the console | 1x |
| 8 to 12.5 s | Who would win in a fight, Jensen Huang or Elon Musk? | The question on the sign | 1x |
| 12.5 to 15 s | Press RUN | RUN pressed, its lamp lights | 0.33x |
| 15 to 18 s | A neural network reads your question | Input lamps light | 1x |
| 18 to 23.5 s | and decides which part of the brain it triggers | The redstone neuron (the network's judgment detector) computing; the brain's clock is paused | 2x |
| 23.5 to 27 s | Thinking... | Same computation | time-lapse, about 21x |
| 27 to 32 s | Is this asking for an opinion? Yes. | Its 4 output lamps change from 0000 to 0110 (6) at 29.7 s; caption appears as they change | 1x |
| 32 to 37.5 s | Judgment, memory and vision fight over it | The 8 comparator rails race; floating tags count lit lamps (Judgment 7, Memory 3, Vision 3, the rest 0) | 1x |
| 37.5 to 42.5 s | Judgment wins. The signal shoots up to the brain... | The winner's axon lane lights toward the brain | 1x |
| 42.5 to 48.5 s | ...and triggers the prefrontal cortex | The prefrontal region lights | 1x |
| 48.5 to 53.4 s | REDSTONE CORTEX | Hero shot, region lit (from the earlier brain take) | 1x |

All shots from 4.5 s to 48.5 s are one continuous run, fight take 2 in [video_link_take.txt](video_link_take.txt) (RUN at 06:22:57, neuron done at 06:25:28 with output 6, winner Prefrontal, outputs o = [6,0,0,0,0,2,2,0]). The player's walking, typing and button press were sent to the game client as keyboard input by `video/film_demo.py`; the recording player then teleported to the neuron and back. The sky was set to noon at the neuron and midnight at the brain, and weather was cleared. Before the take the neuron's output lamps were reset to 0000 by a real rainbow question (Visual), so the change to 0110 is visible. Fight take 1 (06:13) gave the same result but its race tags were too small to read (scale 0.9); take 2 used scale 2.6.

## X post

I built a brain in Minecraft. You write any question on a sign, press RUN, and a neural network decides which part of the brain it triggers. "Who would win in a fight, Jensen Huang or Elon Musk?" lands in the prefrontal cortex, the judgment area.

Part of that network is built entirely from redstone: one neuron, 49,164 blocks. It is the judgment detector. The brain stops and waits about two and a half minutes while it decides whether your question asks for an opinion. The other neurons run as Minecraft commands.

Then the brain areas race through real redstone comparators, and the winner's signal travels down a redstone wire to its region.

Code and test logs: github.com/devansh-gr/Minecraft_Brain

## Evidence

- Neuron, in game: 10/10 cases, identical to the redstone simulator (docs/hw_neuron_game.txt, docs/hw_neuron_sim.txt).
- Tick rate: 24/24 correct from 20 to 100 TPS; 144 s per evaluation at 20 TPS, 28.8 s at 100 (docs/hw_neuron_tps.md).
- Weight-change demo as filmed: docs/hw_demo_weight_change.txt.
- Brain: docs/TEST_REPORT_UPRIGHT.md.
- Neuron linked into the brain: 5/5 in-place self-test and 2/2 questions (docs/hw_brain_link.txt, docs/NOTEBOOK.md 17.s).

## Not claimed

- No full neural network in redstone. One of the brain's 24 neurons is redstone; the rest run as datapack commands.
- Commands carry the neuron's input in and read its output lamps back; they do not compute its result.
- Not a biological brain simulation.
