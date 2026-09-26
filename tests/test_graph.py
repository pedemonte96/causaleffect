"""Tests for graph construction, traversal, and separation."""

import pytest

from causaleffect import graph


def test_edge_views_separate_visible_and_latent_arcs() -> None:
    """Directed and confounded views preserve the intended edges."""
    g = graph.createGraph(["X<->Y", "Z->Y"])
    directed, bidirected = graph.get_directed_bidirected_graphs(g)

    assert graph.printGraph(directed)[1] == ["Z->Y"]
    assert graph.printGraph(bidirected)[1] == ["X<->Y"]


def test_opposite_directed_edges_do_not_become_confounding() -> None:
    """A directed cycle remains in the directed graph view."""
    g = graph.createGraph(["X->Y", "Y->X"])
    directed, bidirected = graph.get_directed_bidirected_graphs(g)

    assert set(graph.printGraph(directed)[1]) == {"X->Y", "Y->X"}
    assert not bidirected.es


@pytest.mark.parametrize(
    "edges",
    [["X->Y", "X->Y"], ["X->Y", "X->Y", "Y->X"]],
    ids=["duplicate", "duplicate-with-reverse"],
)
def test_parallel_visible_edges_keep_their_direction(edges: list[str]) -> None:
    """Parallel visible arrows neither become latent arcs nor create negative edge counts."""
    g = graph.createGraph(edges)

    directed, bidirected = graph.get_directed_bidirected_graphs(g)

    assert directed.ecount() == len(edges)
    assert not bidirected.es


def test_visible_self_loop_stays_directed() -> None:
    """A self-loop is a visible cycle rather than a latent arc."""
    directed, bidirected = graph.get_directed_bidirected_graphs(graph.createGraph(["X->X"]))

    assert directed.ecount() == 1
    assert not directed.is_dag()
    assert not bidirected.es


def test_repeated_bidirected_arc_keeps_both_encoded_pairs() -> None:
    """Repeated latent arcs do not create spurious visible arrows."""
    directed, bidirected = graph.get_directed_bidirected_graphs(
        graph.createGraph(["X<->Y", "X<->Y"])
    )

    assert not directed.es
    assert bidirected.ecount() == 4
    assert sorted(bidirected.es["confounding"]) == [-1, -1, 1, 1]


def test_edge_views_preserve_vertex_and_edge_attributes() -> None:
    """Splitting a bow retains the original edge types and graph attributes."""
    g = graph.createGraph(["X->Y", "X<->Y"])
    g.vs["kind"] = ["exposure", "outcome"]
    g.es["weight"] = [3, 5, 7]

    directed, bidirected = graph.get_directed_bidirected_graphs(g)

    assert directed.vs["kind"] == bidirected.vs["kind"] == g.vs["kind"]
    assert directed.es["weight"] == [3]
    assert sorted(bidirected.es["weight"]) == [5, 7]
    assert directed.es["confounding"] == [0]
    assert sorted(bidirected.es["confounding"]) == [-1, 1]


def test_components_retain_internal_arrows_and_attributes() -> None:
    """A C-component is an induced subgraph with valid edge metadata."""
    g = graph.createGraph(["A<->B", "A->B", "B->C"])
    g.vs["kind"] = ["a", "b", "c"]
    g.es["weight"] = [2, 3, 5, 7]

    components = {frozenset(c.vs["name"]): c for c in graph.get_C_components(g)}
    confounded = components[frozenset({"A", "B"})]

    assert set(components) == {frozenset({"A", "B"}), frozenset({"C"})}
    assert confounded.vs["kind"] == ["a", "b"]
    assert sorted(confounded.es["confounding"]) == [-1, 0, 1]
    assert sorted(confounded.es["weight"]) == [2, 3, 5]


def test_ordering_helpers_follow_visible_arrows() -> None:
    """Topological order and its prefix follow visible arrows."""
    g = graph.createGraph(["X->Y", "Y->Z"])

    assert graph.get_topological_ordering(g) == ["X", "Y", "Z"]
    assert graph.get_previous_order("Z", {"X", "Z"}, ["X", "Y", "Z"]) == {"X"}


def test_ancestors_include_starting_vertices() -> None:
    """Ancestors include their starting vertex or vertex set."""
    g = graph.createGraph(["X->Y", "Y->Z"])

    assert graph.get_ancestors(g, "Z") == {"X", "Y", "Z"}
    assert graph.get_ancestors(g, {"Y", "Z"}) == {"X", "Y", "Z"}


def test_descendants_include_starting_vertices_and_converging_paths() -> None:
    """Descendants include roots and visit converging paths once."""
    g = graph.createGraph(["X->Y", "Y->Z"])

    assert graph.get_descendants(g, "X") == {"X", "Y", "Z"}
    assert graph.get_descendants(g, {"X", "Y"}) == {"X", "Y", "Z"}
    diamond = graph.createGraph(["X->A", "X->B", "A->Y", "B->Y"])
    assert graph.get_descendants(diamond, "X") == {"X", "A", "B", "Y"}


def test_ancestry_traversal_rejects_cycles() -> None:
    """Ancestor and descendant traversal reject directed cycles."""
    cycle = graph.createGraph(["X->Y", "Y->X"])
    with pytest.raises(ValueError, match="cycle"):
        graph.get_ancestors(cycle, "X")
    with pytest.raises(ValueError, match="cycle"):
        graph.get_descendants(cycle, "X")


def test_graph_equality_requires_matching_vertices_and_edges() -> None:
    """Equal graphs have the same vertices and causal edges."""
    full = graph.createGraph(["X->Y", "Y->Z"])

    assert graph.graphs_are_equal(full, full.copy())
    assert not graph.graphs_are_equal(full, graph.createGraph(["X->Y"]))
    assert not graph.graphs_are_equal(full, graph.createGraph(["X->Z", "Y->Z"]))


def test_subgraph_comparison_checks_vertices_and_edges() -> None:
    """A subgraph cannot require missing vertices or edges."""
    full = graph.createGraph(["X->Y", "Y->Z"])

    assert not graph.check_subgraph(graph.createGraph(["W->X"]), full)
    assert not graph.check_subgraph(graph.createGraph(["X->Y", "Y->Z", "X->Z"]), full)


def test_subgraph_comparison_counts_parallel_edges() -> None:
    """One visible arrow cannot contain two copies of the same arrow."""
    required = graph.createGraph(["A->B", "A->B"])
    available = graph.createGraph(["A->B", "A->C"])

    assert not graph.check_subgraph(required, available)


def test_graph_equality_distinguishes_visible_and_latent_edges() -> None:
    """Reciprocal visible arrows are not the same causal edge as confounding."""
    confounded = graph.createGraph(["A<->B"])
    visible = graph.createGraph(["A->B", "B->A"])

    assert not graph.graphs_are_equal(confounded, visible)


def test_component_membership_uses_vertices() -> None:
    """An internal visible arrow does not change C-component membership."""
    smaller = graph.createGraph(["A<->B"])
    larger = graph.createGraph(["A<->B", "A->B"])

    assert graph.check_subcomponent(smaller, [larger])
    assert not graph.check_subcomponent(smaller, [graph.createGraph(["A->C"])])


def test_create_graph_parses_reversed_and_confounding_edges() -> None:
    """Graph construction handles reversed and bidirected arrows."""
    g = graph.createGraph(["X<-Y", "X<->Z"])

    assert sorted(graph.printGraph(g)[1]) == ["X<->Z", "Y->X"]


def test_create_graph_verbose_reports_vertices(capsys: pytest.CaptureFixture[str]) -> None:
    """Verbose graph construction reports its vertices."""
    graph.createGraph(["X->Y"], verbose=True)

    assert "'X'" in capsys.readouterr().out


@pytest.mark.parametrize("edge", ["Ab->Qb", "A_->Q_D", "0->1", "_A->Q_"])
def test_create_graph_accepts_arbitrary_variable_names(edge: str) -> None:
    """Graph construction accepts the variable names from issue #6."""
    assert graph.createGraph([edge]).ecount() == 1


@pytest.mark.parametrize("edge", ["X-Y", "->Y", "X->", "X->Y->Z"])
def test_invalid_edge_is_rejected(edge: str) -> None:
    """Malformed edge strings raise a helpful error."""
    with pytest.raises(ValueError, match="Invalid edge"):
        graph.createGraph([edge])


def test_unobserved_graph_replaces_confounding_edges() -> None:
    """A latent parent replaces a bidirected edge."""
    original = graph.createGraph(["X<->Y"])
    unobserved = graph.unobserved_graph(original)

    (latent,) = set(unobserved.vs["name"]) - {"X", "Y"}
    assert set(graph.printGraph(unobserved)[1]) == {f"{latent}->X", f"{latent}->Y"}
    assert graph.printGraph(original)[1] == ["X<->Y"]


def test_latent_name_never_reuses_an_observed_vertex() -> None:
    """Latent expansion leaves an unrelated observed node causally distinct."""
    original = graph.createGraph(["X<->Y", "Z->YX"])

    expanded = graph.unobserved_graph(original)
    latent = set(expanded.vs["name"]) - set(original.vs["name"])

    assert len(latent) == 1
    (name,) = latent
    assert set(graph.printGraph(expanded)[1]) == {"Z->YX", f"{name}->X", f"{name}->Y"}
    assert graph.dSep(expanded, {"Z"}, "Y", set())


def test_distinct_confounding_pairs_receive_distinct_latents() -> None:
    """Different endpoint pairs cannot collide through name concatenation."""
    original = graph.createGraph(["A<->BC", "CA<->B"])

    expanded = graph.unobserved_graph(original)
    latent = set(expanded.vs["name"]) - set(original.vs["name"])
    child_sets = {
        frozenset(expanded.vs[i]["name"] for i in expanded.neighbors(name, mode="out"))
        for name in latent
    }

    assert child_sets == {frozenset({"A", "BC"}), frozenset({"CA", "B"})}


@pytest.mark.parametrize(
    ("edges", "expected"),
    [
        (["X<->Y"], {"X", "Y"}),
        (["X<->Y", "Y->Z"], {"X", "Y"}),
    ],
    ids=["latent-only", "latent-and-visible"],
)
def test_bidirected_arcs_are_not_causal_parents(edges: list[str], expected: set[str]) -> None:
    """Only visible arrows contribute to causal parent counts."""
    assert graph.get_vertices_no_parents(graph.createGraph(edges)) == expected


@pytest.mark.parametrize(
    ("edges", "conditioned", "expected"),
    [
        pytest.param(["X->M", "M->Y"], set(), False, id="open-chain"),
        pytest.param(["X->M", "M->Y"], {"M"}, True, id="blocked-chain"),
        pytest.param(["M->X", "M->Y"], {"M"}, True, id="blocked-fork"),
        pytest.param(["X->M", "Y->M"], set(), True, id="closed-collider"),
        pytest.param(["X->M", "Y->M"], {"M"}, False, id="open-collider"),
        pytest.param(["X->M", "Y->M", "M->D"], {"D"}, False, id="open-descendant"),
    ],
)
def test_d_separation(edges: list[str], conditioned: set[str], expected: bool) -> None:
    """Separation follows chain, fork, collider, and descendant rules."""
    g = graph.createGraph(edges)
    assert graph.dSep(g, {"Y"}, "X", conditioned) is expected


@pytest.mark.parametrize(
    ("edges", "conditioned", "expected", "message"),
    [
        pytest.param(["X->M", "M->Y"], {"M"}, True, "Chain or Fork", id="blocked-chain"),
        pytest.param(["M->X", "M->Y"], {"M"}, True, "Chain or Fork", id="blocked-fork"),
        pytest.param(["X->M", "Y->M"], set(), True, "Collider", id="closed-collider"),
        pytest.param(["X->M", "Y->M"], {"M"}, False, "d-connected", id="open-collider"),
    ],
)
def test_verbose_d_separation_reports_path_status(
    edges: list[str],
    conditioned: set[str],
    expected: bool,
    message: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verbose separation reports why a path is blocked or open."""
    assert graph.dSep(graph.createGraph(edges), {"Y"}, "X", conditioned, verbose=True) is expected
    assert message in capsys.readouterr().out


def test_d_separation_rejects_conditioned_endpoints() -> None:
    """A path cannot condition on its source or target."""
    g = graph.createGraph(["X->M", "M->Y"])
    path = [g.vs.find(name=name).index for name in ("X", "M", "Y")]

    with pytest.raises(ValueError, match="Source or target"):
        graph.is_path_d_separated(g, path, {"X"})
