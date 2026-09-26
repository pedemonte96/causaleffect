"""Tests for causal effect identification and input validation."""

import pytest
from igraph import Graph

from causaleffect import ID, Probability, createGraph, printGraph
from causaleffect.id import ID_rec, NoCaseTriggeredError


def test_confounded_direct_effect_returns_hedge() -> None:
    """A direct effect with confounding returns both hedge forests."""

    P = ID({"Y"}, {"X"}, createGraph(["X->Y", "X<->Y"]))
    assert not P.identifiable
    assert [printGraph(forest) for forest in P.hedge] == [
        (["X", "Y"], ["X->Y", "X<->Y"]),
        (["Y"], []),
    ]
    assert all(edge["confounding"] in (-1, 0, 1) for forest in P.hedge for edge in forest.es)


def test_conditional_nonidentifiability_returns_hedge() -> None:
    """Conditional identification preserves a non-identifiability result."""

    P = ID({"Y"}, {"X"}, createGraph(["Z->X", "X->Y", "X<->Y"]), cond={"Z"})
    assert not P.identifiable
    assert len(P.hedge) == 2


@pytest.mark.parametrize(
    ("outcome", "intervention", "conditioned"),
    [
        ({"Y"}, {"Y"}, None),
        ({"Y"}, {"X"}, {"Y"}),
        ({"Y"}, {"X"}, {"X"}),
    ],
    ids=["outcome-intervention", "outcome-condition", "intervention-condition"],
)
def test_rejects_overlapping_query_variables(
    outcome: set[str],
    intervention: set[str],
    conditioned: set[str] | None,
) -> None:
    """Outcome, intervention, and condition sets must be disjoint."""
    with pytest.raises(ValueError, match="Intersection"):
        ID(outcome, intervention, createGraph(["X->Y"]), cond=conditioned)


@pytest.mark.parametrize(
    "edges", [["X->Y", "Y->X"], ["X->X", "X->Y"]], ids=["two-vertex", "self-loop"]
)
def test_rejects_cyclic_graph(edges: list[str]) -> None:
    """Identification accepts only acyclic directed causal graphs."""
    with pytest.raises(ValueError, match="DAG"):
        ID({"Y"}, {"X"}, createGraph(edges))


@pytest.mark.parametrize(
    ("outcome", "intervention", "conditioned", "variable"),
    [
        ({"NO"}, {"X"}, None, "Y"),
        ({"Y"}, {"NO"}, None, "X"),
        ({"Y"}, {"X"}, {"NO"}, "cond"),
    ],
    ids=["outcome", "intervention", "condition"],
)
def test_rejects_unknown_query_variables(
    outcome: set[str],
    intervention: set[str],
    conditioned: set[str] | None,
    variable: str,
) -> None:
    """Every unknown outcome, intervention, or condition fails at the API boundary."""
    with pytest.raises(ValueError, match=f"{variable} contains variables not present"):
        ID(outcome, intervention, createGraph(["X->Y"]), cond=conditioned)


@pytest.mark.parametrize("conditioned", [None, {"Z"}], ids=["id", "idc"])
def test_accepts_named_igraph_dag_without_confounding_metadata(
    conditioned: set[str] | None,
) -> None:
    """An ordinary named DAG has only visible arrows without changing the caller's graph."""
    g = Graph(edges=[(0, 1), (2, 1)], directed=True)
    g.vs["name"] = ["X", "Y", "Z"]

    result = ID({"Y"}, {"X"}, g, cond=conditioned)

    assert result.printLatex() == ("P(y|x, z)" if conditioned else r"\sum_{z}P(y|x, z)P(z)")
    assert "confounding" not in g.edge_attributes()


@pytest.mark.parametrize(
    ("directed", "named", "message"),
    [
        (False, True, "directed"),
        (True, False, "names"),
    ],
    ids=["undirected", "unnamed"],
)
def test_rejects_graphs_without_required_structure(
    directed: bool, named: bool, message: str
) -> None:
    """Identification rejects undirected graphs and graphs without names."""
    g = Graph(edges=[(0, 1)], directed=directed)
    if named:
        g.vs["name"] = ["X", "Y"]

    with pytest.raises(ValueError, match=message):
        ID({"Y"}, {"X"}, g)


def test_rejects_duplicate_vertex_names() -> None:
    """Name-based graph lookup requires one unique name per vertex."""
    g = Graph(edges=[(0, 1)], directed=True)
    g.vs["name"] = ["X", "X"]

    with pytest.raises(ValueError, match="unique"):
        ID({"X"}, set(), g)


@pytest.mark.parametrize("edge_type", [None, 2, "U", True])
def test_rejects_invalid_confounding_values(edge_type: object) -> None:
    """Only signed bidirected halves and zero-valued arrows are accepted."""
    g = createGraph(["X->Y"])
    g.es["confounding"] = [edge_type]

    with pytest.raises(ValueError, match="confounding"):
        ID({"Y"}, {"X"}, g)


@pytest.mark.parametrize(
    ("edges", "types"),
    [
        (["X->Y"], [1]),
        (["X<->Y"], [1, 1]),
        (["X<->Y", "X<->Y"], [1, -1, 1, 0]),
        (["X<->X"], [1, -1]),
    ],
    ids=["missing-half", "same-sign", "unequal-pairs", "self-loop"],
)
def test_rejects_unpaired_confounding_edges(edges: list[str], types: list[int]) -> None:
    """Each latent arc needs opposite signed halves between distinct vertices."""
    g = createGraph(edges)
    g.es["confounding"] = types

    with pytest.raises(ValueError, match="confounding"):
        ID({"Y"} if "Y" in g.vs["name"] else {"X"}, set(), g)


def test_parallel_visible_arrows_are_valid_identification_input() -> None:
    """Duplicating a visible arrow does not alter the causal effect."""
    g = createGraph(["X->Y", "X->Y"])

    assert ID({"Y"}, {"X"}, g).printLatex() == "P(y|x)"


def test_repeated_bidirected_arcs_remain_valid_identification_input() -> None:
    """Duplicating a latent arc does not invent a visible causal arrow."""
    g = createGraph(["X<->Y", "X<->Y"])

    assert ID({"Y"}, {"X"}, g).printLatex() == "P(y)"


def test_without_intervention_returns_marginal() -> None:
    """An empty intervention returns the outcome's marginal probability."""
    g = createGraph(["X->Y"])
    assert ID({"Y"}, set(), g).printLatex() == "P(y)"


def test_recursive_id_base_case_marginalizes_joint() -> None:
    """Recursive identification sums non-outcome variables from a joint expression."""
    g = createGraph(["X->Y"])
    joint = Probability(recursive=True, children={Probability(var={"X"}), Probability(var={"Y"})})
    result = ID_rec({"Y"}, set(), joint, g, ["X", "Y"])
    assert result._sumset == {"X"}
    assert result.printLatex(simplify=False) == r"\sum_{x}P(x)P(y)"


def test_identification_uses_multivertex_confounding_component() -> None:
    """A confounded outcome component is factored and marginalized."""
    g = createGraph(["X->Y", "Z->Y", "Y<->Z"])
    result = ID({"Y"}, {"X"}, g)

    assert result.printLatex(simplify=False) == r"\sum_{z}P(y|x, z)P(z|x)"
    assert result.printLatex() == "P(y|x)"


def test_unidentifiable_subproblem_propagates_hedge() -> None:
    """A non-identifiable component makes the full query non-identifiable."""
    g = createGraph(["X->Y", "X<->Y", "Z->Y"])
    result = ID({"Y"}, {"X"}, g)

    assert not result.identifiable
    assert [set(forest.vs["name"]) for forest in result.hedge] == [{"X", "Y"}, {"Y"}]


def test_multiple_conditioning_variables_are_processed() -> None:
    """Conditional identification handles more than one measured parent."""
    g = createGraph(["X->Y", "Z->Y", "W->Y"])
    assert ID({"Y"}, {"X"}, g, cond={"Z", "W"}).printLatex() == "P(y|w, x, z)"


def test_confounding_keeps_multiple_variables_in_condition() -> None:
    """Confounded measured parents remain in a conditional effect."""
    g = createGraph(["X->Y", "Z->Y", "W->Y", "Z<->Y", "W<->Y"])
    result = ID({"Y"}, {"X"}, g, cond={"Z", "W"})

    assert result.printLatex() == r"\frac{P(w, y, z|x)}{P(w, z|x)}"


@pytest.mark.parametrize(
    ("edges", "conditioned", "trace_line"),
    [
        (["X->Z", "Z->Y", "X<->Y"], None, "Line 4"),
        (["X<->Y", "Z->Y", "X->Z", "W->X", "W->Z"], {"Z"}, "Line 1 COND"),
        (["X->Y", "X<->Y"], None, "Line 5"),
        (["X->Y", "Z->Y", "Y<->Z"], None, "Line 6 Probabilities"),
    ],
    ids=["frontdoor", "conditional", "hedge", "multivertex-component"],
)
def test_verbose_trace_preserves_identification(
    edges: list[str],
    conditioned: set[str] | None,
    trace_line: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verbose tracing reports each branch without changing its result."""
    g = createGraph(edges)
    expected = ID({"Y"}, {"X"}, g, cond=conditioned)
    actual = ID({"Y"}, {"X"}, g, cond=conditioned, verbose=True)

    assert actual.identifiable == expected.identifiable
    assert actual.printLatex() == expected.printLatex()
    assert trace_line in capsys.readouterr().out


def test_conditional_rule_moves_variable_into_intervention() -> None:
    """IDC applies its separation rule to a conditioned parent."""
    g = createGraph(["Z->X", "Z->Y", "X->Y"])
    result = ID({"Y"}, {"X"}, g, cond={"Z"})

    assert result.printLatex() == "P(y|x, z)"


def test_no_case_exception_keeps_message() -> None:
    """The internal error reports its supplied message."""
    assert str(NoCaseTriggeredError("missing case")) == "missing case"
