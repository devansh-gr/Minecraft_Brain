# 30-Second X Demo: Storyboard

Every shot shows real in-world behaviour. Camera presets are functions: `/function brain:cam/<name>` teleports you to the exact position, yaw and pitch. Turn the HUD off with F1 before recording.

| Time | Shot | Camera | Action | On-screen text |
|---|---|---|---|---|
| 0-3 s | Reveal | `cam/1_reveal` (16, -38, 22, facing south, pitch 32) | Idle brain under the glass roof, region labels floating | "I built a brain in Minecraft." |
| 3-7 s | Input | `cam/2_input` (8, -57.5, -82) | Write "what is seven times eight" on the sign, press RUN | |
| 7-12 s | Neural computation | `cam/3_processor` (16, -49, -80, pitch 38) | Input bars light, hidden bars grow over 4 steps | "8 inputs, 16 hidden neurons, 8 outputs" |
| 12-16 s | Decision | `cam/4_decision` (16, -49, -26, pitch 48) | Output bars die from weakest to strongest; the winner remains | "Redstone comparators kill the weaker signals" |
| 16-20 s | Brain fires | `cam/5_axons` (16, -51, -2), then `cam/6_brain_top` | Pulse runs down the lamp axon; parietal lights ring by ring | |
| 20-25 s | Damage | `cam/4_decision` then `cam/6_brain_top` | Pull the Parietal axon lever, RUN again: board shows the decision, brain stays dark, BLOCKED lamp on | "Cut the axon: it still thinks, but the signal never arrives" |
| 25-30 s | Repair + wide | `cam/7_wide` (-62, -40, -70) | Push the lever back, RUN: region lights again | "Redstone + a datapack. No mods." |

Separate learning clip (about 15 s): EXP 3, RUN (tie: temporal and visual both light), TRAIN, RUN (only visual lights). Show the TRAINED panel with the synapse counts.

## Timing notes
- A full run takes about 22 seconds: input 0.05 s, hidden 0.6 to 2.4 s, outputs 3 s, inhibition ramp 3.8 to 8 s, excitation 12.5 s, readout 19 s. Record the decision shot from 3 to 12 s.
- The idle reset happens at 29 s. Wait for READY before the next RUN.
- Night is frozen (`advance_time` false), so the glow reads well.

## Suggested post text
I built a brain in vanilla Minecraft.

Ask it a question. A small neural network computes in the datapack, then 8 brain regions compete through real redstone comparators. The strongest signal survives, runs down a redstone axon, and lights up a cortex built from an MRI atlas.

You can teach it, and you can cut its axons and watch the signal fail to arrive.

It's a neuroscience-inspired model, not a real brain simulator.
