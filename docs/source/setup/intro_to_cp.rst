Introduction to constraint programming
======================================

Constraint programming (CP) is a paradigm rooted in the fields of computer science and artificial intelligence for solving combinatorial problems.
In CP, problems are defined through variables with specific domains and constraints that describe the feasible values that variables can take.
The goal is to find a value for each variable such that all constraints are satisfied.
While CP traditionally focused on finding feasible solutions, it can also be used to solve optimization problems (that is, with an objective function) and has been very successful at doing so for applications such as scheduling and planning.

The way that CP solvers find a solution is by systematically searching through the space of feasible solutions, while reducing the set of solutions to explore through constraint propagation.
Constraint propagation is a method that reduces variable domains by reasoning on existing constraints and propagating this information to other constraints, which in turn can result in more domain reductions.
Combined with search methods, such as branching or local search heuristics, the CP solver can navigate through the complex search space until the (best) solution is found or when a stopping criterion is met.

A key strength of CP is its expressive modeling language.
It provides logical constraints (such as AND, XOR, OR) and global constraints, which capture real-world structures and have strong propagation procedures that can substantially reduce variable domains.
An example of such a global constraint is the `NoOverlap` constraint, which is crucial for machine scheduling problems, ensuring that processing tasks do not overlap with each other.
Compared to mixed-integer linear programming, which only allows modeling using linear constraints, the expressive language of CP enables users to define many combinatorial problems compactly and solve them effectively.

.. example::

  .. figure:: ../assets/sudoku.png
    :alt: A 9x9 Sudoku puzzle.
    :figwidth: 50%

  A Sudoku puzzle is a simple example to explain the basics of CP.

  1. **Variables:** Each cell in the 9x9 Sudoku grid is treated as a variable, with possible values ranging from 1 to 9.

  2. **Constraints:**
     Rules are applied to these variables, including:

     * Each row must contain unique numbers.
     * Each column must contain unique numbers.
     * Each of the nine 3x3 subgrids (or boxes) must also contain unique numbers.
     * Finally, the pre-filled cell restricts its corresponding variable to a specific value.

  3. **Propagation:** As you reason through the constraints, you reduce the domains of variables, and this information can be used to further narrow down possibilities without guessing.

  4. **Search:** When reasoning with constraints alone cannot determine the remaining values, you may have to make educated guesses. If a guess leads to a contradiction, you backtrack to eliminate that option and try a different one.

  5. **Solution:** A solution is found when all cells are filled in such a way that all constraints are satisfied.


Several popular tools and libraries are available for modeling and solving CP problems.

* `Google OR-Tools CP-SAT <https://developers.google.com/optimization/cp/cp_solver>`_ is an open-source solver with an extremely competitive CP solver, consistently winning the yearly `MiniZinc challenge <https://www.minizinc.org/challenge/>`_.
* `IBM ILOG CP Optimizer <https://www.ibm.com/products/ilog-cplex-optimization-studio/cplex-cp-optimizer>`_ is particularly geared towards industrial scheduling and planning tasks.
* `MiniZinc <https://www.minizinc.org/>`_ is a high-level constraint modeling language that allows you to easily model discrete optimization problems and can be easily used with any CP solver.

For those interested in more details of CP, we refer to the following resources:

* `CP-SAT Primer <https://github.com/d-krupke/cpsat-primer>`_: a great introduction book to Google OR-Tools' CP-SAT solver. This book will help you to get familiar with modeling basics.
* `Discrete Optimization Coursera <https://www.coursera.org/learn/discrete-optimization>`_: module 3 covers constraint programming by Pascal van Hentenryck, who has made many great advancements in CP.
* `Combinatorial Optimisation and Constraint Programming by Pierre Flener <https://github.com/Pierre-Flener/Pierre-Flener.github.io/tree/main/courses/COCP/slides>`_: course about constraint programming by Pierre Flener.
