# Demo and launch video

Every frame in the video is real Minecraft footage recorded with ReplayMod, from runs logged with timestamps. Nothing is composited into the world.

## Footage

| Replay | World | What happened (log) |
|---|---|---|
| `neuron_demo_vd20.mcpr` (506 s) | `server_hw/` HW, neuron at (1000, 1300) | w0=4 -> y=4, then w0=8 -> y=9, same x0=5, x1=3, w1=-2, b=3, at 20 TPS ([log](hw_demo_weight_change.txt), takes from 17:04) |
| `brain_takes.mcpr` (206 s) | `server/` BrainUpright | 60 s idle at frozen midnight, then "what is seven times eight" and "can you hear the music?" through the normal sign + RUN path ([log](video_brain_takes.txt)) |

Recording client: Fabric 0.20.1 + ReplayMod 26.3-2.6.28 + Fabric API 0.167.0+26.3, in the isolated `clienttest/` folder (gitignored), user `Camera` in spectator. Server view distance 20 on the HW server so the whole 460 x 501 neuron is in the replay.

## Shots

All camera paths are source code in [`video/shots.py`](../video/shots.py): keyframes of (render time, eye, look-at) on a centripetal Catmull-Rom spline, plus a linear replay-time path. `python3 video/shots.py neuron|brain REPLAY.mcpr` writes one reel into the replay; each reel is one render with 1 ms hard cuts between shots.

| Shot | Replay | Content | Speed |
|---|---|---|---|
| hook | brain | close on the cortex, pull back | 1x |
| reveal | brain | three-quarter orbit of the lit hemisphere | 1x |
| flyover | neuron | low pass over the circuit rising to the full 460 x 501 array, during the w0=8 run | 2x, labelled |
| reg4, reg8 | neuron | the W0 register row as the weight is written | 1.4x |
| lapse4 | neuron | the computation | about 27x, labelled time-lapse |
| out4, out8 | neuron | the 4 output lamps latch 4 (0100) and 9 (1001) | 1.5x |
| activate | brain | the winning region lights after RUN | 1x |
| hero | brain | rising pullback, whole brain | 1x |

The brain shots show the separate hybrid brain. Captions say so; the neuron does not drive it.

Render: 2560 x 1440, 60 FPS, H.264, from the ReplayMod render dialog. Final edit, captions and audio: ffmpeg (see `video/`).

## Run the weight-change demo yourself

```
cd hw
python3 demo_weight_change.py     # needs the neuron built (test_neuron_game.py --build)
```

It loads x0=5, x1=3, w1=-2, b=3 and w0=4 through the write-enable rows, reads the latches back, presses START, waits for the output strobe, and reads the output latch. Then the same with w0=8. Allow about 6 minutes at 20 TPS, or run `/tick rate 100` first (the harness waits in game ticks).
