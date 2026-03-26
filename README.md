# 1D Beam Solver

Python beam analysis project for Mechanics of Materials coursework.

Repository: [MarkZaki/1D-Beam-Solver](https://github.com/MarkZaki/1D-Beam-Solver)

## Overview

This project solves a first set of statically determinate 1D beam problems and generates the core engineering diagrams needed for classwork:

- support reactions
- shear force diagrams
- bending moment diagrams
- deflection curves

The current version focuses on a small, verifiable solver instead of a large feature set.

## Implemented Scope

Supported beam types:

- simply supported beam
- cantilever beam

Supported load types:

- signed point loads
- distributed loads defined as `w(x)` over any span segment
- applied moments

Implemented outputs:

- left and right reactions for simply supported beams
- fixed-end shear and moment for cantilevers
- shear values along the beam
- bending moment values along the beam
- deflection values from numerical integration of `M / (E * I)`
- saved plot images for shear, moment, and deflection
- browser-based UI for custom beam cases
- beam model drawing with supports, loads, reactions, and applied moments
- point inspection at any beam location

## Project Structure

```text
1D-Beam-Solver/
|-- README.md
|-- plan.md
|-- requirements.txt
|-- app.py
|-- main.py
|-- beam.py
|-- solver.py
|-- plots.py
|-- utils.py
`-- tests/
```

## Installation

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Usage

Run a custom CLI case:

```bash
python main.py --support-type simply_supported --length 5 --point-load -10000:2.5
```

Run a custom case with a variable distributed load:

```bash
python main.py --support-type simply_supported --length 10 --udl "-250 - 20*x:2:6"
```

Launch the browser UI:

```bash
streamlit run app.py
```

Generate the three diagram images:

```bash
python main.py --support-type cantilever --length 3 --point-load -5000:3 --plot --output-dir generated_plots
```

Run the automated checks:

```bash
python -m unittest discover -s tests -v
```

## Notes on Conventions

- Vertical forces are signed.
- Use negative values for downward point loads.
- For distributed loads, enter a signed expression in `x`. Example downward load: `-250 - 20*x`.
- The parser accepts either `x` or `X` in the distributed-load expression.
- Applied moments are entered as positive clockwise values.
- The CLI reports absolute maximum moment and absolute maximum deflection for easy comparison with textbook results.
- Raw bending moment and deflection arrays keep their engineering sign, so cantilever downward-load cases show negative bending moments and negative deflection values internally.

## Validation

The test suite verifies:

- Streamlit helper functions for custom beam creation
- reactions for point-load and UDL cases
- applied moment reactions and bending-moment jumps
- zero end moments for simply supported beams
- maximum moment against reference formulas
- maximum deflection against reference formulas
- plot file generation

## Next Steps

Good next additions after this version:

- richer mixed-load examples and presets
- stress calculations from `M * c / I`
- torsion and axial loading utilities
- packaging and saved project files

## Status

This repository now contains both a CLI workflow and a Streamlit UI on top of the solver core, while still leaving room for broader Mechanics of Materials features in later versions.
