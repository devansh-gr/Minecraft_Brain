# Phase 3 Evidence: Lesions and Repair

Run 2026-11-18 on the test copy of the world. Script: `exp_lesions.py`; raw data `build/phase3.json`. Input: "what color is the sky when i feel sad and hear music?". The lesioned region is the region the intact run physically selected (**temporal**); it is not hardcoded.

Output order: prefrontal, Broca, motor, somato, parietal, temporal, occipital, cerebellum. *fired* = tract heads powered after the comparator decision. *lit* = fraction of 40 sampled cortex lamps lit per region. *BLOCKED* = console lamp driven by the readout.

| step | o (datapack) | fired (physical decision) | cortex lit | BLOCKED | status |
|---|---|---|---|---|---|
| 1-2 intact | [3, 0, 0, 2, 1, 10, 5, 0] | ['temporal'] | {'temporal': 1.0} | False | COMPLETE · Temporal  |
| 3-5 axon cut | [3, 0, 0, 2, 1, 10, 5, 0] | ['temporal'] | {} | True | COMPUTED Temporal · AXON CUT, signal blocked |
| 6-8 axon repaired | [3, 0, 0, 2, 1, 10, 5, 0] | ['temporal'] | {'temporal': 1.0} | False | COMPLETE · Temporal  |
| region lesion | [3, 0, 0, 2, 1, 0, 7, 0] | ['occipital'] | {'occipital': 1.0} | False | COMPLETE · Visual  |
| synapse lesion | [3, 0, 0, 2, 1, 3, 5, 0] | ['occipital'] | {'occipital': 1.0} | False | COMPLETE · Visual  |
| synapse lesion + TRAIN x1 | [0, 0, 0, 2, 1, 10, 0, 0] | ['temporal'] | {'temporal': 1.0} | False | COMPLETE · Temporal  |
| synapse lesion + TRAIN x2 | [0, 0, 0, 2, 1, 15, 0, 0] | ['temporal'] | {'temporal': 1.0} | False | COMPLETE · Temporal  |
| synapse lesion + TRAIN x3 | [0, 0, 0, 2, 1, 15, 0, 0] | ['temporal'] | {'temporal': 1.0} | False | COMPLETE · Temporal  |
| repaired + weights reset | [3, 0, 0, 2, 1, 10, 5, 0] | ['temporal'] | {'temporal': 1.0} | False | COMPLETE · Temporal  |

## Reading the results
- **Axon lesion (the mandatory 8-step experiment).** The computation (o) and the physical decision (fired) are identical to the intact run, but no temporal lamp lights and BLOCKED is on. After repair, delivery returns. The cut is a subtract-mode comparator in the tract whose side input comes from the lever; no command touches the tract.
- **Region lesion.** temporal's primary hidden unit and output are silenced in the network. Its output is 0, so it never enters the comparator competition, and the circuit selects the runner-up. The runner-up's output rose from 5 to 7, because the shared inhibition term I fell once temporal's primary unit was silent.
- **Synapse lesion.** Cutting temporal's direct primary-to-output synapse dropped its output from 10 to 3, below the runner-up, so the winner changed. Training temporal under the lesion strengthened its remaining association connections and weakened the competitor's: one update restored temporal as the physical winner (10), and a second saturated it (15). This shows recovery through alternative pathways in this small network; it does not model clinical stroke recovery.
- **Full repair** (all levers reset, weights reset) restored the intact numbers and decision exactly.

Limitation: region and synapse lesions act on the datapack's numerical model (they set values to 0 or remove a term). Only the axon lesion is a physical interruption of redstone.
