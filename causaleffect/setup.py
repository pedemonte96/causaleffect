from setuptools import setup, find_packages

VERSION = '0.0.1'
DESCRIPTION = 'Causal effect package'
LONG_DESCRIPTION = 'Causal effect package'

# Setting up
setup(
    name="causaleffect",
    version=VERSION,
    author="Martí Pedemonte",
    author_email="pedemonte96@gmail.com",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    packages=find_packages(),
    install_requires=['pycairo'],

    keywords=['python', 'causaleffect'],
    classifiers= [
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Education",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
    ]
)