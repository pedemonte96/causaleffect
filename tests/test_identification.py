from causaleffect import createGraph, graph, printGraph, Probability, ID, id
import numpy as np
import pytest

def test_fig_3_5_a():
    '''Code in Figure 3.5 (a)'''

    edges = ['X<->Z', 'X<->W', 'X->Z', 'Z->W', 'W->Y', 'X->Y']
    G = createGraph(edges)
    vertices = ['X', 'Y', 'Z', 'W']
    assert np.array_equal(np.array(vertices).sort(), np.array(printGraph(G)[0]).sort())
    assert np.array_equal(np.array(edges).sort(), np.array(printGraph(G)[1]).sort())
    output = 'X-+Z, Z-+W, W-+Y, X-+Y, X-+Z, X+-Z, X-+W, X+-W'
    to_r = graph.to_R_notation(edges)
    assert output == to_r[0] and 5 == to_r[1] and 8 == to_r[2]

def test_fig_3_6_a():
    '''Code in Figure 3.6 (a)'''

    p1 = Probability(var={'X', 'Z'}, cond={'W'})
    p2 = Probability(var={'Y'}, cond={'Z'})
    p3 = Probability(var={'W'})
    p = Probability(recursive=True, children={p1, p2, p3})
    assert p.printLatex(simplify=False) == 'P(w)P(x, z|w)P(y|z)'

def test_fig_3_6_b():
    '''Code in Figure 3.6 (b)'''

    p1 = Probability(var={'X', 'Z'}, cond={'W'})
    p2 = Probability(var={'Y'}, cond={'Z'})
    p3 = Probability(var={'W'})
    p4 = Probability(sumset={'X', 'Z', 'W'}, recursive=True, children={p1, p2, p3})
    p = Probability(sumset={'Z', 'W'}, recursive=True, children={p1, p2, p3}, fraction=True, divisor=p4)
    assert p.printLatex(simplify=False) == '\\frac{\\sum_{w, z}P(w)P(x, z|w)P(y|z)}{\\sum_{w, x, z}P(w)P(x, z|w)P(y|z)}'

def test_fig_3_10():
    '''Code in Figure 3.10'''

    G = createGraph(['X->Z', 'Z->Y', 'X<->Y'])
    P = ID({'Y'}, {'X'}, G)
    assert P.printLatex() == '\\sum_{z}P(z|x)\\left(\\sum_{x}P(x)P(y|x, z)\\right)'

def test_fig_3_12():
    '''Code in Figure 3.12'''

    G = createGraph(['W->X', 'X->Y_1', 'Z->Y_2', 'W<->Y_1', 'W<->Z', 'W<->Y_2', 'X<->Z'])
    P = ID({'Y_1', 'Y_2'}, {'X'}, G)
    assert P.printLatex() == '\\sum_{z}P(y_2, z)\\left(\\sum_{w}P(w)P(y_1|w, x)\\right)'

def test_fig_3_13():
    '''Code in Figure 3.13'''

    G = createGraph(['W->X', 'X->Y_1', 'Z->Y_2', 'W<->Y_1', 'W<->Z', 'W<->Y_2', 'X<->Z', 'W->Z'])
    with pytest.raises(id.HedgeFound) as e_info:
        P = ID({'Y_1', 'Y_2'}, {'X'}, G)

def test_fig_3_15_a():
    '''Code in Figure 3.15 (a)'''

    G = createGraph(['X<->Y', 'Z->Y', 'X->Z', 'W->X', 'W->Z'])
    P = ID({'Y'}, {'X'}, G, cond={'Z'})
    assert P.printLatex() == '\\frac{\\sum_{x}P(x|w)P(y|w, x, z)}{\\sum_{x, y}P(x|w)P(y|w, x, z)}'

def test_fig_3_15_b():
    '''Code in Figure 3.15 (b)'''

    G = createGraph(['X<->Y', 'Z->Y', 'X->Z', 'W->X', 'W->Z'])
    P = ID({'Y'}, {'X'}, G)
    assert P.printLatex() == '\\sum_{w, z}P(w)P(z|w, x)\\left(\\sum_{x}P(x|w)P(y|w, x, z)\\right)'


def test_fig_3_16():
    '''Code in Figure 3.16'''

    G = createGraph(['Z->X', 'Z->Y', 'X->Y'])
    P = ID({'Y'}, {'X'}, G)
    assert P.printLatex() == '\\sum_{z}P(y|x, z)P(z)'
