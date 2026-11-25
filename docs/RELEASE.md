# Release: Redstone Cortex launch

Demonstrated version: commit `023589c` (neuron hardware unchanged since the 10/10 run; this commit adds the final shot timings and stills).

## Files

- Video: `release/redstone_cortex.mp4` (local, not in git: GitHub caps files at 100 MB). 55.4 s, 2560 x 1440, 60 FPS, H.264 + AAC, 218 MB, sha256 `95271aaee2496fe5...`. Fits X (under 512 MB and 140 s).
- Cover: `docs/img/launch/cover.jpg`. Screenshots: `docs/img/launch/` (brain close, reveal, parietal lit, neuron overview, weight register, output 9).
- Camera paths: `video/shots.py`. Edit: `video/edit.py`. Replays: `clienttest/replay_recordings/neuron_link.mcpr` (take 3) and `brain_takes.mcpr` (local).
- Render settings: ReplayMod default rendering, MP4 custom bitrate 40 Mbps, 2560 x 1440, 60 FPS. Final encode: x264 CRF 17, AAC 192k.
- Audio: original track synthesized by `video/music.py` (Am-F-C-G pad, arpeggio, soft kick), no samples or third-party music.

## What the video shows

| Time | Content | Speed |
|---|---|---|
| 0 to 4.5 s | Upright brain, close-up | 1x |
| 4.5 to 8.5 s | A player walks to the console | 1x |
| 8.5 to 13 s | The question on the sign: "what is seven times eight" | 1x |
| 13 to 16 s | RUN pressed, its lamp lights | 0.33x |
| 16 to 19 s | Input lamps light | 1x |
| 19 to 24.5 s | The redstone neuron (the brain's math detector) computing; the brain's clock is paused | 2x |
| 24.5 to 28.5 s | Same computation | time-lapse, about 21x |
| 28.5 to 33.5 s | Its 4 output lamps change from 0000 to 1001 (9); caption appears as they change | 1x |
| 33.5 to 38.5 s | The 8 comparator rails race, the math rail stays lit | 1x |
| 38.5 to 44 s | The winner's axon lane lights toward the brain | 1x |
| 44 to 50.5 s | The parietal (math) region lights | 1x |
| 50.5 to 55.4 s | Hero shot, region lit (from the earlier brain take) | 1x |

All shots from 4.5 s to 50.5 s are one continuous run, take 3 in [video_link_take.txt](video_link_take.txt) (RUN at 22:30:26, neuron done at 22:32:57 with output 9). The player's walking, typing and button press were sent to the game client as keyboard input by `video/film_demo.py`; the recording player then teleported to the neuron and back. Lighting: the sky was set to noon while the camera was at the neuron and back to midnight for the brain, and weather was cleared, because take 1 was too dark and rainy to read. Before take 3 the neuron's output lamps were reset to 0000 by a real rainbow question (Visual), so the change to 1001 is visible; take 2 started with 1001 still latched from an earlier run.

## X post

I built a brain in Minecraft. You write a question on a sign, press RUN, and it lights up the part of the brain that handles that kind of question. "What is seven times eight" lands in the math area.

One of its neurons is built entirely from redstone, 49,164 blocks. It is the brain's math detector: the brain stops and waits about two and a half minutes while it works out how much math is in your question, then uses its answer. The other neurons run as Minecraft commands.

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
