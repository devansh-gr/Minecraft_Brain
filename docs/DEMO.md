# Demo and launch video

Every frame in the video is real Minecraft footage recorded with ReplayMod, from runs logged with timestamps. Nothing is composited into the world.

## Footage

| Replay | World | What happened (log) |
|---|---|---|
| `neuron_demo_vd20.mcpr` (506 s) | `server_hw/` HW, neuron at (1000, 1300) | w0=4 -> y=4, then w0=8 -> y=9, same x0=5, x1=3, w1=-2, b=3, at 20 TPS ([log](hw_demo_weight_change.txt), takes from 17:04) |
| `neuron_link_fight2.mcpr` (272 s) | `server/` BrainUpright, with the redstone neuron at (1000, 1300) as the judgment detector | The current video: "who would win in a fight jensen huang or elon musk?". Same walk, sign and RUN; floating tags over the race count lit lamps per region. |
| `neuron_link.mcpr` (244 s, take 3) | same, neuron as the math detector | The earlier math video. Same walk, sign and RUN; the recording player follows the run to the neuron (noon, clear weather) while the brain waits for it, then back to the brain (midnight) for the race, axon and lit region ([log](video_link_take.txt)) |
| `demo_takes.mcpr` (487 s) | `server/` BrainUpright | A survival player walks to the console, types "what is seven times eight" on the sign and presses RUN; then "can you hear the music?" as a backup take ([log](video_demo_takes.txt)). Keyboard input sent to the client by `video/film_demo.py` |
| `brain_takes.mcpr` (206 s) | `server/` BrainUpright | 60 s idle at frozen midnight, then "what is seven times eight" and "can you hear the music?" through the normal sign + RUN path ([log](video_brain_takes.txt)) |

Recording client: Fabric 0.20.1 + ReplayMod 26.3-2.6.28 + Fabric API 0.167.0+26.3, in the isolated `clienttest/` folder (gitignored), user `Camera` in spectator. Server view distance 20 on the HW server so the whole 460 x 501 neuron is in the replay, and 16 on the brain server for the demo takes (restored to 8 after).

## Shots

All camera paths are source code in [`video/shots.py`](../video/shots.py): keyframes of (render time, eye, look-at) on a centripetal Catmull-Rom spline, plus a linear replay-time path. `python3 video/shots.py neuron|brain|demo|link REPLAY.mcpr` writes one reel into the replay; each reel is one render with 1 ms hard cuts between shots.

| Shot | Replay | Content | Speed |
|---|---|---|---|
| hook | brain | close on the cortex, pull back | 1x |
| approach, write, press | demo | the player walks to the console, the question appears on the sign, RUN lights | 1x, 1x, 0.67x |
| proc, decide, axon, lands | demo | input lamps, the 8 comparator rails (one stays lit), the winner's axon lane, the parietal region lighting, all from the same run | 1x |
| l_approach to l_lands | link | the same walk/sign/RUN/input shots, then l_flyover (neuron, 2x), l_lapse (about 21x), l_out (output lamps 0000 to 0110), then race with lamp-count tags, axon and lit region from the same run | see RELEASE.md |
| reveal | brain | three-quarter orbit of the lit hemisphere | 1x |
| flyover | neuron | low pass over the circuit rising to the full 460 x 501 array, during the w0=8 run | 2x, labelled |
| reg4, reg8 | neuron | the W0 register row as the weight is written | 1.4x |
| lapse4 | neuron | the computation | 27.6x, labelled time-lapse |
| out4, out8 | neuron | the 4 output lamps latch 4 (0100) and 9 (1001) | 1.5x |
| activate | brain | the winning region lights after RUN | 1x |
| hero | brain | rising pullback, whole brain | 1x |

Since 2026-11-24 the redstone neuron is part of the brain (since 2026-11-25 its judgment detector, README section 2). The current video uses the `link` reel plus the brain reel's hook and hero shots.

Render: 2560 x 1440, 60 FPS, H.264, from the ReplayMod render dialog. Final edit and captions: ffmpeg via `video/edit.py`. Music: original, synthesized by `video/music.py`.

## Run the weight-change demo yourself

```
cd hw
python3 demo_weight_change.py     # needs the neuron built (test_neuron_game.py --build)
```

It loads x0=5, x1=3, w1=-2, b=3 and w0=4 through the write-enable rows, reads the latches back, presses START, waits for the output strobe, and reads the output latch. Then the same with w0=8. Allow about 6 minutes at 20 TPS, or run `/tick rate 100` first (the harness waits in game ticks).
