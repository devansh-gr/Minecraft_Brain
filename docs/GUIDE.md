# How Redstone Cortex Works

This is a teaching model. It borrows ideas from neuroscience and builds them out of Minecraft parts. It is not a brain, and it cannot tell you which part of your brain a question really uses. Everything described here is implemented and tested in the world.

## Input encoding
You write a question on a sign. The datapack splits it into words, strips endings like "-ing" and "-s", and looks each word up in an 863-word list. Each word belongs to one of 8 categories. The count of matches per category becomes the input neurons: x = 3 times the count, capped at 15.

## Weighted synaptic integration
Each hidden neuron adds up its inputs, each multiplied by a weight (a synapse strength). 8 hidden neurons are "primary": each listens to one category. 8 are "association" neurons: each listens to a pair of categories, for example temporal + occipital. Output neurons add up the hidden neurons the same way. All numbers are integers, so they fit Minecraft scoreboards.

## Neural activation
Hidden neurons do not jump straight to their value. Over 4 time steps each one moves halfway toward its target, so you can watch the bars grow. A shared inhibition term (the sum of all hidden activity divided by 16) is subtracted every step. That is negative feedback: when many neurons are active, all of them are held back a little.

## Competitive inhibition
The 8 output values become physical redstone signal strengths (0 to 15) by filling barrels. A chain of comparators finds the largest value and sends it back to every channel. Each channel fires only if its own strength is at least that maximum. Inhibition is raised step by step, so the weakest channels go dark first and you can watch the decision form. Ties fire every tied channel. All zeros fire nothing. This is an analogy for lateral inhibition, not a model of real inhibitory circuits.

## Learning and plasticity
Pick a target region and press TRAIN. Every active hidden neuron gets a stronger connection to the target. Connections to any region that was tying or beating the target get weaker. Each change is 1 quarter of the neuron's activity, rounded up, and weights stay between -8 and 12. This is a simplified, supervised version of associative learning. The changed weights are stored in the world, so they survive reloads and restarts. RESET LEARNING puts every weight back to its starting value.

## Working and long-term memory
Working memory keeps the 5 most recent runs: the text, the input values, the output values, the winner, and whether a lesion or training was involved. REPLAY runs a stored input again through the current weights, so you can compare before and after training. Long-term memory is the weights themselves.

## Axonal transmission
The winning channel's signal becomes a full-strength pulse and travels along a line of redstone dust on lamps. Repeaters along the line restore the signal, which dust loses at one level per block. That is an engineering analogy for signal regeneration along an axon, not a model of real nerve fibres. At the brain, the pulse spreads ring by ring through each region.

## Region lesions versus axon lesions
- **Region lesion** (lever in zone C): the region's neurons are silenced in the network. Its output is 0, so it never enters the competition, and the runner-up can win instead. This changes computation.
- **Axon lesion** (lever on the axon in zone D): the network and the competition run normally and the region still wins, but a comparator on the axon blocks the pulse, so the brain region stays dark. This changes transmission only.
- **Synapse lesion** (lever in zone B): the region's main input connection stops counting. Its output drops but other paths remain, so training can partly restore it.

## Limitations
- Keyword matching is not understanding. "How do I quit soccer" goes to motor.
- Real brains process questions in many regions at once. Winner-take-all is a simplification chosen to make competition visible.
- The cortex map is the left hemisphere only. Deep structures such as the amygdala and hippocampus are not shown, so emotion words map to prefrontal.
- The network is tiny (8-16-8) and its starting weights were set by hand, not trained on data.
- Recovery after a synapse lesion shows how a network can route around damage. It does not reproduce stroke recovery.
