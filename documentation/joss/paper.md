---
title: 'Algorithmic Causal Effect Identification with `causaleffect`'
tags:
  - Python
  - DAG
  - do-calculus
  - causality
  - causal model
  - identifiability
  - C-component
  - hedge
  - d-separation
authors:
  - name: Martí Pedemonte
    affiliation: 2
  - name: Jordi Vitrià
    affiliation: 1
  - name: Álvaro Parafita
    affiliation: 1
affiliations:
 - name: Department of Mathematics and Computer Science, Universitat de Barcelona
   index: 1
 - name: Universitat de Barcelona
   index: 2
date: 15 July 2021
bibliography: paper.bib
---

# Summary

Our evolution as a species made a huge step forward when we understood the relationships between causes and effects. These associations may be trivial for some events, but they are not in complex scenarios. To rigorously prove that some occurrences are caused by others, causal theory and causal inference were formalized, introducing the $do$-operator and its associated rules [@Pearl:1995]. The main goal of this work is to implement in Python some algorithms to compute conditional and non-conditional causal queries from observational data. The theory behind these algorithms, designed by Shpitser and Pearl in 2006 [@Pearl:2006a, @Pearl:2006b], can be found in the extensive technical report [@pedemonte2021algorithmic], where a detailed and thorough study of the algorithms is also presentad. The main identification algorithm can be seen as a repeated application of the rules of $do$-calculus, and it eventually either returns an expression for the causal query from experimental probabilities or fails to identify the causal effect, in which case the effect is non-identifiable. We introduce our newly developed Python library [@GithubCausaleffect] and give some usage examples.

# Statement of need

...




# References