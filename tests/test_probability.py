"""Tests for probability expressions and simplification."""

from causaleffect import Probability
from causaleffect.probability import get_new_probability


def test_default_sets_are_independent() -> None:
    """New expressions do not share mutable defaults."""
    first = Probability()
    second = Probability()
    first._var.add("X")

    assert second._var == set()
    assert first.printLatex(simplify=False) == "P(x)"
    assert second.printLatex(simplify=False) == "1"


def test_copy_and_attributes_include_nested_expressions() -> None:
    """Copies are deep and recursive attributes describe their children."""
    child = Probability(var={"Y"}, cond={"X"})
    expression = Probability(recursive=True, children={child})
    clone = expression.copy()
    next(iter(clone._children))._var.add("Z")

    assert child._var == {"Y"}
    assert expression.attributes()["children"] == [child.attributes()]
    assert clone.attributes()["children"] != expression.attributes()["children"]


def test_fraction_attributes_and_free_variables() -> None:
    """A fraction exposes its divisor and includes denominator variables."""
    denominator = Probability(var={"Z"})
    expression = Probability(var={"Y"}, sumset={"Y"}, fraction=True, divisor=denominator)

    assert expression.attributes()["divisor"] == denominator.attributes()
    assert expression.getFreeVariables() == {"Z"}


def test_simplify_cancels_simple_denominators() -> None:
    """Simplification removes redundant denominator factors."""
    expression = Probability(var={"X", "Y"}, fraction=True, divisor=Probability(var={"X"}))
    expression.simplify(complete=False)

    assert expression.printLatex(simplify=False) == "P(y|x)"
    assert not expression._fraction

    expression = Probability(var={"X"}, fraction=True, divisor=Probability(var={"X"}, sumset={"X"}))
    expression.simplify(complete=False)
    assert expression.printLatex(simplify=False) == "P(x)"


def test_simplify_merges_conditional_factors() -> None:
    """Complete simplification combines a joint and conditional factor."""
    expression = Probability(
        recursive=True,
        children={Probability(var={"Y"}, cond={"X"}), Probability(var={"X"})},
    )
    expression.simplify()

    assert expression.printLatex(simplify=False) == "P(x, y)"
    assert not expression._recursive


def test_decouple_flattens_unsummed_products_only() -> None:
    """Nested products flatten unless their own summation binds them."""
    nested = Probability(recursive=True, children={Probability(var={"X"}), Probability(var={"Y"})})
    summed = Probability(recursive=True, children={Probability(var={"W"})}, sumset={"W"})
    expression = Probability(recursive=True, children={nested, summed})

    assert expression.decouple() is expression
    assert len(expression._children) == 3
    assert summed in expression._children
    assert nested not in expression._children


def test_sorting_and_new_conditionals() -> None:
    """Ordering and conditioning work for simple and recursive expressions."""
    assert Probability(var={"A"}) < Probability(var={"Z"})
    assert Probability(var={"A"}) < Probability()
    assert not Probability() < Probability(var={"A"})

    source = Probability(var={"X", "Y", "Z"})
    assert get_new_probability(source, {"Y"}).printLatex() == "P(y)"
    assert get_new_probability(source, {"Y"}, {"X"}).printLatex() == "P(y|x)"

    product = Probability(recursive=True, children={Probability(var={"X"}), Probability(var={"Y"})})
    assert get_new_probability(product, {"X"})._sumset == {"Y"}
