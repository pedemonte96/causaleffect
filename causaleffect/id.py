from causaleffect.probability import *
from causaleffect.graph import *


# Define exceptions that can occur.
class HedgeFound(Exception):
    '''Exception raised when a hedge is found.'''

    def __init__(self, g1, g2, message="Causal effect not identifiable. A hedge has been found:"):
        self._message = message
        v1, e1 = printGraph(g1)
        v2, e2 = printGraph(g2)
        super().__init__(self._message + "\n\nC-Forest 1:\nVertices: " + ', '.join(v1) +
                         '\nEdges: ' + ', '.join(e1) + "\n\nC-Forest 2:\nVertices: " +
                         ', '.join(v2) + '\nEdges: ' + ', '.join(e2))


class NoCaseTriggered(Exception):
    '''Exception raised when none of the lines in ID is triggered.
    Should not be necessary when algorithm implementation is completed.'''

    def __init__(self, message="No case has been triggered"):
        self._message = message
        super().__init__(self._message)


def ID_rec(Y, X, P, G, ordering, verbose=False, tab=0):
    '''Recursive non-conditional identification algorithm.'''

    V = set(G.vs["name"])
    G_dir, G_bidir = get_directed_bidirected_graphs(G)
    # line 1
    if len(X) == 0:
        if verbose: print("Depth:", tab, "Line 1 before: Y:", Y, "X:", X, "V:", V, "P:", P.printLatex())
        if verbose: print("Depth:", tab, "Line 1 sumset:", P._sumset.union(V.difference(Y)))
        P_out = P.copy()
        if P_out._recursive:
            P_out._sumset = P._sumset.union(V.difference(Y))
        else:
            P_out._var = Y
        if verbose: print("Depth:", tab, "Line 1 output:", P_out.printLatex())
        return P_out

    # line 2
    anc = get_ancestors(G_dir, Y)
    if len(V.difference(anc)) != 0:
        if verbose: print("Depth:", tab, "Line 2 before: Y:", Y, "X:", X, "V:", V, "P:", P.printLatex())
        P_out = P.copy()
        if P_out._recursive:
            P_out._sumset = P._sumset.union(V.difference(anc))
        else:
            P_out._var = anc
        if verbose: print("Depth:", tab, "Line 2 output: Y:", Y, "new X:", X.intersection(anc), "new V:", anc, "P:",
                          P_out.printLatex())
        if verbose: print("Depth:", tab, "Line 2 graph:", printGraph(G.induced_subgraph(G.vs.select(name_in=anc))))
        return ID_rec(Y, X.intersection(anc), P_out, G.induced_subgraph(G.vs.select(name_in=anc)), ordering,
                      verbose=verbose, tab=tab + 1)

    # line 3
    G_x = G.copy()
    G_x.delete_edges(G_x.es.select(_target_in=G_x.vs.select(name_in=X)))
    G_x_dir, G_x_bidir = get_directed_bidirected_graphs(G_x)
    anc_x = get_ancestors(G_x_dir, Y)
    W = V.difference(X).difference(anc_x)
    if len(W) != 0:
        if verbose: print("Depth:", tab, "Line 3 before: Y:", Y, "X:", X, "V:", V, "P:", P.printLatex())
        if verbose: print("Depth:", tab, "Line 3 W:", W, "new X:", X.union(W))
        return ID_rec(Y, X.union(W), P, G, ordering, verbose=verbose, tab=tab + 1)

    # line 4
    C_components_V_X = get_C_components(G.induced_subgraph(G.vs.select(name_in=V.difference(X))))
    if len(C_components_V_X) > 1:
        if verbose: print("Depth:", tab, "Line 4 before: Y:", Y, "X:", X, "V:", V, "P:", P.printLatex())
        if verbose: print("Depth:", tab, "Line 4 sumset:", V.difference(Y.union(X)))
        if verbose: print("Depth:", tab, "Line 4 Probabilities:")
        probabilities = set()
        for subcomponent in C_components_V_X:
            subcomponent_vertices = set(subcomponent.vs["name"])
            if verbose: print("Depth:", tab, "Line 4 Y:", subcomponent_vertices, "X:",
                              V.difference(subcomponent_vertices))
            probabilities.add(
                ID_rec(subcomponent_vertices, V.difference(subcomponent_vertices), P, G, ordering, verbose=verbose,
                       tab=tab + 1))
        return Probability(recursive=True, children=probabilities, sumset=V.difference(Y.union(X)))

    # line 5
    C_components = get_C_components(G)
    if len(C_components) == 1:
        if verbose: print("Depth:", tab, "Line 5")
        raise HedgeFound(G, C_components_V_X[0])

    # line 6
    if check_subcomponent(C_components_V_X[0], C_components):
        S = set(C_components_V_X[0].vs["name"])
        if verbose: print("Depth:", tab, "Line 6 before: Y:", Y, "X:", X, "V:", V, "P:", P.printLatex())
        if verbose: print("Depth:", tab, "Line 6 free variables:", P.getFreeVariables())
        if verbose: print("Depth:", tab, "Line 6 S:", S, "Sumset:", S.difference(Y))

        if len(S) == 1:
            if verbose: print("Depth:", tab, "Line 6 S has only 1 element")
            (vertex,) = S
            cond = get_previous_order(vertex, V, ordering)
            if verbose: print("Depth:", tab, "Line 6 var:", vertex, "cond:", cond)
            P_out = get_new_probability(P, {vertex}, cond)
            P_out._sumset = P_out._sumset.union(S.difference(Y))
            return P_out

        if verbose: print("Depth:", tab, "Line 6 Probabilities:")
        probabilities = set()
        for vertex in S:
            cond = get_previous_order(vertex, V, ordering)
            if verbose: print("Depth:", tab, "Line 6 var:", vertex, "cond:", cond)
            P_out = get_new_probability(P, {vertex}, cond)
            probabilities.add(P_out)
        return Probability(recursive=True, children=probabilities, sumset=S.difference(Y))

    # line 7
    for component in C_components:
        if check_subgraph(C_components_V_X[0], component):
            S_comp = set(component.vs["name"])
            if verbose: print("Depth:", tab, "Line 7 before: Y:", Y, "X:", X, "V:", V, "P:", P.printLatex())
            if verbose: print("Depth:", tab, "Line 7 output: Y:", Y, "new X:", X.intersection(S_comp))

            if len(S_comp) == 1:
                if verbose: print("Depth:", tab, "Line 7 S_comp has only 1 element")
                (vertex,) = S_comp
                cond = get_previous_order(vertex, V, ordering).intersection(S_comp).union(
                    get_previous_order(vertex, V, ordering).difference(S_comp))
                if verbose: print("Depth:", tab, "Line 7 var:", vertex, "cond:", cond)
                P_out = get_new_probability(P, {vertex}, cond)
                # P_mock = Probability(var={vertex}, cond=get_previous_order(vertex, V, ordering).intersection(S_comp).union(get_previous_order(vertex, V, ordering).difference(S_comp)))
                # if verbose: print("Depth:", tab, "Line 7 mock ", P_mock.printLatex())
                # if verbose: print("Depth:", tab, "Line 7 out  ", P_out.printLatex())
                if verbose: print("Depth:", tab, "Line 7 with vertex ", vertex, " and probability: ",
                                  P_out.printLatex())
                if verbose: print("Depth:", tab, "Line 7 graph:", printGraph(G.induced_subgraph(G.vs.select(name_in=S_comp))))

                return ID_rec(Y, X.intersection(S_comp), P_out, G.induced_subgraph(G.vs.select(name_in=S_comp)),
                              ordering, verbose=verbose, tab=tab + 1)

            if verbose: print("Depth:", tab, "Line 7 Probabilities has ", len(S_comp), " elements")
            probabilities = set()
            for vertex in S_comp:
                cond = get_previous_order(vertex, V, ordering).intersection(S_comp).union(
                    get_previous_order(vertex, V, ordering).difference(S_comp))
                if verbose: print("Depth:", tab, "Line 7 var:", vertex, "cond:", cond)
                P_out = get_new_probability(P, {vertex}, cond)
                # P_mock = Probability(var={vertex}, cond=get_previous_order(vertex, V, ordering).intersection(S_comp).union(get_previous_order(vertex, V, ordering).difference(S_comp)))
                # if verbose: print("Depth:", tab, "Line 7 mock ", P_mock.printLatex())
                # if verbose: print("Depth:", tab, "Line 7 out  ", P_out.printLatex())
                if verbose: print("Depth:", tab, "Line 7 with vertex ", vertex, " and probability: ",
                                  P_out.printLatex())

                probabilities.add(P_out)
            if verbose: print("Depth:", tab, "Line 7 graph:", printGraph(G.induced_subgraph(G.vs.select(name_in=S_comp))))
            return ID_rec(Y, X.intersection(S_comp), Probability(recursive=True, children=probabilities),
                          G.induced_subgraph(G.vs.select(name_in=S_comp)), ordering, verbose=verbose, tab=tab + 1)
    raise NoCaseTriggered()


def IDC(Y, X, Z, P, G, ordering, verbose=False, tab=0):
    '''Recursive conditional identification algorithm.'''

    # line 1
    for node in Z:
        G_xz = unobserved_graph(G)
        G_xz.delete_edges(G_xz.es.select(_target_in=G_xz.vs.select(name_in=X)))
        G_xz.delete_edges(G_xz.es.select(_source_in=G_xz.vs.select(name_in={node})))
        cond = Z.difference({node})
        if dSep(G_xz, Y, node, X.union(cond), verbose=verbose):
            if verbose: print("Depth:", tab, "Line 1 CONDITIONAL", "New X: ", X.union({node}))
            return IDC(Y, X.union({node}), cond, P, G, ordering, verbose=verbose, tab=tab + 1)

    # line 2
    if verbose: print("Depth:", tab, "Line 2 CONDITIONAL, calling ID_rec with: Y: ", Y.union(Z), " X: ", X)
    prob = ID_rec(Y.union(Z), X, P, G, ordering, verbose=verbose, tab=tab + 1)
    prob_denom = prob.copy()
    prob_denom._sumset = prob_denom._sumset.union(Y)
    prob._fraction = True
    prob._divisor = prob_denom

    return prob


def ID(Y, X, G, cond=set(), verbose=False):
    '''Identification algorithm. If some conditional variables are inputted, then IDC is called.
    Otherwise, ID_rec is called.'''
    
    if len(Y.intersection(X)) + len(Y.intersection(cond)) + len(X.intersection(cond)) != 0:
        raise Exception('Intersection of variables not empty.')
    G_dir, G_bidir = get_directed_bidirected_graphs(G)
    if not G_dir.is_dag():
        raise Exception('Entered graph is not a DAG.')
    if len(cond) == 0:
        return ID_rec(Y, X, Probability(var=set(G.vs["name"])), G, get_topological_ordering(G), verbose=verbose)
    else:
        return IDC(Y, X, cond, Probability(var=set(G.vs["name"])), G, get_topological_ordering(G), verbose=verbose)
