![PyJobShop logo](assets/images/logo.svg)

# PyJobShop

PyJobShop is a Python library for solving scheduling problems with constraint
programming. It currently supports the following scheduling problems:

- **Resource environments:** single machines, parallel machines, hybrid flow
  shops, open shops, job shops, flexible job shops, distributed shops,
  renewable resources and consumable resources.
- **Constraints:** release dates, deadlines, due dates, multiple modes,
  permutations, sequence-dependent setup times, no-wait, no-idle, blocking,
  breaks, optional task selection, and arbitrary precedence constraints.
- **Objective functions:** minimizing makespan, total flow time, number of
  tardy jobs, total tardiness, total earliness, maximum tardiness, and total
  setup times.

You can find PyJobShop on the Python Package Index under the name `pyjobshop`.
To install it, simply run:

```shell
pip install pyjobshop
```
