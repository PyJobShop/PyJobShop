Introduction to constraint programming
======================================

Constraint programming (CP) is a paradigm rooted in the fields of computer science and artificial intelligence for solving combinatorial problems.
In CP, problems are defined through variables with specific domains and constraints that describe the feasible values that variable can take.
The goal is to find a value for each variable such that all constraints are satisfied.
While CP traditionally focused at finding feasible solutions, it can also be used to solve optimization problems (that is, with an objective function) and has been very successful at doing so for applications such as scheduling and planning.

The way that CP solvers find a solution is by systematically searching through the space of feasible solutions, while reducing the set of solutions to explore through constraint propagation.
Constraint propagation is a method that reduces variable domains by reasoning on existing constraints, and propagating this information to other constraints, which in turn can result in more domain reductions.
Combined with search methods, such as branching or local search heuristics, the CP solver can navigates through the complex search space until the (best) solution is found or when a stopping criterion is met.

A key strength of CP is its expressive modeling language.
It provides logical constraints (such as AND, XOR, OR) and global constraints, which capture real-world structures and have strong propagation procedures that can substantially reduce variable domains.
An example of such global constraint is the `NoOverlap` constraint, which is crucial for machine scheduling problems, ensuring that processing tasks do not overlap with each other.
Compared to mixed-integer linear programming, which only allows for linear constraints as its, the expressive language of CP enables users to define many combinatorial problems compactly and solve them effectively.

Several popular tools and libraries are available for modeling and solving CP problems.
[Google OR-Tools CP-SAT](https://developers.google.com/optimization/cp/cp_solver) is an open-source solver with an extremely competitive CP solver, consistenly winning the yearly [MiniZinc challenge](https://www.minizinc.org/challenge/).
Another tool is [IBM ILOG CP Optimizer](https://www.ibm.com/products/ilog-cplex-optimization-studio/cplex-cp-optimizer), which is particularly geared towards industrial scheduling and planning tasks.
[MiniZinc](https://www.minizinc.org/) is a high-level constraint modeling language that allows you to easily model discrete optimization problems, and can be easily used with any CP solver.

For those interested in more details of CP, we refer to the following resources:

  * [CP-SAT Primer](https://github.com/d-krupke/cpsat-primer): a great introduction book to Google OR-Tools' CP-SAT solver. This book will help you to get familiar with modeling basics.
  * [Discrete Optimization Coursera](https://www.coursera.org/learn/discrete-optimization): module 3 covers constraint programming by Pascal van Hentenryck, who has made many great advancements in CP.
  * [Combinatorial Optimisation
and Constraint Programming by Pierre Flener](https://github.com/Pierre-Flener/Pierre-Flener.github.io/tree/main/courses/COCP/slides): course about constraint programming by Pierre Flener
