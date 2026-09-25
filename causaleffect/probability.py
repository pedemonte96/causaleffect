"""Probability expressions for causal effects."""

from __future__ import annotations

import copy

from igraph import Graph


# Define a probability distribution class
class Probability:
    """Probability distribution class. If recursive is set to True, var and cond are ignored
    and it becomes a product of probabilities in children. If fraction is set to True, the
    divisor is enabled. A hedge marks a non-identifiable effect."""

    def __init__(
        self,
        var: set[str] | None = None,
        cond: set[str] | None = None,
        recursive: bool = False,
        children: set[Probability] | None = None,
        sumset: set[str] | None = None,
        fraction: bool = False,
        divisor: Probability | None = None,
        hedge: tuple[Graph, Graph] | None = None,
    ) -> None:
        """Create a probability expression or a non-identifiability result with a hedge."""
        self._var: set[str] = set() if var is None else var
        self._cond: set[str] = set() if cond is None else cond
        self._recursive: bool = recursive
        self._children: set[Probability] = set() if children is None else children
        self._sumset: set[str] = set() if sumset is None else sumset
        self._fraction: bool = fraction
        self._divisor: Probability | None = divisor
        self.hedge: tuple[Graph, Graph] | None = hedge

    @property
    def identifiable(self) -> bool:
        """Whether the causal effect has an identifiable probability expression."""
        return self.hedge is None

    def copy(self) -> Probability:
        """Return a deep copy of the probability expression."""
        return copy.deepcopy(self)

    # GetAttributes
    def attributes(self) -> dict[str, object]:
        """Function that shows all attributes of the probability distribution."""
        if not self.identifiable:
            return {"identifiable": False, "hedge": self.hedge}
        out = {}
        out["var"] = self._var
        out["cond"] = self._cond
        out["recursive"] = self._recursive
        if self._recursive:
            out["children"] = [child.attributes() for child in self._children]
        else:
            out["children"] = self._children
        out["sumset"] = self._sumset
        out["fraction"] = self._fraction
        if self._fraction:
            out["divisor"] = self._divisor.attributes()
        else:
            out["divisor"] = self._divisor
        return out

    def getFreeVariables(self) -> set[str]:
        """Function that returns the free variables of the distribution."""
        free = set()
        if not self._recursive:
            free = free.union(self._var)
        else:
            for prob in self._children:
                free = free.union(prob.getFreeVariables())
        free = free.difference(self._sumset)
        if self._fraction:
            free = free.union(self._divisor.getFreeVariables())
        return free

    def simplify(self, complete: bool = True, verbose: bool = False) -> None:
        """Function that simplifies some expressions."""
        self.decouple()
        changes = True
        while changes:
            changes = False
            if not self._recursive:
                sum_variables = self._sumset.intersection(self._var)
                self._sumset = self._sumset.difference(sum_variables)
                self._var = self._var.difference(sum_variables)

                if self._fraction and not self._divisor._recursive:
                    sum_variables = self._divisor._sumset.intersection(self._divisor._var)
                    self._divisor._sumset = self._divisor._sumset.difference(sum_variables)
                    self._divisor._var = self._divisor._var.difference(sum_variables)
                    if len(self._divisor._var) == 0:
                        self._divisor = None
                        self._fraction = False
                    elif len(self._divisor._cond) == 0 and self._divisor._var.issubset(self._var):
                        self._var = self._var.difference(self._divisor._var)
                        self._cond = self._cond.union(self._divisor._var)
                        self._divisor = None
                        self._fraction = False
            elif complete:
                simplified = None
                for prob1 in self._children:
                    for prob2 in self._children:
                        if (
                            not prob1._recursive
                            and not prob2._recursive
                            and prob1 != prob2
                            and prob1._cond == prob2._var.union(prob2._cond)
                        ):
                            simplified = prob2
                            if verbose:
                                print("Additional simplification")
                            prob1._var = prob1._var.union(prob2._var)
                            prob1._cond = prob1._cond.difference(prob2._var)
                            changes = True
                        if simplified is not None:
                            break
                    if simplified is not None:
                        break
                if simplified is not None:
                    self._children.remove(simplified)
                    if len(self._children) == 1:
                        (prob,) = self._children
                        self._sumset = prob._sumset.union(self._sumset)
                        self._var = prob._var
                        self._cond = prob._cond
                        self._recursive = False
                        self._children = set()

    def __lt__(self, other: Probability) -> bool:
        """Function that enables alphabetical sorting of variables."""
        if len(other._var) == 0:
            return True
        if len(self._var) == 0:
            return False
        return min(self._var) < min(other._var)

    def printLatex(
        self,
        tab: int = 0,
        simplify: bool = True,
        complete_simplification: bool = True,
        verbose: bool = False,
    ) -> str:
        """Return the probability expression or non-identifiability status in LaTeX."""
        if not self.identifiable:
            return r"\text{Causal effect not identifiable}"
        if simplify:
            self.simplify(complete=complete_simplification, verbose=verbose)
            if self._recursive:
                for prob in self._children:
                    prob.simplify(complete=complete_simplification, verbose=verbose)
        out = ""
        if self._fraction:
            out += "\\frac{"
        if len(self._sumset) != 0:
            if tab == 0:
                out += r"\sum_{" + ", ".join(sorted(self._sumset)).lower() + "}"
            else:
                out += r"\left(\sum_{" + ", ".join(sorted(self._sumset)).lower() + "}"
        if not self._recursive:
            if len(self._var) != 0:
                out += "P(" + ", ".join(sorted(self._var)).lower()
                if len(self._cond) != 0:
                    out += "|" + ", ".join(sorted(self._cond)).lower()
                out += ")"
            else:
                out += "1"
        else:
            for prob in sorted(self._children):
                out += prob.printLatex(
                    tab=tab + 1,
                    simplify=simplify,
                    complete_simplification=complete_simplification,
                    verbose=verbose,
                )
        if len(self._sumset) != 0 and tab != 0:
            out += "\\right)"
        if self._fraction:
            out += "}{"
            out += self._divisor.printLatex(
                simplify=simplify, complete_simplification=complete_simplification, verbose=verbose
            )
            out += "}"
        return out

    def decouple(self) -> Probability:
        """Flatten nested products when no summation blocks simplification."""
        new_children = set()
        decouple = False
        if self._recursive:
            for p in self._children:
                if p._recursive and len(p._sumset) == 0:
                    decouple = True
                    subdec = p.decouple()
                    new_children = new_children.union(subdec._children)
                else:
                    new_children = new_children.union({p})
            if decouple:
                self._children = new_children
        return self


def get_new_probability(P: Probability, var: set[str], cond: set[str] | None = None) -> Probability:
    """Function that returns a new probability object P_out with variables var
    conditioned on cond from the given probability P."""
    cond = set() if cond is None else cond
    P_out = P.copy()
    if len(cond) == 0:
        if P_out._recursive:
            P_out._sumset = P_out._sumset.union(P.getFreeVariables().difference(var))
        else:
            P_out._var = var
    else:
        P_denom = P.copy()
        P_out._sumset = P_out._sumset.union(P.getFreeVariables().difference(cond.union(var)))
        P_out._fraction = True
        P_denom._sumset = P_denom._sumset.union(P.getFreeVariables().difference(cond))
        P_out._divisor = P_denom
        P_out.simplify(complete=False)
    return P_out
