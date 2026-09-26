"""Regression tests for figures in the causal inference paper."""

from causaleffect import ID, Probability, createGraph, printGraph, to_R_notation


def test_figure_3_5_a_graph_edges() -> None:
    """Figure 3.5(a) preserves visible and latent graph edges."""
    edges = ["X<->Z", "X<->W", "X->Z", "Z->W", "W->Y", "X->Y"]

    vertices, actual_edges = printGraph(createGraph(edges))

    assert set(vertices) == {"X", "Y", "Z", "W"}
    assert sorted(actual_edges) == sorted(edges)


def test_figure_3_5_a_r_notation() -> None:
    """R notation encodes the visible and latent edges of Figure 3.5(a)."""
    edges = ["X<->Z", "X<->W", "X->Z", "Z->W", "W->Y", "X->Y"]
    expected = "X-+Z, Z-+W, W-+Y, X-+Y, X-+Z, X+-Z, X-+W, X+-W"

    assert to_R_notation(edges) == (expected, 5, 8)


def test_figure_3_6_a_product_latex() -> None:
    """Figure 3.6(a) renders a product of conditional probabilities."""
    factors = {
        Probability(var={"X", "Z"}, cond={"W"}),
        Probability(var={"Y"}, cond={"Z"}),
        Probability(var={"W"}),
    }

    assert Probability(recursive=True, children=factors).printLatex(simplify=False) == (
        "P(w)P(x, z|w)P(y|z)"
    )


def test_figure_3_6_b_fraction_latex() -> None:
    """Figure 3.6(b) renders a fraction with separate summation scopes."""
    factors = {
        Probability(var={"X", "Z"}, cond={"W"}),
        Probability(var={"Y"}, cond={"Z"}),
        Probability(var={"W"}),
    }
    denominator = Probability(sumset={"X", "Z", "W"}, recursive=True, children=factors)
    expression = Probability(
        sumset={"Z", "W"}, recursive=True, children=factors, fraction=True, divisor=denominator
    )

    assert expression.printLatex(simplify=False) == (
        r"\frac{\sum_{w, z}P(w)P(x, z|w)P(y|z)}{\sum_{w, x, z}P(w)P(x, z|w)P(y|z)}"
    )


def test_figure_3_10_frontdoor_identification() -> None:
    """Figure 3.10 identifies a frontdoor effect."""
    G = createGraph(["X->Z", "Z->Y", "X<->Y"])
    P = ID({"Y"}, {"X"}, G)
    assert P.printLatex() == "\\sum_{z}P(z|x)\\left(\\sum_{x}P(x)P(y|x, z)\\right)"


def test_figure_3_12_multivariate_identification() -> None:
    """Figure 3.12 identifies a multivariate effect."""
    G = createGraph(["W->X", "X->Y_1", "Z->Y_2", "W<->Y_1", "W<->Z", "W<->Y_2", "X<->Z"])
    P = ID({"Y_1", "Y_2"}, {"X"}, G)
    assert P.printLatex() == "\\sum_{z}P(y_2, z)\\left(\\sum_{w}P(w)P(y_1|w, x)\\right)"


def test_figure_3_13_unidentifiable_hedge() -> None:
    """Figure 3.13 returns the expected hedge for an unidentifiable effect."""
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


def test_figure_3_15_a_conditional_identification() -> None:
    """Figure 3.15(a) identifies a conditional effect."""
    G = createGraph(["X<->Y", "Z->Y", "X->Z", "W->X", "W->Z"])
    P = ID({"Y"}, {"X"}, G, cond={"Z"})
    assert P.printLatex() == "\\frac{\\sum_{x}P(x|w)P(y|w, x, z)}{\\sum_{x, y}P(x|w)P(y|w, x, z)}"


def test_figure_3_15_b_marginal_identification() -> None:
    """Figure 3.15(b) identifies a marginal effect."""
    G = createGraph(["X<->Y", "Z->Y", "X->Z", "W->X", "W->Z"])
    P = ID({"Y"}, {"X"}, G)
    assert P.printLatex() == "\\sum_{w, z}P(w)P(z|w, x)\\left(\\sum_{x}P(x|w)P(y|w, x, z)\\right)"


def test_figure_3_16_backdoor_adjustment() -> None:
    """Figure 3.16 identifies an effect by adjusting for a common cause."""
    G = createGraph(["Z->X", "Z->Y", "X->Y"])
    P = ID({"Y"}, {"X"}, G)
    assert P.printLatex() == "\\sum_{z}P(y|x, z)P(z)"
