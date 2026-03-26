# 1D Beam Solver

Documentation-first Python project for a Mechanics of Materials beam analysis tool.

Repository: [MarkZaki/1D-Beam-Solver](https://github.com/MarkZaki/1D-Beam-Solver)

## Overview

This repository is intended to become a simple beam solver and visualizer built in Python for coursework and self-study in Mechanics of Materials.

The target project scope includes:

- beam reaction calculations
- shear force and bending moment diagrams
- deflection estimation for basic loading cases
- stress and strain related post-processing
- simple visualization of engineering results

## Current Status

This repository is currently in the setup and planning stage.

What exists now:

- a cleaned project README
- an action plan in [`plan.md`](./plan.md)
- initial git metadata for a Python project

What is not implemented yet:

- solver code
- plotting code
- a command-line or graphical interface
- tests and example problems

## Planned Capabilities

The first implementation version is expected to support:

- simply supported beams
- cantilever beams
- point loads
- uniformly distributed loads
- applied moments
- reaction force calculation
- shear force and bending moment evaluation
- deflection plotting for basic textbook cases

Future expansion may include:

- multiple load cases
- torsion and axial loading utilities
- stress calculations across different sections
- a simple UI built with a Python web or desktop framework

## Engineering Basis

The project will follow standard introductory Mechanics of Materials relationships and textbook beam formulas.

Example reference formulas:

- Simply supported beam with a center point load: `y_max = F * L^3 / (48 * E * I)`
- Cantilever beam with an end point load: `y_max = F * L^3 / (3 * E * I)`

These formulas are included here as project intent, not as implemented functionality yet.

## Planned Project Structure

The repository is expected to grow into a structure close to:

```text
1D-Beam-Solver/
|-- README.md
|-- plan.md
|-- main.py
|-- beam.py
|-- solver.py
|-- plots.py
|-- utils.py
`-- tests/
```

File names may change during implementation if a better module layout becomes clear.

## Requirements

There are no runtime requirements yet because the solver has not been implemented.

Planned Python stack:

- Python 3.11 or newer
- `numpy` for numerical calculations
- `matplotlib` for plotting
- optionally `streamlit` for a simple interface

## Getting Started

To clone the repository:

```bash
git clone https://github.com/MarkZaki/1D-Beam-Solver.git
cd 1D-Beam-Solver
```

Suggested local setup for future development:

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Current recommended workflow:

1. Read this README.
2. Review the action list in [`plan.md`](./plan.md).
3. Create the initial Python modules and tests.
4. Add example beam cases and validate the results.

## Repository Link

- GitHub: [https://github.com/MarkZaki/1D-Beam-Solver](https://github.com/MarkZaki/1D-Beam-Solver)

## Next Steps

- scaffold the first Python modules
- define the beam and load data structures
- implement reaction, shear, and moment calculations
- add plotting utilities
- create sample problems and tests

## Notes

This README is intentionally accurate to the current repository state. As code is added, the documentation should be updated to reflect the real implementation rather than the intended design alone.
