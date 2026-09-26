"""Tests for graph construction, traversal, and separation."""

from unittest.mock import Mock

import pytest

from causaleffect import graph


def test_plot_graph_passes_styles_and_optional_filename(monkeypatch: pytest.MonkeyPatch) -> None:
    """Plotting passes graph styles to igraph and uses the requested filename."""
    g = graph.createGraph(["X->Y"])
    result = object()
    plot = Mock(return_value=result)
    monkeypatch.setattr(graph, "plot", plot)

    assert graph.plotGraph(g) is result
    assert plot.call_args.args == (g,)
    assert plot.call_args.kwargs["vertex_label"] == ["X", "Y"]
    assert graph.plotGraph(g, "figure") is result
    assert plot.call_args.args == (g, "figure.png")


def test_graph_components_and_edge_views() -> None:
    """Directed and confounded views preserve the intended edges."""
    g = graph.createGraph(["X<->Y", "Z->Y"])
    directed, bidirected = graph.get_directed_bidirected_graphs(g)

    assert graph.printGraph(directed)[1] == ["Z->Y"]
    assert graph.printGraph(bidirected)[1] == ["X<->Y"]
    assert {frozenset(component.vs["name"]) for component in graph.get_C_components(g)} == {
        frozenset({"X", "Y"}),
        frozenset({"Z"}),
    }


def test_opposite_directed_edges_do_not_become_confounding() -> None:
    """A directed cycle remains in the directed graph view."""
    g = graph.createGraph(["X->Y", "Y->X"])
    directed, bidirected = graph.get_directed_bidirected_graphs(g)

    assert not directed.is_dag()
    assert set(graph.printGraph(directed)[1]) == {"X->Y", "Y->X"}
    assert not bidirected.es


def test_graph_ancestry_and_ordering() -> None:
    """Traversal includes the starting vertices and rejects cycles."""
    g = graph.createGraph(["X->Y", "Y->Z"])

    assert graph.get_vertices_no_parents(g) == {"X"}
    assert graph.get_topological_ordering(g) == ["X", "Y", "Z"]
    assert graph.get_previous_order("Z", {"X", "Z"}, ["X", "Y", "Z"]) == {"X"}
    assert graph.get_ancestors(g, "Z") == {"X", "Y", "Z"}
    assert graph.get_ancestors(g, {"Y", "Z"}) == {"X", "Y", "Z"}
    assert graph.get_descendants(g, "X") == {"X", "Y", "Z"}
    assert graph.get_descendants(g, {"X", "Y"}) == {"X", "Y", "Z"}
    diamond = graph.createGraph(["X->A", "X->B", "A->Y", "B->Y"])
    assert graph.get_descendants(diamond, "X") == {"X", "A", "B", "Y"}

    cycle = graph.createGraph(["X->Y", "Y->X"])
    with pytest.raises(ValueError, match="cycle"):
        graph.get_ancestors(cycle, "X")
    with pytest.raises(ValueError, match="cycle"):
        graph.get_descendants(cycle, "X")


def test_subgraph_comparisons() -> None:
    """Graph comparisons distinguish vertices, edges, and equal graphs."""
    full = graph.createGraph(["X->Y", "Y->Z"])
    same = full.copy()
    wrong_edge = graph.createGraph(["X->Z"])

    assert graph.graphs_are_equal(full, same)
    assert not graph.graphs_are_equal(full, wrong_edge)
    assert not graph.check_subgraph(graph.createGraph(["W->X"]), full)
    assert not graph.check_subgraph(graph.createGraph(["X->Y", "Y->Z", "X->Z"]), full)
    assert not graph.check_subgraph(wrong_edge, full)
    assert graph.check_subcomponent(full, [wrong_edge, same])
    assert not graph.check_subcomponent(full, [wrong_edge])


def test_reversed_and_confounding_edges(capsys: pytest.CaptureFixture[str]) -> None:
    """Graph creation reports its structure and handles both arrow forms."""
    g = graph.createGraph(["X<-Y", "X<->Z"], verbose=True)

    assert "'X'" in capsys.readouterr().out
    assert sorted(graph.printGraph(g)[1]) == ["X<->Z", "Y->X"]


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


@pytest.mark.parametrize(
    ("edges", "conditioned", "expected"),
    [
        (["X->M", "M->Y"], set(), False),
        (["X->M", "M->Y"], {"M"}, True),
        (["M->X", "M->Y"], {"M"}, True),
        (["X->M", "Y->M"], set(), True),
        (["X->M", "Y->M"], {"M"}, False),
        (["X->M", "Y->M", "M->D"], {"D"}, False),
    ],
)
def test_d_separation(edges: list[str], conditioned: set[str], expected: bool) -> None:
    """Conditioning blocks chains and opens colliders."""
    g = graph.createGraph(edges)
    assert graph.dSep(g, {"Y"}, "X", conditioned) is expected
    assert graph.dSep(g, {"Y"}, "X", conditioned, verbose=True) is expected


def test_d_separation_rejects_conditioned_endpoints() -> None:
    """A path cannot condition on its source or target."""
    g = graph.createGraph(["X->M", "M->Y"])
    path = [g.vs.find(name=name).index for name in ("X", "M", "Y")]

    with pytest.raises(ValueError, match="Source or target"):
        graph.is_path_d_separated(g, path, {"X"})
