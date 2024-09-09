# Project scheduling instance parsers

This module provides parsers for various project scheduling benchmark instance formats.

## Data repositories

The following websites provide widely-used project scheduling benchmark instances.

- [PSPLIB](https://www.om-db.wi.tum.de/psplib/): PSPLIB contains different problem sets for various types of resource constrained project scheduling problems as well as optimal and heuristic solutions.

- [OR&S project database](https://www.projectmanagement.ugent.be/research/data): This is the research data website of the Operations Research and Scheduling (OR&S) Research group of the Faculty of Economics and Business Administration at Ghent University (Belgium). OR&S is very active in the field of project scheduling and has published instances for many problem variants.


## Instance formats and parsers

We have implemented parsers for the following instance formats:

- Patterson format (`parse_patterson.py`): The Patterson format is a commonly used format for RCPSP instances. See [this](http://www.p2engine.com/p2reader/patterson_format) website for more details.

- PSPLIB format (`parse_psplib.py`): The PSPLIB library has its own format which is used for RCPSP and MMRCPSP instances.

- MPLIB format (`parse_mplib.py`): OR&S contains multi-project RCPSP instances named `MPLIB` which can be parsed using this function.

All parsers return an instance of the `ProjectInstance` class, which is effectively a representation for the multi-project, multi-mode, resource-constrained project scheduling problem (MP-MM-RCPSP). 
