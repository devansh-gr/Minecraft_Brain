# Redstone Cortex

A neuroscience-inspired circuit model in vanilla Minecraft 26.3. Write a question on a sign and press RUN. A small neural network (8 inputs, 16 leaky hidden neurons, 8 outputs) computes in the datapack. The 8 outputs then compete through physical redstone comparators: inhibition rises, weaker candidates go dark, and the survivor's spike runs down a lamp axon into a 12,856-lamp cortex built from the Harvard-Oxford MRI atlas.

- **Learns:** a TRAIN button applies a bounded supervised update to the 128 hidden-to-output synapses. Weights persist across reloads and restarts.
- **Remembers:** working memory of the last 5 runs, with REPLAY.
- **Breaks:** region, synapse and axon lesions with REPAIR. An axon lesion is a physical redstone gate.
- **Honest split:** the datapack reads text and does the arithmetic. Redstone makes the decision and carries the signal. No command blocks.

Docs: [architecture](docs/ARCHITECTURE.md), [how it works](docs/GUIDE.md), [test report](docs/TEST_REPORT.md), [demo storyboard](docs/DEMO.md), [research notebook](docs/NOTEBOOK.md).

## Build
```
python3 -m venv .venv && .venv/bin/pip install numpy scipy nibabel nilearn nbtlib
.venv/bin/python gen.py
```
Copy `build/datapack/redstone_cortex` into a flat 26.3 world's `datapacks` folder, then run `/forceload add -80 -100 110 190` and `/function brain:build`. Tests: `python3 test.py` against a server with RCON on port 25599.
