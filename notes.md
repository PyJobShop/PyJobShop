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


- In Naderi 2023, they only use cumulative constraints for HFSP with identical machines.
