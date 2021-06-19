import copy


# Define a probability distribution class
class Probability:
    '''Probability distribution class. If recursive is set to True, var and cond are ignored
    and it becomes a product of probabilities in children. If fraction is set to True, the
    divisor is enabled.'''

    def __init__(self, var=set(), cond=set(), recursive=False, children=set(), sumset=set(), fraction=False,
                 divisor=None):
        self._var = var
        self._cond = cond
        self._recursive = recursive
        self._children = children
        self._sumset = sumset
        self._fraction = fraction
        self._divisor = divisor

    def copy(self):
        return copy.deepcopy(self)

    # GetAttributes
    def attributes(self):
        '''Function that shows all attributes of the probability distribution.'''
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

    def getFreeVariables(self):
        '''Function that returns the free variables of the distribution.'''
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

    def simplify(self, complete=True, verbose=False):
        '''Function that simplifies some expressions.'''
        self.decouple()
        changes = True
        while (changes):
            changes = False
            if not self._recursive:
                sum_variables = self._sumset.intersection(self._var)
                self._sumset = self._sumset.difference(sum_variables)
                self._var = self._var.difference(sum_variables)

                if self._fraction:
                    if not self._divisor._recursive:
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
                        if not prob1._recursive and not prob2._recursive and not prob1 == prob2:
                            if prob1._cond == prob2._var.union(prob2._cond):
                                simplified = prob2
                                if verbose: print("Additional simplification")
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

    def __lt__(self, other):
        '''Function that enables alphabetical sorting of variables.'''
        if len(other._var) == 0:
            return True
        if len(self._var) == 0:
            return False
        return sorted(self._var)[0].__lt__(sorted(other._var)[0])

    def printLatex(self, tab=0, simplify=True, complete_simplification=True, verbose=False):
        '''Function that returns a string in LaTeX syntax of the probability distribution.'''
        if simplify:
            self.simplify(complete=complete_simplification, verbose=verbose)
            if self._recursive:
                for prob in self._children:
                    prob.simplify(complete=complete_simplification, verbose=verbose)
        out = ""
        if self._fraction:
            out += '\\frac{'
        if len(self._sumset) != 0:
            if tab == 0:
                out += '\sum_{' + ', '.join(sorted(self._sumset)).lower() + '}'
            else:
                out += '\\left(\sum_{' + ', '.join(sorted(self._sumset)).lower() + '}'
        if not self._recursive:
            if len(self._var) != 0:
                out += 'P(' + ', '.join(sorted(self._var)).lower()
                if len(self._cond) != 0:
                    out += '|' + ', '.join(sorted(self._cond)).lower()
                out += ')'
            else:
                out += '1'
        else:
            for prob in sorted(self._children):
                out += prob.printLatex(tab=tab + 1, simplify=simplify, complete_simplification=complete_simplification,
                                       verbose=verbose)
        if len(self._sumset) != 0 and tab != 0:
            out += '\\right)'
        if self._fraction:
            out += '}{'
            out += self._divisor.printLatex(simplify=simplify, complete_simplification=complete_simplification,
                                            verbose=verbose)
            out += '}'
        return out

    def decouple(self):
        '''Recursive function that decouples products of probabilities when possible to ease simplification.'''
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


def get_new_probability(P, var, cond={}):
    '''Function that returns a new probability object P_out with variabes var conditioned on cond from
    the given probability P.'''
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
