from setuptools import setup

version = '0.0.1'
description = 'Computing causal effects'
long_description = """
# causaleffect

This project implements causal effect identifiability algorithms
and provides functionality for defining and plotting
causal diagrams.

It implements both conditional and non-conditional
causal effect queries from a DAG, and returns a hedge
if the inputted causal effect is not identifiable.

For more information, 
please look at our [Github page](https://github.com/pedemonte96/causaleffect).
"""

with open('requirements.txt') as f:
    install_requires = [line.strip() for line in f if line.strip()]

setup(
    name="causaleffect",
    packages=['causaleffect'],
    version=version,
    description=description,
    long_description=long_description,
    long_description_content_type='text/markdown',
    author="Martí Pedemonte",
    author_email="pedemonte96@gmail.com",
    url='https://github.com/pedemonte96/causaleffect',
    install_requires=install_requires,
    python_requires=">=3.7",
    keywords=['causaleffect', 'causality',
    'causation', 'identifiability', 'identification',
    'graph'],
    classifiers= [
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3",
        "Operating System :: Microsoft :: Windows",
    ]
)