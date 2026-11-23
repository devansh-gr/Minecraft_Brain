# Release: Redstone Cortex launch (draft)

Demonstrated version: the commit that adds the final video (SHA filled in at release).

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
