# Redstone Cortex

A brain circuit in vanilla Minecraft 26.3. Write a question on a sign and press the button. Eight brain regions compete through comparator circuitry, the weaker candidates die out as inhibition rises, and the winning spike travels down a lamp axon into a 12,856-lamp cortex map built from the Harvard-Oxford MRI atlas, where it spreads ring by ring through 1,698 repeaters.

- Pure redstone after the input: winner-take-all, axons, cortex lighting.
- One command block (the button) and a datapack that reads the sign.
- Lesion levers: silence a region and the same question goes to the runner-up.

This is a neuroscience-inspired circuit model, not a biologically accurate brain simulation. Keyword matching decides which region a question goes to.

Design, parameters and test results: [docs/NOTEBOOK.md](docs/NOTEBOOK.md).

## Build
```
python3 -m venv .venv && .venv/bin/pip install numpy scipy nibabel nilearn nbtlib
.venv/bin/python gen.py
```
Copy `build/datapack/redstone_cortex` into a flat 26.3 world's `datapacks` folder, then run `/forceload add -64 -34 96 172` and `/function brain:build`.
