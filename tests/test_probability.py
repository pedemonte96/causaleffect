"""Tests for probability expressions and simplification."""

import pytest

from causaleffect import Probability
from causaleffect.probability import get_new_probability


def test_default_variable_sets_are_independent() -> None:
    """New expressions do not share their variable sets."""
    first = Probability()
    second = Probability()
    first._var.add("X")

    assert second._var == set()


def test_copy_clones_nested_expressions() -> None:
    """Copying a recursive expression copies its children."""
    child = Probability(var={"Y"}, cond={"X"})
    expression = Probability(recursive=True, children={child})
    clone = expression.copy()
    next(iter(clone._children))._var.add("Z")

    assert child._var == {"Y"}


def test_recursive_attributes_include_children() -> None:
    """Recursive attributes describe their child expressions."""
    child = Probability(var={"Y"}, cond={"X"})
    expression = Probability(recursive=True, children={child})

    assert expression.attributes()["children"] == [child.attributes()]


def test_fraction_attributes_include_divisor() -> None:
    """Fraction attributes describe the divisor."""
    denominator = Probability(var={"Z"})
    expression = Probability(var={"Y"}, fraction=True, divisor=denominator)

    assert expression.attributes()["divisor"] == denominator.attributes()


def test_fraction_free_variables_include_denominator() -> None:
    """Free variables include unsummed denominator variables."""
    expression = Probability(var={"Y"}, sumset={"Y"}, fraction=True, divisor=Probability(var={"Z"}))

    assert expression.getFreeVariables() == {"Z"}


def test_simplify_cancels_matching_marginal() -> None:
    """A matching marginal denominator becomes a condition."""
    expression = Probability(var={"X", "Y"}, fraction=True, divisor=Probability(var={"X"}))
    expression.simplify(complete=False)

    assert expression.printLatex(simplify=False) == "P(y|x)"


def test_simplify_removes_unit_denominator() -> None:
    """Summing out a denominator's only variable yields one."""
    expression = Probability(var={"X"}, fraction=True, divisor=Probability(var={"X"}, sumset={"X"}))
    expression.simplify(complete=False)

    assert expression.printLatex(simplify=False) == "P(x)"


def test_simplify_preserves_nonredundant_denominator() -> None:
    """A conditional denominator remains when it cannot be cancelled."""
    expression = Probability(var={"Y"}, fraction=True, divisor=Probability(var={"Z"}, cond={"X"}))

    expression.simplify()

    assert expression.printLatex(simplify=False) == r"\frac{P(y)}{P(z|x)}"


def test_fraction_keeps_unmatched_conditioning() -> None:
    """P(A,B|C) divided by P(B) is not P(A|B,C)."""
    expression = Probability(
        var={"A", "B"}, cond={"C"}, fraction=True, divisor=Probability(var={"B"})
    )

    assert expression.printLatex() == r"\frac{P(a, b|c)}{P(b)}"


def test_fraction_cancels_matching_conditional_marginal() -> None:
    """A matching conditional denominator permits the chain-rule identity."""
    expression = Probability(
        var={"A", "B"},
        cond={"C"},
        fraction=True,
        divisor=Probability(var={"B"}, cond={"C"}),
    )

    assert expression.printLatex() == "P(a|b, c)"


def test_nested_fraction_denominator_is_preserved() -> None:
    """An atomic-looking denominator can itself be a fraction."""
    denominator = Probability(fraction=True, divisor=Probability(var={"B"}))
    expression = Probability(var={"A"}, fraction=True, divisor=denominator)

    assert expression.printLatex() == r"\frac{P(a)}{\frac{1}{P(b)}}"


def test_simplify_merges_conditional_factors(capsys: pytest.CaptureFixture[str]) -> None:
    """Complete simplification combines a joint and conditional factor."""
    expression = Probability(
        recursive=True,
        children={Probability(var={"Y"}, cond={"X"}), Probability(var={"X"})},
    )
    expression.simplify(complete=False)
    assert expression.printLatex(simplify=False) == "P(x)P(y|x)"

    expression.simplify(verbose=True)

    assert expression.printLatex(simplify=False) == "P(x, y)"
    assert not expression._recursive
    assert "Additional simplification" in capsys.readouterr().out


def test_unrelated_product_factors_stay_separate() -> None:
    """Simplification leaves independent probability factors intact."""
    expression = Probability(
        recursive=True, children={Probability(var={"X"}), Probability(var={"Y"})}
    )

    expression.simplify()

    assert expression.printLatex(simplify=False) == "P(x)P(y)"


def test_decouple_flattens_unsummed_products_only() -> None:
    """Nested products flatten unless their own summation binds them."""
    nested = Probability(recursive=True, children={Probability(var={"X"}), Probability(var={"Y"})})
    summed = Probability(recursive=True, children={Probability(var={"W"})}, sumset={"W"})
    expression = Probability(recursive=True, children={nested, summed})

    expression.decouple()
    assert len(expression._children) == 3
    assert summed in expression._children
    assert nested not in expression._children


def test_decouple_retains_nested_product_denominator() -> None:
    """Flattening a fractional product must not discard its denominator."""
    fraction = Probability(
        recursive=True,
        children={Probability(var={"A"}), Probability(var={"B"})},
        fraction=True,
        divisor=Probability(var={"B"}),
    )
    expression = Probability(recursive=True, children={fraction, Probability(var={"C"})})

    expression.decouple()

    assert fraction in expression._children
    assert expression.printLatex(simplify=False) == r"P(c)\frac{P(a)P(b)}{P(b)}"


@pytest.mark.parametrize("fraction_on_conditional", [False, True], ids=["marginal", "conditional"])
def test_chain_rule_merge_retains_fraction_factors(fraction_on_conditional: bool) -> None:
    """A fraction on either factor cannot be absorbed by a product rewrite."""
    conditional = Probability(
        var={"A"},
        cond={"B"},
        fraction=fraction_on_conditional,
        divisor=Probability(var={"C"}) if fraction_on_conditional else None,
    )
    marginal = Probability(
        var={"B"},
        fraction=not fraction_on_conditional,
        divisor=None if fraction_on_conditional else Probability(var={"C"}),
    )
    expression = Probability(recursive=True, children={conditional, marginal})

    expression.simplify()

    assert expression._recursive
    assert expression.printLatex(simplify=False) == (
        r"\frac{P(a|b)}{P(c)}P(b)" if fraction_on_conditional else r"P(a|b)\frac{P(b)}{P(c)}"
    )


def test_chain_rule_merge_retains_child_summation() -> None:
    """A factor's local sum cannot disappear during product simplification."""
    conditional = Probability(var={"A"}, cond={"B"})
    summed = Probability(var={"B"}, sumset={"B"})
    expression = Probability(recursive=True, children={conditional, summed})

    expression.simplify()

    assert expression._recursive
    assert summed in expression._children
    assert expression.printLatex(simplify=False) == r"P(a|b)\left(\sum_{b}P(b)\right)"


def test_empty_probability_order_is_strict() -> None:
    """Two empty probability factors never precede each other."""
    first, second = Probability(), Probability()

    assert not first < second
    assert not second < first


def test_probability_order_breaks_ties_and_places_empty_factors_last() -> None:
    """Ordering breaks ties and places nonempty factors before empty factors."""
    assert Probability(var={"A", "B"}) < Probability(var={"A", "C"})
    assert Probability(var={"A"}, cond={"B"}) < Probability(var={"A"}, cond={"C"})
    assert Probability(var={"A"}) < Probability(var={"Z"})
    assert Probability(var={"A"}) < Probability()
    assert not Probability() < Probability(var={"A"})


def test_new_probability_handles_atomic_and_recursive_expressions() -> None:
    """New probabilities select and condition atomic or recursive expressions."""
    source = Probability(var={"X", "Y", "Z"})
    assert get_new_probability(source, {"Y"}).printLatex() == "P(y)"
    assert get_new_probability(source, {"Y"}, {"X"}).printLatex() == "P(y|x)"

    product = Probability(recursive=True, children={Probability(var={"X"}), Probability(var={"Y"})})
    assert get_new_probability(product, {"X"})._sumset == {"Y"}
