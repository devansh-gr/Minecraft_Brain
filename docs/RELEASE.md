# Release: Redstone Cortex launch

Demonstrated version: commit `023589c` (neuron hardware unchanged since the 10/10 run; this commit adds the final shot timings and stills).

## Files

- Video: `release/redstone_cortex.mp4` (local, not in git: GitHub caps files at 100 MB). 64.9 s, 2560 x 1440, 60 FPS, H.264 + AAC, 251 MB, sha256 `51d41d056b4a6921...`. Fits X (under 512 MB and 140 s).
- Cover: `docs/img/launch/cover.jpg`. Screenshots: `docs/img/launch/` (brain close, reveal, parietal lit, neuron overview, weight register, output 9).
- Camera paths: `video/shots.py`. Edit: `video/edit.py`. Replays: `clienttest/replay_recordings/neuron_demo_vd20.mcpr`, `brain_takes.mcpr`, `demo_takes.mcpr` (local).
- Render settings: ReplayMod default rendering, MP4 custom bitrate 40 Mbps, 2560 x 1440, 60 FPS. Final encode: x264 CRF 17, AAC 192k.
- Audio: original track synthesized by `video/music.py` (Am-F-C-G pad, arpeggio, soft kick), no samples or third-party music.

## What the video shows

| Time | Content | Speed |
|---|---|---|
| 0 to 4.5 s | Upright brain, close-up | 1x |
| 4.5 to 8.5 s | A player walks to the console | 1x |
| 8.5 to 13 s | The question on the sign: "what is seven times eight" | 1x |
| 13 to 16 s | RUN pressed, its lamp lights | 0.67x |
| 16 to 19 s | Input lamps light (the network itself runs as datapack commands) | 1x |
| 19 to 24 s | The 8 comparator rails race, one stays lit | 1x |
| 24 to 29.5 s | The winner's axon lane lights toward the brain | 1x |
| 29.5 to 36 s | The parietal region lights | 1x |
| 36 to 42 s | Neuron flyover during the w0=8 run (separate build) | 2x |
| 42 to 45 s | w0 = 4 written into the register latches | 1.4x |
| 45 to 48 s | Computation | time-lapse, 27.6x |
| 48 to 52.5 s | Lamps latch 0100 = 4; caption appears only after they change | 1.5x |
| 52.5 to 55.5 s | w0 = 8 written | 1.4x |
| 55.5 to 60 s | Lamps latch 1001 = 9 | 1.5x |
| 60 to 65 s | Hero shot, region still lit | 1x |

The question shots are one continuous run (take 1 in [video_demo_takes.txt](video_demo_takes.txt)): the sign, the RUN press, the comparators, the axon and the lit region are the same answer. The player's walking, typing and button press were sent to the game client as keyboard input by `video/film_demo.py`.

## X post

I built a brain in Minecraft. You write a question on a sign, press RUN, and it lights up the brain region it links to that kind of question. "What is seven times eight" lands in the math area.

A small neural network reads the words (it runs as Minecraft commands). Then 8 possible answers race through real redstone comparators, and the winner's signal travels down a redstone wire to its brain region.

Separately, I built one neuron that does its math entirely in redstone, 49,164 blocks. Change one connection's strength from 4 to 8 and its answer goes from 4 to 9.

Code and test logs: github.com/devansh-gr/Minecraft_Brain

## Evidence

- Neuron, in game: 10/10 cases, identical to the redstone simulator (docs/hw_neuron_game.txt, docs/hw_neuron_sim.txt).
- Tick rate: 24/24 correct from 20 to 100 TPS; 143 s per evaluation at 20 TPS, 28.8 s at 100 (docs/hw_neuron_tps.md).
- Weight-change demo as filmed: docs/hw_demo_weight_change.txt.
- Brain: docs/TEST_REPORT_UPRIGHT.md.

## Not claimed

- No full neural network in redstone. One neuron.
- The neuron does not drive the brain.
- Not a biological brain simulation.
