"""Regression tests for published causal effect examples."""

import pytest

from causaleffect import ID, Probability, createGraph, printGraph, to_R_notation
from causaleffect.id import ID_rec, NoCaseTriggeredError


def test_fig_3_5_a() -> None:
    """Code in Figure 3.5 (a)"""

    edges = ["X<->Z", "X<->W", "X->Z", "Z->W", "W->Y", "X->Y"]
    G = createGraph(edges)
    vertices = ["X", "Y", "Z", "W"]
    actual_vertices, actual_edges = printGraph(G)
    assert sorted(actual_vertices) == sorted(vertices)
    assert sorted(actual_edges) == sorted(edges)
    output = "X-+Z, Z-+W, W-+Y, X-+Y, X-+Z, X+-Z, X-+W, X+-W"
    assert to_R_notation(edges) == (output, 5, 8)


def test_fig_3_6_a() -> None:
    """Code in Figure 3.6 (a)"""

    p1 = Probability(var={"X", "Z"}, cond={"W"})
    p2 = Probability(var={"Y"}, cond={"Z"})
    p3 = Probability(var={"W"})
    p = Probability(recursive=True, children={p1, p2, p3})
    assert p.printLatex(simplify=False) == "P(w)P(x, z|w)P(y|z)"


def test_fig_3_6_b() -> None:
    """Code in Figure 3.6 (b)"""

    p1 = Probability(var={"X", "Z"}, cond={"W"})
    p2 = Probability(var={"Y"}, cond={"Z"})
    p3 = Probability(var={"W"})
    p4 = Probability(sumset={"X", "Z", "W"}, recursive=True, children={p1, p2, p3})
    p = Probability(
        sumset={"Z", "W"}, recursive=True, children={p1, p2, p3}, fraction=True, divisor=p4
    )
    assert (
        p.printLatex(simplify=False)
        == "\\frac{\\sum_{w, z}P(w)P(x, z|w)P(y|z)}{\\sum_{w, x, z}P(w)P(x, z|w)P(y|z)}"
    )


def test_fig_3_10() -> None:
    """Code in Figure 3.10"""

    G = createGraph(["X->Z", "Z->Y", "X<->Y"])
    P = ID({"Y"}, {"X"}, G)
    assert P.printLatex() == "\\sum_{z}P(z|x)\\left(\\sum_{x}P(x)P(y|x, z)\\right)"


def test_fig_3_12() -> None:
    """Code in Figure 3.12"""

    G = createGraph(["W->X", "X->Y_1", "Z->Y_2", "W<->Y_1", "W<->Z", "W<->Y_2", "X<->Z"])
    P = ID({"Y_1", "Y_2"}, {"X"}, G)
    assert P.printLatex() == "\\sum_{z}P(y_2, z)\\left(\\sum_{w}P(w)P(y_1|w, x)\\right)"


def test_fig_3_13() -> None:
    """Code in Figure 3.13"""

    G = createGraph(["W->X", "X->Y_1", "Z->Y_2", "W<->Y_1", "W<->Z", "W<->Y_2", "X<->Z", "W->Z"])
    P = ID({"Y_1", "Y_2"}, {"X"}, G)
    assert not P.identifiable
    forests = [printGraph(forest) for forest in P.hedge]
    assert [set(vertices) for vertices, _ in forests] == [
        {"W", "X", "Y_1", "Z", "Y_2"},
        {"W", "Y_1", "Z", "Y_2"},
    ]
    assert [set(edges) for _, edges in forests] == [
        {"W->X", "X->Y_1", "Z->Y_2", "W->Z", "W<->Y_1", "W<->Y_2", "X<->Z", "W<->Z"},
        {"W->Z", "Z->Y_2", "W<->Y_1", "W<->Y_2", "W<->Z"},
    ]
    assert P.attributes() == {"identifiable": False, "hedge": P.hedge}
    assert P.printLatex() == r"\text{Causal effect not identifiable}"


def test_confounded_direct_effect_returns_hedge() -> None:
    """A direct effect with confounding returns both hedge forests."""

    P = ID({"Y"}, {"X"}, createGraph(["X->Y", "X<->Y"]))
    assert not P.identifiable
    assert [printGraph(forest) for forest in P.hedge] == [
        (["X", "Y"], ["X->Y", "X<->Y"]),
        (["Y"], []),
    ]


def test_conditional_nonidentifiability_returns_hedge() -> None:
    """Conditional identification preserves a non-identifiability result."""

    P = ID({"Y"}, {"X"}, createGraph(["Z->X", "X->Y", "X<->Y"]), cond={"Z"})
    assert not P.identifiable
    assert len(P.hedge) == 2


def test_fig_3_15_a() -> None:
    """Code in Figure 3.15 (a)"""

    G = createGraph(["X<->Y", "Z->Y", "X->Z", "W->X", "W->Z"])
    P = ID({"Y"}, {"X"}, G, cond={"Z"})
    assert P.printLatex() == "\\frac{\\sum_{x}P(x|w)P(y|w, x, z)}{\\sum_{x, y}P(x|w)P(y|w, x, z)}"


def test_fig_3_15_b() -> None:
    """Code in Figure 3.15 (b)"""

    G = createGraph(["X<->Y", "Z->Y", "X->Z", "W->X", "W->Z"])
    P = ID({"Y"}, {"X"}, G)
    assert P.printLatex() == "\\sum_{w, z}P(w)P(z|w, x)\\left(\\sum_{x}P(x|w)P(y|w, x, z)\\right)"


def test_fig_3_16() -> None:
    """Code in Figure 3.16"""

    G = createGraph(["Z->X", "Z->Y", "X->Y"])
    P = ID({"Y"}, {"X"}, G)
    assert P.printLatex() == "\\sum_{z}P(y|x, z)P(z)"


@pytest.mark.parametrize(
    ("outcome", "intervention", "conditioned"),
    [
        ({"Y"}, {"Y"}, None),
        ({"Y"}, {"X"}, {"Y"}),
        ({"Y"}, {"X"}, {"X"}),
    ],
)
def test_rejects_overlapping_query_variables(
    outcome: set[str],
    intervention: set[str],
    conditioned: set[str] | None,
) -> None:
    """Outcome, intervention, and condition sets must be disjoint."""
    with pytest.raises(ValueError, match="Intersection"):
        ID(outcome, intervention, createGraph(["X->Y"]), cond=conditioned)


def test_rejects_cyclic_graph() -> None:
    """Identification accepts only acyclic directed causal graphs."""
    with pytest.raises(ValueError, match="DAG"):
        ID({"Y"}, {"X"}, createGraph(["X->Y", "Y->X"]))


def test_without_intervention_and_recursive_base_case() -> None:
    """Empty interventions marginalize other variables in either expression form."""
    g = createGraph(["X->Y"])
    assert ID({"Y"}, set(), g).printLatex() == "P(y)"

    joint = Probability(recursive=True, children={Probability(var={"X"}), Probability(var={"Y"})})
    result = ID_rec({"Y"}, set(), joint, g, ["X", "Y"])
    assert result._sumset == {"X"}
    assert result.printLatex(simplify=False) == r"\sum_{x}P(x)P(y)"


@pytest.mark.parametrize(
    ("edges", "conditioned"),
    [
        (["X->Z", "Z->Y", "X<->Y"], None),
        (["X<->Y", "Z->Y", "X->Z", "W->X", "W->Z"], {"Z"}),
        (["X->Y", "X<->Y"], None),
    ],
)
def test_verbose_trace_preserves_identification(
    edges: list[str],
    conditioned: set[str] | None,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verbose tracing leaves the identified effect unchanged."""
    g = createGraph(edges)
    expected = ID({"Y"}, {"X"}, g, cond=conditioned)
    actual = ID({"Y"}, {"X"}, g, cond=conditioned, verbose=True)

    assert actual.identifiable == expected.identifiable
    assert actual.printLatex() == expected.printLatex()
    assert "Depth:" in capsys.readouterr().out


def test_conditional_rule_moves_variable_into_intervention() -> None:
    """IDC applies its separation rule to a conditioned parent."""
    g = createGraph(["Z->X", "Z->Y", "X->Y"])
    result = ID({"Y"}, {"X"}, g, cond={"Z"})

    assert result.identifiable
    assert result.printLatex() == "P(y|x, z)"


def test_no_case_exception_keeps_message() -> None:
    """The internal error reports its supplied message."""
    assert str(NoCaseTriggeredError("missing case")) == "missing case"
