from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Union

import matplotlib.pyplot as plt
import networkx as nx
from psplib import ProjectInstance, parse


@dataclass
class AlternativeSubgraph:
    """
    Represents a single alternative subgraph in an ASLIB instance.

    Parameters
    ----------
    branches
        A list of branches in the subgraph. Each branch is a list of activity
        indices that are part of the branch.
    """

    branches: list[list[int]]


def parse_aslib(loc: Union[str, Path]) -> list[AlternativeSubgraph]:
    """
    Parses an ASLIB-formatted instance from a file. This format is used for
    RCPSP instances with alternative subgraphs.

    Note
    ----
    This only parses the "b" files from the ASLIB instance. The "a" files
    are parsed as Patterson-formatted instances.

    Parameters
    ----------
    loc
        The location of the instance.

    Returns
    -------
    list[AlternativeSubgraph]
        The alternative subgraphs data.
    """
    with open(loc, "r") as fh:
        lines = iter(line.strip() for line in fh.readlines() if line.strip())

    pct_flex, pct_nested, pct_linked = map(float, next(lines).split())
    num_subgraphs = int(next(lines))
    total_branches = 1  # first branch is always the dummy branch
    subgraphs = []

    for _ in range(num_subgraphs):
        num_branches, *branch_idcs = map(int, next(lines).split())
        total_branches += num_branches
        branch_idcs = [idx - 1 for idx in branch_idcs]
        subgraphs.append(branch_idcs)

    branches: list[list[int]] = [[] for _ in range(total_branches)]
    for activity, line in enumerate(lines):
        num_braches, *branch_idcs = map(int, line.split())
        for idx in branch_idcs:
            branches[idx - 1].append(activity)

    result = [AlternativeSubgraph([branches[0]])]
    result += [
        AlternativeSubgraph([branches[idx] for idx in branch_idcs])
        for branch_idcs in subgraphs
    ]
    return result


def to_networkx_graph(instance: ProjectInstance) -> nx.DiGraph:
    """
    Converts a ProjectInstance to a networkX DiGraph.
    """
    G = nx.DiGraph()

    for idx, activity in enumerate(instance.activities):
        G.add_node(idx)
        for succ in activity.successors:
            G.add_edge(idx, succ)

    return G


def plot_graph(G: nx.DiGraph, subgraphs: list[AlternativeSubgraph]):
    """
    Plot the graph using networkx with multipartite layout and coloring
    nodes based on branch membership.
    """

    assert nx.is_directed_acyclic_graph(G)

    for layer, nodes in enumerate(nx.topological_generations(G)):
        for node in nodes:
            G.nodes[node]["layer"] = layer

    pos = nx.multipartite_layout(G, subset_key="layer")
    colors = color_nodes(G, subgraphs)

    fig, ax = plt.subplots()
    nx.draw_networkx(
        G,
        pos=pos,
        ax=ax,
        node_color=colors,
        cmap=plt.cm.get_cmap("tab10"),
    )
    ax.set_title("DAG layout in topological order")
    fig.tight_layout()
    plt.show()


def color_nodes(G, graphs):
    """
    Assign colors to nodes based on their branch membership.
    """
    colors = []
    branches = [branch for graph in graphs for branch in graph.branches]
    for node in G.nodes:
        for idx, branch in enumerate(branches):
            if node in branch:
                colors.append(idx)
                break
        else:
            colors.append(-1)
    return colors


def write_rcpsp_ps(loc, instance, tasks):
    """
    Writes instance in "van der Beek (2024)" format.
    """
    with open(loc, "w") as fh:

        def write(*args):
            fh.write(" ".join(map(str, args)) + "\n")

        write(instance.num_activities, instance.num_resources, 0)
        write(*[res.capacity for res in instance.resources])

        fixed = [idx for idx, task in enumerate(tasks) if not task.optional]
        write(*fixed)

        for task in tasks:
            write()
            write(*([task.duration] + task.demands))

            groups_line = [len(task.groups)]
            for group in task.groups:
                groups_line.append(len(group))
                groups_line.extend(group)

            write(*groups_line)
            write(len(task.successors), *task.successors)


@dataclass
class VDBTask:
    duration: int
    demands: list[int]
    successors: list[int]
    optional: bool
    groups: list[list[int]]


def subgraphs2vdbtasks(
    instance: ProjectInstance, subgraphs: list[AlternativeSubgraph]
) -> list[VDBTask]:
    """
    Converts the RCPSP-AS instance to a list of tasks for VanDerBeek-format.
    """
    G = to_networkx_graph(instance)
    top_gen = nx.topological_generations(G)
    order = [node for nodes in top_gen for node in nodes]

    fixed, optional = subgraphs[0], subgraphs[1:]
    fixed_activities = fixed.branches[0]

    all_heads = []  # TODO what are heads?
    groups = defaultdict(list)

    for graph in optional:
        heads = [min(branch, key=order.index) for branch in graph.branches]
        preds = [(u, v) for u, v in G.edges if v in heads]
        source = {u for (u, _) in preds}
        assert len(source) == 1

        all_heads.extend(heads)
        groups[source.pop()].append(heads)

    for u, v in G.edges:
        if v not in all_heads:
            groups[u].append([v])

    tasks = []
    for idx, activity in enumerate(instance.activities):
        duration = activity.modes[0].duration
        demands = activity.modes[0].demands
        successors = activity.successors
        task = VDBTask(
            duration,
            demands,
            successors,
            idx not in fixed_activities,
            groups[idx],
        )
        tasks.append(task)

    for task in tasks:
        # In RCPSP-AS, all timing successors are also selection successors.
        select_succ = [succ for group in task.groups for succ in group]
        assert set(select_succ) == set(task.successors)

    return tasks


if __name__ == "__main__":
    for instance_idx in range(1010):
        instance_loc = f"tmp/ASLIB/ASLIB0/aslib0_{instance_idx}a.RCP"
        instance = parse(instance_loc, instance_format="patterson")
        subgraphs = parse_aslib(instance_loc.replace("a.RCP", "b.RCP"))
        tasks = subgraphs2vdbtasks(instance, subgraphs)

        loc = f"tmp/rcpsp-ps/instances/ASLIB0/aslib0_{instance_idx}a.txt"
        write_rcpsp_ps(loc, instance, tasks)
        print(instance_idx)
