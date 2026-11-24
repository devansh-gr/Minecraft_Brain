# Release: Redstone Cortex launch

Demonstrated version: commit `023589c` (neuron hardware unchanged since the 10/10 run; this commit adds the final shot timings and stills).

## Files

- Video: `release/redstone_cortex.mp4` (local, not in git: GitHub caps files at 100 MB). 47.9 s, 2560 x 1440, 60 FPS, H.264 + AAC, 165 MB, sha256 `44c729cfb2ec6f0a...`. Fits X (under 512 MB and 140 s).
- Cover: `docs/img/launch/cover.jpg`. Screenshots: `docs/img/launch/` (brain close, reveal, parietal lit, neuron overview, weight register, output 9).
- Camera paths: `video/shots.py`. Edit: `video/edit.py`. Replays: `clienttest/replay_recordings/neuron_demo_vd20.mcpr`, `brain_takes.mcpr` (local).
- Render settings: ReplayMod default rendering, MP4 custom bitrate 40 Mbps, 2560 x 1440, 60 FPS. Final encode: x264 CRF 17, AAC 192k.
- Audio: a drone synthesized in `video/edit.py` (sine tones), no third-party music.

## What the video shows

| Time | Content | Speed |
|---|---|---|
| 0 to 11 s | Upright brain, close-up and reveal | 1x |
| 11 to 19 s | Neuron flyover during the w0=8 run | 2x |
| 19 to 22 s | w0 = 4 written into the register latches | 1.4x |
| 22 to 25 s | Computation | time-lapse, 27.6x |
| 25 to 29.5 s | Lamps latch 0100 = 4; caption appears only after they change | 1.5x |
| 29.5 to 32.5 s | w0 = 8 written | 1.4x |
| 32.5 to 37 s | Lamps latch 1001 = 9 | 1.5x |
| 37 to 43 s | Hybrid brain: parietal lights after "what is seven times eight" | 1x |
| 43 to 48 s | Hero shot, region still lit | 1x |

## X post

I built a brain in Minecraft. Then I built one neuron whose math runs entirely through redstone.

49,164 blocks. The inputs and weights sit in redstone latches. A carry-save array multiplies and adds, a delay-line sequencer clocks it, and 4 lamps show the answer.

Same inputs, change one stored weight from 4 to 8: the output goes from 4 to 9.

The brain is a separate, hybrid build: the network runs in a datapack, and redstone comparators pick the winner.

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
