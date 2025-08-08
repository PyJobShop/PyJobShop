# Redundant cumulative constraints for machines

Machines use no-overlap constraints.
In some special cases, like hybrid flow shops, we can reformulate the machines using cumulative constraints to enhance propagation.

The idea is as follows:
- Create a graph $G$ whose nodes are defined by all machines, $V=M$.
- For each task, find the machines that it could be assigned to.
    - For each pair of machines, create an edge in the graph $(u, v)$.

- Identify the connected components of $G$, defined by $C_1, \dots, C_k$.


What is the meaning behind a connected component? One components defines all machines that are could be required at the same time by a set of tasks. Which tasks exactly? Precisely the tasks that could require at least one of these machines. Because the tasks often exceed the machines, this can be propagated with a cumulative constraint:
- cumulative(tasks, 1) <= len(components)


- In Naderi 2023, they only use cumulative constraints for HFSP with identical machines. In that case, you don't need to add noOverlap constraints, because the pulse constraints always allow for a perfect 1-to-1 mapping between task and mode variables (each mode variable has the same duration). When the machines are not identical, then this no longer works because this 1-to-1 mapping no longer holds -- we need to add no overlap per machine as well.
