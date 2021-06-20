import numpy as np
from igraph import *


# Define some useful graph functions

def plotGraph(g, name=None):
    '''Function that plots a graph. Requires the pycairo library.'''

    color_dict = {0: "blue", 1: "#008833"}
    visual_style = {}
    visual_style["vertex_label_dist"] = 2
    visual_style["vertex_size"] = 20
    visual_style["vertex_label"] = g.vs["name"]
    visual_style["edge_width"] = [1 + 1.5 * (1 - abs(val)) for val in g.es["confounding"]]
    visual_style["edge_color"] = [color_dict[abs(val)] for val in g.es["confounding"]]
    visual_style["edge_curved"] = [(val) * 0.2 for val in g.es["confounding"]]
    visual_style["layout"] = g.layout("circle")
    visual_style["bbox"] = (300, 300)
    visual_style["margin"] = 40
    if name is not None:
        return plot(g, name + ".png", **visual_style)
    return plot(g, **visual_style)


def get_directed_bidirected_graphs(g):
    '''Function that, given a graph, it decouples it and returns confounded graph
    and a graph with visible causations.'''

    adj_bidir = np.asarray(g.get_adjacency().data) + np.asarray(g.get_adjacency().data).T
    adj_bidir[adj_bidir < 2] = 0
    adj_bidir[adj_bidir >= 2] = 1
    adj_dir = np.asarray(g.get_adjacency().data) - adj_bidir
    g_dir = Graph.Adjacency(adj_dir.tolist())
    g_bidir = Graph.Adjacency(adj_bidir.tolist())
    g_dir.vs["name"] = g.vs["name"]
    g_bidir.vs["name"] = g.vs["name"]
    confounding_dir = [0 for edge in g_dir.es]
    confounding_bidir = []
    for edge in g_bidir.es:
        if edge.source_vertex["name"] < edge.target_vertex["name"]:
            confounding_bidir.append(-1)
        else:
            confounding_bidir.append(1)
    g_bidir.es["confounding"] = confounding_bidir
    g_dir.es["confounding"] = confounding_dir
    return g_dir, g_bidir


def get_C_components(g):
    '''Function that returs the different C-components of a graph.'''

    g_dir, g_bidir = get_directed_bidirected_graphs(g)
    g_out = g_bidir.copy()
    for e in g_dir.es:
        if e.target_vertex.index in g_bidir.subcomponent(e.source_vertex.index):
            g_out.add_edge(e.source_vertex.index, e.target_vertex.index)
    return g_out.decompose()


def get_vertices_no_parents(g):
    '''Function that returns the set of vertices without parents'''

    degrees = g.degree(mode="in")
    vertices = []
    for i in range(len(degrees)):
        if degrees[i] == 0:
            vertices.append(g.vs[i]["name"])
    return set(vertices)


def get_topological_ordering(g):
    '''Function that returns the ordering of the vertices of a graph'''

    g_dir, g_bidir = get_directed_bidirected_graphs(g)
    return [g_dir.vs[index]["name"] for index in g_dir.topological_sorting()]


def get_previous_order(v, possible, ordering):
    '''Function that returns all previous vertices of a initial vertex from
    a possible set of vertices and an ordernig of the graph'''

    return set(ordering[:ordering.index(v)]).intersection(possible)


def get_ancestors(g, v_name):
    '''Function that returns a set containing all ancestors of a vertex,
    including itself'''

    if not g.is_dag():
        raise ValueError("Graph contains a cycle")
    ancestors = []
    if type(v_name) == type(set()):
        for e in v_name:
            ancestors += get_ancestors(g, e)
    else:
        ancestors = [v_name]
        parents = [v_name]
        checked = [v_name]
        while len(parents) > 0:
            name_vertex = parents.pop(0)
            checked.append(name_vertex)
            new_neighbors = g.neighbors(g.vs.find(name=name_vertex), mode="in")
            for i in range(len(new_neighbors)):
                if g.vs[new_neighbors[i]]["name"] not in ancestors:
                    ancestors.append(g.vs[new_neighbors[i]]["name"])
                if g.vs[new_neighbors[i]]["name"] not in parents and g.vs[new_neighbors[i]]["name"] not in checked:
                    parents.append(g.vs[new_neighbors[i]]["name"])
    return set(ancestors)


def get_descendants(g, v_name):
    '''Function that returns a set containing all descendants of a vertex,
    including itself'''

    if not g.is_dag():
        raise ValueError("Graph contains a cycle")
    descendants = []
    if type(v_name) == type(set()):
        for e in v_name:
            descendants += get_descendants(g, e)
    else:
        descendants = [v_name]
        children = [v_name]
        checked = [v_name]
        while len(children) > 0:
            name_vertex = children.pop(0)
            checked.append(name_vertex)
            new_neighbors = g.neighbors(g.vs.find(name=name_vertex), mode="out")
            for i in range(len(new_neighbors)):
                if g.vs[new_neighbors[i]]["name"] not in descendants:
                    descendants.append(g.vs[new_neighbors[i]]["name"])
                if g.vs[new_neighbors[i]]["name"] not in children and g.vs[new_neighbors[i]]["name"] not in checked:
                    children.append(g.vs[new_neighbors[i]]["name"])
    return set(descendants)


def graphs_are_equal(g1, g2):
    '''Function that checks if two given graphs are equal'''

    return check_subgraph(g1, g2) and check_subgraph(g2, g1)


def check_subcomponent(subcomponent, components):
    '''Function that checks if a graph is part of a set of graphs'''

    for g in components:
        if graphs_are_equal(subcomponent, g):
            return True
    return False


def check_subgraph(g1, g2):
    '''Function that checks ig a graph g1 is a subgraph of g2'''

    # Check that g1<g2
    g1_vertices = set(g1.vs["name"])
    g2_vertices = set(g2.vs["name"])
    if not g1_vertices.issubset(g2_vertices):
        return False
    if len(g1.es) > len(g2.es):
        return False
    # check edges g1 included in g2
    for edge in g1.es:
        source = edge.source_vertex["name"]
        target = edge.target_vertex["name"]
        outgoing_vertices = g2.vs(g2.neighbors(g2.vs.find(name=source), mode="out"))["name"]
        if target not in outgoing_vertices:
            return False
    return True


def createGraph(list_edges_string, verbose=False):
    '''Creates a graph from a list of edges in string-format.'''

    vertices = []
    edges = []
    confounding = []
    for e in list_edges_string:
        conf = 0
        e = e.replace(" ", "")
        endpoints = e.replace("<", "").replace("-", "").replace(">", "")
        for i in range(1, len(endpoints)):
            if endpoints[i].isalpha():
                vertex1, vertex2 = endpoints[:i], endpoints[i:]
                break
        e = e.replace(vertex1, "").replace(vertex2, "")
        index1, index2 = -1, -1
        if vertex1 in vertices:
            index1 = vertices.index(vertex1)
        else:
            index1 = len(vertices)
            vertices.append(vertex1)
        if vertex2 in vertices:
            index2 = vertices.index(vertex2)
        else:
            index2 = len(vertices)
            vertices.append(vertex2)
        if (e[0] == '<'):
            conf += 1
            edges.append((index2, index1))
        if (e[-1] == '>'):
            conf += 1
            edges.append((index1, index2))
        # confounding edge
        if (conf == 2):
            confounding.append(1)
            confounding.append(-1)
        else:
            confounding.append(0)

    if verbose: print(vertices)
    if verbose: print(edges)
    if verbose: print(confounding)
    g = Graph(vertex_attrs={"name": vertices}, edges=edges, directed=True)

    g.es["confounding"] = confounding
    return g


def to_R_notation(edges):
    '''Function that, given a list of strings containing the edges of a graph, returns
    the equivalent graph information for causaleffect package in R.'''

    # ["X->Y", "X<-A", "X<-E", "X<-V", "Y<-A", "Y<-H_1", "Y<-G", "Y<-V", "Y<-H", "Y<-E", "H->V", "V->E"]
    bidirected = []
    final_bidirected = []
    for i, e in enumerate(edges):
        e = e.replace("<", "+")
        e = e.replace(">", "+")
        edges[i] = e
        if e.count("+") == 2:
            bidirected.append(e)
    directed = [e for e in edges if e not in bidirected]

    for e in bidirected:
        one = e.replace("+", "", 1)
        two = e[::-1].replace("+", "", 1)[::-1]
        final_bidirected.append(one)
        final_bidirected.append(two)

    out = ', '.join(directed + final_bidirected)
    return out, len(directed) + 1, len(directed) + len(final_bidirected)


def unobserved_graph(g):
    '''Constructs a causal diagram where confounded variables have explicit unmeasurable nodes
    from a DAG of bidirected edges'''

    G = g.copy()
    vertices = G.vs["name"]
    delete_edges = []
    add_edges = []
    for e in G.es:
        if e["confounding"] != 0:
            delete_edges.append(e.index)
            if e["confounding"] == 1:
                new_vertex_name = G.vs[e.source]["name"] + G.vs[e.target]["name"]
            if e["confounding"] == -1:
                new_vertex_name = G.vs[e.target]["name"] + G.vs[e.source]["name"]
            src = -1
            if new_vertex_name in vertices:
                src = vertices.index(new_vertex_name)
            else:
                src = len(vertices)
                vertices.append(new_vertex_name)
                G.add_vertices(1)
                G.vs[-1]["name"] = new_vertex_name
            add_edges.append((src, e.target))
    G.add_edges(add_edges)
    G.delete_edges(delete_edges)
    G.es["confounding"] = [0 for i in G.es]

    return G


def dSep(G, Y, node, cond, verbose=False):
    '''Checks if node and the set Y are d-separated, given the whole graph G and the measured variables cond'''

    if verbose: print('dSep: dSep of node:', node, ' to set: ', Y)
    for y in Y:
        if verbose: print('dSep: Path from ', y, ' to ', node)
        paths = G.get_all_simple_paths(v=G.vs.find(name_eq=node), to=G.vs.find(name_eq=y), mode='ALL')
        if verbose: print('dSep: All possible paths: ', paths)
        for p in paths:
            if verbose:
                p_name = []
                for i in p:
                    p_name.append(G.vs[i]["name"])
                print('dSep: Path:', p, p_name)
            if not is_path_d_separated(G, p, cond, verbose=verbose):
                return False
    # If all paths are d-separated, return True
    return True


def is_path_d_separated(G, p, cond, verbose=False):
    '''Checks if a path is d-separated, given the whole graph G and the measured variables cond'''

    if verbose: print('is_path_d_separated: Path ', p, 'Conditional: ', cond)
    if G.vs[p[0]]["name"] in cond or G.vs[p[-1]]["name"] in cond:
        raise Exception('Source or target nodes in conditional d-separation path')
    for i in range(len(p) - 2):
        e1, e2 = '', ''
        if len(G.es.select(_source=p[i]).select(_target=p[i + 1])):
            if verbose: print(G.vs[p[i]]["name"], '->', G.vs[p[i + 1]]["name"])
            e1 = 'r'
        if len(G.es.select(_source=p[i + 1]).select(_target=p[i])):
            if verbose: print(G.vs[p[i]]["name"], '<-', G.vs[p[i + 1]]["name"])
            if e1 == 'r':
                e1 = 'b'
            else:
                e1 = 'l'
        if len(G.es.select(_source=p[i + 1]).select(_target=p[i + 2])):
            if verbose: print(G.vs[p[i + 1]]["name"], '->', G.vs[p[i + 2]]["name"])
            e2 = 'r'
        if len(G.es.select(_source=p[i + 2]).select(_target=p[i + 1])):
            if verbose: print(G.vs[p[i + 1]]["name"], '<-', G.vs[p[i + 2]]["name"])
            if e2 == 'r':
                e2 = 'b'
            else:
                e2 = 'l'

        if ((e1 == 'r' and e2 == 'r') or (e1 == 'l' and e2 == 'l') or (e1 == 'l' and e2 == 'r') or
                (e1 == 'l' and e2 == 'b') or (e1 == 'b' and e2 == 'r')):  # -> -> // <- <- // <- -> // <- <-> // <-> ->
            if G.vs[p[i + 1]]["name"] in cond:
                if verbose: print('is_path_d_separated: Chain or Fork:', G.vs[p[i]]["name"], e1, G.vs[p[i+1]]["name"], e2, G.vs[p[i+2]]["name"])
                return True

        if ((e1 == 'r' and e2 == 'l') or (e1 == 'r' and e2 == 'b') or (e1 == 'b' and e2 == 'l') or
                (e1 == 'b' and e2 == 'b')):  # -> <- // -> <-> // <-> <- // <-> <->
            G_dir, G_bidir = get_directed_bidirected_graphs(G)
            if len(get_descendants(G_dir, G.vs[p[i + 1]]["name"]).intersection(cond)) == 0:
                if verbose: print('is_path_d_separated: Collider:', G.vs[p[i]]["name"], e1, G.vs[p[i+1]]["name"], e2, G.vs[p[i+2]]["name"])
                return True
    if verbose: print('is_path_d_separated: d-connected path ', p, 'Conditional: ', cond)
    return False


def printGraph(G):
    '''Function that returns a tuple with list of nodes and a list of edges of the graph.'''

    edges = []
    confounded = []
    for edge in G.es:
        if edge["confounding"] == -1:
            confounded.append(edge.source_vertex["name"] + "<->" + edge.target_vertex["name"])
        elif edge["confounding"] == 1:
            confounded.append(edge.target_vertex["name"] + "<->" + edge.source_vertex["name"])
        else:
            edges.append(edge.source_vertex["name"] + "->" + edge.target_vertex["name"])
    confounded = list(set(confounded))
    nodes = G.vs["name"]
    return nodes, edges + confounded
