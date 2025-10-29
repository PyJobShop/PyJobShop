# CP-SAT Solver Documentation - Table of Contents (Python Only)

This is a comprehensive checklist for OR-Tools CP-SAT solver documentation, focusing exclusively on Python implementations.
Source: https://github.com/google/or-tools/tree/main/ortools/sat/docs

---

## 🔢 Integer Arithmetic

- [ ] **integer_arithmetic.md** - Integer variables and linear constraints

  ### Integer Variables
  - [ ] Interval domain
  - [ ] Non-contiguous domain
  - [ ] Boolean variables
  - [ ] Other methods

  ### Linear Constraints
  - [ ] Python linear constraints and expressions
  - [ ] Generic linear constraint
  - [ ] Limitations

  ### Examples
  - [ ] **Rabbits and Pheasants** (Python)
  - [ ] **Earliness-Tardiness Cost Function** (Python)
  - [ ] **Step Function** (Python)

  ### Advanced Topics
  - [x] Product of a Boolean and an Integer Variable (Python)
  - [ ] Scanning the Domain of Variables (Python)

---

## 📅 Scheduling

- [ ] **scheduling.md** - Interval variables and scheduling constraints

  ### Core Concepts
  - [ ] Introduction to scheduling in Operations Research
  - [ ] **Interval Variables** (Python)
  - [ ] **Optional Intervals** (Python)
  - [ ] **Time Relations Between Intervals** (Python)

  ### Resource Constraints
  - [ ] **NoOverlap Constraint** (Python)
  - [ ] **Cumulative Constraint** with min/max capacity profile (Python)
  - [x] **Alternative Resources** for one interval

  ### Task Sequencing
  - [ ] **Ranking Tasks** in a disjunctive resource (Python)
  - [ ] **Ranking Tasks** using a circuit constraint (Python)

  ### Advanced Scheduling
  - [ ] **Intervals Spanning Over Breaks** in calendar (Python)
  - [ ] **Detecting Interval Overlaps** (Python)
  - [ ] **Transitions** in NoOverlap constraint (Python)
  - [ ] **Managing Sequences** in NoOverlap constraint (Python)

---

## 🔗 Channeling Constraints

- [ ] **channeling.md** - Connecting different variable types

  ### If-Then-Else Expressions
  - [x] Python implementation

  ### Index of First True Boolean
  - [ ] Python implementation

  ### Bin-Packing Problem
  - [ ] Python implementation

---

## ⚙️ Using the Solver

- [ ] **solver.md** - Solver configuration and control

  ### Solver Parameters
  - [ ] **Changing solver parameters**
    - [ ] Time limit (Python)

  ### Solution Handling
  - [ ] **Printing intermediate solutions** (Python)
  - [ ] **Searching for all solutions** (Python)
  - [ ] **Stopping search early** (Python)

---

## 🛠️ Model Manipulation

- [ ] **model.md** - Working with CP models

  ### Model Structure
  - [ ] Introduction to CpModel class
  - [ ] Protocol buffers and modeling objects
  - [ ] Python method references

  ### Solution Hinting
  - [ ] Python implementation

  ### Model Copy
  - [ ] Python implementation

---

## 🐛 Troubleshooting

- [ ] **troubleshooting.md** - Debugging and performance tuning

  ### Debugging
  - [ ] **Enable logging** (`log_search_progress`)
  - [ ] **Exporting the model** (text and binary formats)

  ### Performance Tuning
  - [ ] **Improving performance with multiple workers**
    - [ ] 8 workers (minimum for parallel search)
    - [ ] 16 workers (adds continuous probing)
    - [ ] 24 workers (includes dual subsolvers)
    - [ ] 32+ workers (additional LNS and solution subsolvers)

  ### Infeasibility
  - [ ] **Solve status** understanding
    - [ ] UNKNOWN
    - [ ] MODEL_INVALID
    - [ ] FEASIBLE
    - [ ] INFEASIBLE
    - [ ] OPTIMAL
  - [ ] **Debugging infeasible models**
  - [ ] **Using assumptions to explain infeasibility** (Python)

---

## 📖 Additional Resources

- [ ] Official OR-Tools documentation: https://developers.google.com/optimization
- [ ] CP-SAT GitHub repository: https://github.com/google/or-tools
- [ ] CP-SAT Python API reference: https://or-tools.github.io/docs/pdoc/ortools/sat/python/cp_model.html
- [ ] CP-SAT Primer: https://github.com/d-krupke/cpsat-primer
- [ ] Research papers on CP-SAT solver
