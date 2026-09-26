"""Graph construction and causal graph utilities."""

import re
from collections import Counter
from collections.abc import Iterable

from igraph import Graph, plot
from igraph.drawing import Plot

# Define some useful graph functions


def plotGraph(g: Graph, name: str | None = None) -> Plot:
    """Plot a graph, saving `name.png` when a name is given; requires Cairo."""

    color_dict = {0: "blue", 1: "#008833"}
    visual_style: dict[str, object] = {}
    visual_style["vertex_label_dist"] = 2
    visual_style["vertex_size"] = 20
    visual_style["vertex_label"] = g.vs["name"]
    visual_style["edge_width"] = [1 + 1.5 * (1 - abs(val)) for val in g.es["confounding"]]
    visual_style["edge_color"] = [color_dict[abs(val)] for val in g.es["confounding"]]
    visual_style["edge_curved"] = [(val) * 0.2 for val in g.es["confounding"]]
    visual_style["layout"] = g.layout("circle")
    visual_style["bbox"] = (300, 300)
    visual_style["margin"] = 40
    if name is not None:
        return plot(g, name + ".png", **visual_style)
    return plot(g, **visual_style)


def _typed_graph(g: Graph) -> Graph:
    """Treat edges without type metadata as visible arrows on a copy."""
    if "confounding" in g.edge_attributes():
        return g
    typed = g.copy()
    typed.es["confounding"] = [0] * typed.ecount()
    return typed


def get_directed_bidirected_graphs(g: Graph) -> tuple[Graph, Graph]:
    """Split visible arrows and bidirected arcs without changing their attributes."""
    g = _typed_graph(g)
    directed = [edge.index for edge in g.es if edge["confounding"] == 0]
    bidirected = [edge.index for edge in g.es if edge["confounding"] != 0]
    return (
        g.subgraph_edges(directed, delete_vertices=False),
        g.subgraph_edges(bidirected, delete_vertices=False),
    )


def get_C_components(g: Graph) -> list[Graph]:
    """Return original induced subgraphs grouped by bidirected connectivity."""
    g = _typed_graph(g)
    _g_dir, g_bidir = get_directed_bidirected_graphs(g)
    return [g.induced_subgraph(vertices) for vertices in g_bidir.connected_components(mode="weak")]


def get_vertices_no_parents(g: Graph) -> set[str]:
    """Function that returns the set of vertices without parents"""
    directed, _bidirected = get_directed_bidirected_graphs(g)
    return {
        name
        for name, degree in zip(directed.vs["name"], directed.degree(mode="in"), strict=True)
        if degree == 0
    }


def get_topological_ordering(g: Graph) -> list[str]:
    """Function that returns the ordering of the vertices of a graph"""

    g_dir, _g_bidir = get_directed_bidirected_graphs(g)
    return [g_dir.vs[index]["name"] for index in g_dir.topological_sorting()]


def get_previous_order(v: str, possible: set[str], ordering: list[str]) -> set[str]:
    """Function that returns all previous vertices of a initial vertex from
    a possible set of vertices and an ordernig of the graph"""

    return set(ordering[: ordering.index(v)]).intersection(possible)


def get_ancestors(g: Graph, v_name: str | set[str]) -> set[str]:
    """Function that returns a set containing all ancestors of a vertex,
    including itself"""

    if not g.is_dag():
        raise ValueError("Graph contains a cycle")
    ancestors: list[str] = []
    if isinstance(v_name, set):
        for e in v_name:
            ancestors += get_ancestors(g, e)
    else:
        ancestors = [v_name]
        parents = [v_name]
        checked = [v_name]
        while len(parents) > 0:
            name_vertex = parents.pop(0)
            checked.append(name_vertex)
            new_neighbors = g.neighbors(g.vs.find(name=name_vertex), mode="in")
            for i in range(len(new_neighbors)):
                if g.vs[new_neighbors[i]]["name"] not in ancestors:
                    ancestors.append(g.vs[new_neighbors[i]]["name"])
                if (
                    g.vs[new_neighbors[i]]["name"] not in parents
                    and g.vs[new_neighbors[i]]["name"] not in checked
                ):
                    parents.append(g.vs[new_neighbors[i]]["name"])
    return set(ancestors)


def get_descendants(g: Graph, v_name: str | set[str]) -> set[str]:
    """Function that returns a set containing all descendants of a vertex,
    including itself"""

    if not g.is_dag():
        raise ValueError("Graph contains a cycle")
    descendants: list[str] = []
    if isinstance(v_name, set):
        for e in v_name:
            descendants += get_descendants(g, e)
    else:
        descendants = [v_name]
        children = [v_name]
        checked = [v_name]
        while len(children) > 0:
            name_vertex = children.pop(0)
            checked.append(name_vertex)
            new_neighbors = g.neighbors(g.vs.find(name=name_vertex), mode="out")
            for i in range(len(new_neighbors)):
                if g.vs[new_neighbors[i]]["name"] not in descendants:
                    descendants.append(g.vs[new_neighbors[i]]["name"])
                if (
                    g.vs[new_neighbors[i]]["name"] not in children
                    and g.vs[new_neighbors[i]]["name"] not in checked
                ):
                    children.append(g.vs[new_neighbors[i]]["name"])
    return set(descendants)


def graphs_are_equal(g1: Graph, g2: Graph) -> bool:
    """Function that checks if two given graphs are equal"""

    return check_subgraph(g1, g2) and check_subgraph(g2, g1)


def check_subcomponent(subcomponent: Graph, components: Iterable[Graph]) -> bool:
    """Function that checks if a graph is part of a set of graphs"""
    names = set(subcomponent.vs["name"])
    return any(names == set(g.vs["name"]) for g in components)


def _causal_edge_counts(g: Graph) -> Counter[tuple[bool, str, str]]:
    """Count visible arrows and encoded bidirected halves by causal edge type."""
    counts: Counter[tuple[bool, str, str]] = Counter()
    for edge in _typed_graph(g).es:
        source = edge.source_vertex["name"]
        target = edge.target_vertex["name"]
        bidirected = edge["confounding"] != 0
        if bidirected:
            source, target = sorted((source, target))
        counts[(bidirected, source, target)] += 1
    return counts


def check_subgraph(g1: Graph, g2: Graph) -> bool:
    """Function that checks ig a graph g1 is a subgraph of g2"""

    # Check that g1 is included in g2.
    if not set(g1.vs["name"]).issubset(g2.vs["name"]):
        return False
    # Check edge multiplicity and causal type.
    return not (_causal_edge_counts(g1) - _causal_edge_counts(g2))


def createGraph(list_edges_string: Iterable[str], verbose: bool = False) -> Graph:
    """Build a causal graph from `->`, `<-`, and `<->` edge strings."""

    vertices: list[str] = []
    edges = []
    confounding = []
    for edge in list_edges_string:
        conf = 0
        parts = re.split(r"(<->|->|<-)", edge)
        if len(parts) != 3 or not parts[0].strip() or not parts[2].strip():
            raise ValueError(f"Invalid edge: {edge!r}")
        vertex1, arrow, vertex2 = parts
        vertex1, vertex2 = vertex1.strip(), vertex2.strip()
        index1, index2 = -1, -1
        if vertex1 in vertices:
            index1 = vertices.index(vertex1)
        else:
            index1 = len(vertices)
            vertices.append(vertex1)
        if vertex2 in vertices:
            index2 = vertices.index(vertex2)
        else:
            index2 = len(vertices)
            vertices.append(vertex2)
        if arrow[0] == "<":
            conf += 1
            edges.append((index2, index1))
        if arrow[-1] == ">":
            conf += 1
            edges.append((index1, index2))
        # confounding edge
        if conf == 2:
            confounding.append(1)
            confounding.append(-1)
        else:
            confounding.append(0)

    if verbose:
        print(vertices)
    if verbose:
        print(edges)
    if verbose:
        print(confounding)
    g = Graph(vertex_attrs={"name": vertices}, edges=edges, directed=True)

    g.es["confounding"] = confounding
    return g


def to_R_notation(edges: list[str]) -> tuple[str, int, int]:
    """Convert edge strings to R causaleffect notation, modifying the input list."""

    # ["X->Y", "X<-A", "X<-E", "X<-V", "Y<-A", "Y<-H_1", "Y<-G", "Y<-V",
    #  "Y<-H", "Y<-E", "H->V", "V->E"]
    bidirected = []
    final_bidirected = []
    for i, e in enumerate(edges):
        e = e.replace("<", "+")
        e = e.replace(">", "+")
        edges[i] = e
        if e.count("+") == 2:
            bidirected.append(e)
    directed = [e for e in edges if e not in bidirected]

    for e in bidirected:
        one = e.replace("+", "", 1)
        two = e[::-1].replace("+", "", 1)[::-1]
        final_bidirected.append(one)
        final_bidirected.append(two)

    out = ", ".join(directed + final_bidirected)
    return out, len(directed) + 1, len(directed) + len(final_bidirected)


def unobserved_graph(g: Graph) -> Graph:
    """Constructs a causal diagram where confounded variables have explicit unmeasurable nodes
    from a DAG of bidirected edges"""

    G = _typed_graph(g).copy()
    hidden = [edge for edge in G.es if edge["confounding"] != 0]
    pairs = sorted({tuple(sorted(edge.tuple)) for edge in hidden})
    names = set(G.vs["name"])
    next_index = 1
    for source, target in pairs:
        while f"U_{next_index}" in names:
            next_index += 1
        name = f"U_{next_index}"
        names.add(name)
        next_index += 1
        G.add_vertex(name=name)
        G.add_edges([(G.vcount() - 1, source), (G.vcount() - 1, target)])
    G.delete_edges([edge.index for edge in hidden])
    G.es["confounding"] = [0] * G.ecount()
    return G


def dSep(G: Graph, Y: set[str], node: str, cond: set[str], verbose: bool = False) -> bool:
    """Check whether node and Y are d-separated by cond in G."""

    if verbose:
        print("dSep: dSep of node:", node, " to set: ", Y)
    for y in Y:
        if verbose:
            print("dSep: Path from ", y, " to ", node)
        paths = G.get_all_simple_paths(
            v=G.vs.find(name_eq=node), to=G.vs.find(name_eq=y), mode="ALL"
        )
        if verbose:
            print("dSep: All possible paths: ", paths)
        for p in paths:
            if verbose:
                p_name = []
                for i in p:
                    p_name.append(G.vs[i]["name"])
                print("dSep: Path:", p, p_name)
            if not is_path_d_separated(G, p, cond, verbose=verbose):
                return False
    # If all paths are d-separated, return True
    return True


def is_path_d_separated(G: Graph, p: list[int], cond: set[str], verbose: bool = False) -> bool:
    """Checks if a path is d-separated, given the whole graph G and the measured variables cond"""

    if verbose:
        print("is_path_d_separated: Path ", p, "Conditional: ", cond)
    if G.vs[p[0]]["name"] in cond or G.vs[p[-1]]["name"] in cond:
        raise ValueError("Source or target nodes in conditional d-separation path")
    for i in range(len(p) - 2):
        e1, e2 = "", ""
        if len(G.es.select(_source=p[i]).select(_target=p[i + 1])):
            if verbose:
                print(G.vs[p[i]]["name"], "->", G.vs[p[i + 1]]["name"])
            e1 = "r"
        if len(G.es.select(_source=p[i + 1]).select(_target=p[i])):
            if verbose:
                print(G.vs[p[i]]["name"], "<-", G.vs[p[i + 1]]["name"])
            e1 = "b" if e1 == "r" else "l"
        if len(G.es.select(_source=p[i + 1]).select(_target=p[i + 2])):
            if verbose:
                print(G.vs[p[i + 1]]["name"], "->", G.vs[p[i + 2]]["name"])
            e2 = "r"
        if len(G.es.select(_source=p[i + 2]).select(_target=p[i + 1])):
            if verbose:
                print(G.vs[p[i + 1]]["name"], "<-", G.vs[p[i + 2]]["name"])
            e2 = "b" if e2 == "r" else "l"

        if (
            (e1 == "r" and e2 == "r")
            or (e1 == "l" and e2 == "l")
            or (e1 == "l" and e2 == "r")
            or (e1 == "l" and e2 == "b")
            or (e1 == "b" and e2 == "r")
        ) and G.vs[p[i + 1]]["name"] in cond:  # -> -> // <- <- // <- -> // <- <-> // <-> ->
            if verbose:
                print(
                    "is_path_d_separated: Chain or Fork:",
                    G.vs[p[i]]["name"],
                    e1,
                    G.vs[p[i + 1]]["name"],
                    e2,
                    G.vs[p[i + 2]]["name"],
                )
            return True

        if (
            (e1 == "r" and e2 == "l")
            or (e1 == "r" and e2 == "b")
            or (e1 == "b" and e2 == "l")
            or (e1 == "b" and e2 == "b")
        ):  # -> <- // -> <-> // <-> <- // <-> <->
            G_dir, _G_bidir = get_directed_bidirected_graphs(G)
            if len(get_descendants(G_dir, G.vs[p[i + 1]]["name"]).intersection(cond)) == 0:
                if verbose:
                    print(
                        "is_path_d_separated: Collider:",
                        G.vs[p[i]]["name"],
                        e1,
                        G.vs[p[i + 1]]["name"],
                        e2,
                        G.vs[p[i + 2]]["name"],
                    )
                return True
    if verbose:
        print("is_path_d_separated: d-connected path ", p, "Conditional: ", cond)
    return False


def printGraph(G: Graph) -> tuple[list[str], list[str]]:
    """Return the node names and directed or bidirected edge strings of a graph."""

    edges = []
    confounded = []
    for edge in G.es:
        if edge["confounding"] == -1:
            confounded.append(edge.source_vertex["name"] + "<->" + edge.target_vertex["name"])
        elif edge["confounding"] == 1:
            confounded.append(edge.target_vertex["name"] + "<->" + edge.source_vertex["name"])
        else:
            edges.append(edge.source_vertex["name"] + "->" + edge.target_vertex["name"])
    confounded = list(set(confounded))
    nodes = G.vs["name"]
    return nodes, edges + confounded
