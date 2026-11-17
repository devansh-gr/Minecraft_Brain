# Phase 2 Evidence: Plasticity, Memory, Persistence

Run 2026-11-18 on the test copy of the world (`server/BrainTest`). Script: `exp_plasticity.py`. Raw data: `build/phase2.json`.

## Protocol (no hardcoded winner)
1. Reset weights to baseline. For each candidate question in order, run the full pipeline and keep the first one whose **physical** decision has a unique winner and a nonzero runner-up.
2. A = the region whose tract head fired. B = the region with the highest measured output o other than A (lowest index on ties).
3. Select target B, LEARN on, press TRAIN, rerun the same input through the full pipeline, and read the physical winner. Repeat until the physical winner is B (at most 8 times).
4. Stop and restart the server. Read the weights back and run the same input again.

Input selected: **"what color is the sky when i feel sad and hear music?"**. A = **temporal**, B = **occipital**. Training steps needed: **1**.

## Before and after

| | before training | after training | after server restart |
|---|---|---|---|
| x (input) | [3, 0, 0, 3, 0, 9, 6, 0] | [3, 0, 0, 3, 0, 9, 6, 0] | [3, 0, 0, 3, 0, 9, 6, 0] |
| h (hidden) | [2, 0, 0, 2, 0, 7, 4, 0, 4, 3, 0, 1, 1, 2, 5, 1] | [2, 0, 0, 2, 0, 7, 4, 0, 4, 3, 0, 1, 1, 2, 5, 1] | [2, 0, 0, 2, 0, 7, 4, 0, 4, 3, 0, 1, 1, 2, 5, 1] |
| o (output) | [3, 0, 0, 2, 1, 10, 5, 0] | [3, 0, 0, 2, 1, 0, 15, 0] | [3, 0, 0, 2, 1, 0, 15, 0] |
| physical winner (tract head) | ['temporal'] | ['occipital'] | ['occipital'] |
| cortex lamps lit (sampled fraction) | {'temporal': 1.0} | {'occipital': 1.0} | {'occipital': 1.0} |

Output order: prefrontal, Broca, motor, somato, parietal, temporal, occipital, cerebellum. Hidden activations do not change with training: the rule only modifies hidden-to-output synapses, and the input is the same.

Weights after restart identical to weights before restart: **True**.

## Exact synapses changed by the training step

| synapse | from hidden unit | to output | before | after |
|---|---|---|---|---|
| V0_5 | P:prefrontal (h=2) | temporal | 0 | -1 |
| V0_6 | P:prefrontal (h=2) | occipital | 0 | 1 |
| V3_5 | P:somato (h=2) | temporal | 0 | -1 |
| V3_6 | P:somato (h=2) | occipital | 0 | 1 |
| V5_5 | P:temporal (h=7) | temporal | 4 | 2 |
| V5_6 | P:temporal (h=7) | occipital | 0 | 2 |
| V6_5 | P:occipital (h=4) | temporal | 0 | -1 |
| V6_6 | P:occipital (h=4) | occipital | 4 | 5 |
| V8_5 | A:prefrontal+temporal (h=4) | temporal | 1 | 0 |
| V8_6 | A:prefrontal+temporal (h=4) | occipital | 0 | 1 |
| V9_5 | A:broca+temporal (h=3) | temporal | 1 | 0 |
| V9_6 | A:broca+temporal (h=3) | occipital | 0 | 1 |
| V11_5 | A:motor+somato (h=1) | temporal | 0 | -1 |
| V11_6 | A:motor+somato (h=1) | occipital | 0 | 1 |
| V12_5 | A:somato+parietal (h=1) | temporal | 0 | -1 |
| V12_6 | A:somato+parietal (h=1) | occipital | 0 | 1 |
| V13_5 | A:parietal+occipital (h=2) | temporal | 0 | -1 |
| V13_6 | A:parietal+occipital (h=2) | occipital | 1 | 2 |
| V14_5 | A:temporal+occipital (h=5) | temporal | 1 | -1 |
| V14_6 | A:temporal+occipital (h=5) | occipital | 1 | 3 |
| V15_5 | A:prefrontal+parietal (h=1) | temporal | 0 | -1 |
| V15_6 | A:prefrontal+parietal (h=1) | occipital | 0 | 1 |

Rule check from the data: every |after - before| equals ceil(h_j / 4) for its source unit j: **True**. Strengthened: the connections from all 11 active hidden units to occipital. Weakened: connections to the outputs that tied or beat the target before training (o_k >= o_occipital = 5, o_k > 0): **temporal**. Outputs below 5 (prefrontal 3, somato 2, parietal 1) were not weakened.

## Notes
- One training step was enough: the temporal primary unit (h = 7) lost 2 on its connection to temporal (4 -> 2) and gained 2 toward occipital, and the temporal+occipital association unit moved both ways as well. Pre-clamp sums after training (computed from the stored weights and activations): temporal -4 -> o = clamp(floor(-4/4), 0, 15) = 0; occipital 67 -> 15.
- Working memory recorded both runs, marked the trained one, and survived the restart (`brain:mem` storage is saved with the world).
