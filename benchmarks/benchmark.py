"""Measure graph construction and effect identification times."""

from timeit import repeat

from causaleffect import ID, createGraph

EDGES = ["X<->Y", "Z->Y", "X->Z", "W->X", "W->Z"]
GRAPH = createGraph(EDGES)


def build_graph() -> None:
    """Build the example causal graph."""
    createGraph(EDGES)


def identify_effect() -> None:
    """Identify the example intervention effect."""
    ID({"Y"}, {"X"}, GRAPH)


if __name__ == "__main__":
    for name, operation in (("createGraph", build_graph), ("ID", identify_effect)):
        seconds = min(repeat(operation, number=100, repeat=5)) / 100
        print(f"{name}: {seconds * 1000:.3f} ms/call")
