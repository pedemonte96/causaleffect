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

Our evolution as a species made a huge step forward when we understood the relationships between causes and effects. These associations may be trivial for some events, but they are not in complex scenarios. To rigorously prove that some occurrences are caused by others, causal theory and causal inference were formalized, introducing the $do$-operator and its associated rules [@Pearl:1995]. The main goal of this work is to implement in Python some algorithms to compute conditional and non-conditional causal queries from observational data. The theory behind these algorithms, designed by Shpitser and Pearl in 2006 [@Pearl:2006a; @Pearl:2006b], can be found in the extensive technical report [@Pedemonte:2021], where a detailed and thorough study of the algorithms is also presentad. The main identification algorithm can be seen as a repeated application of the rules of $do$-calculus, and it eventually either returns an expression for the causal query from experimental probabilities or fails to identify the causal effect, in which case the effect is non-identifiable. We introduce our newly developed Python library [@causaleffect:2021] and give some usage examples.

# Statement of need

Before the mathematization of causal theory, some philosophers tried to express the sentence "*$X$ causes $Y$*" as "*$X$ raises the probability of $Y$*" by writing $P(Y|X)>P(Y)$, but this is wrong at its core. Note that "raises" is a causal concept which cannot be directly inferenced from observed data. This inequality really affirms that "*if I see $X$, then the probability of $Y$ increases*", but this increase in probability could be for other reasons, like a third variable $Z$ being the cause of $X$ and $Y$.

According to Pearl, who introduced the $do$-operator, for $X$ to be the cause of $Y$ we need to state that "*doing $X$ raises the probability of $Y$*", which would be written as $P(Y|do(X))>P(Y)$. This concept of doing or intervening can be used to solve causal queries. Note that doing is fundamentally different from seeing: by *doing* $X$ we do not care if a third variable is causing $X$ and $Y$ because it is I who is forcing the value on $X$ and not some other background factor. If we conclude that the probability of $Y$ while I force the value of $X$ is bigger than without forcing it, then $X$ is partially responsible for $Y$.

Before the definition of the $do$-operator we could not solve causal queries because we were simply not asking the correct questions, we did not have the necessary tools to even formulate them. This operator has not only allowed us to ask the right questions, but it has also provided us with a set of rules that can help us resolve these queries [@Pearl:1995]. These rules constitute what is known as $do$-calculus, and under some conditions, they can be used to compute causal effects from observational data. When this is possible, this is, when we can use $do$-calculus to compute the effect of a causal relationship, we say that this effect is *identifiable*.

But why is the identification problem relevant in the framework of causal models? When trying to compute a causal effect we could perform the actual intervention in the real world, fixing the value of a variable $X$ and then measuring the other variable $Y$, and seeing if $P(Y|do(X))>P(Y)$. This is not always feasible, sometimes because it is unethical or sometimes because it is simply not viable. Therefore it is of great importance to have a way of computing these interventions without having to actually perform them in reality. This became possible with the introduction of Pearl's $do$-calculus, but lacked a systematic way of calculating causal queries. Years later, a technique to mechanize the estimation of causal effects was eventually developed. This method takes shape as algorithms, designed by Shpitser and Pearl [@Pearl:2006a; @Pearl:2006b], that use the rules of $do$-calculus to compute a certain causal effect, when possible, and that raise an error when the causal effect is not identifiable.

Our project will consist on implementing them in Python, developing a package available to everyone to perform causal effect calculations. This work is relevant because it gathers a set of recent results which are unknown to many computer scientists and statisticians in general. Most of them know about $do$-calculus, but some of them are unaware of the existence of deterministic algorithms that mechanize the process of computing causal effects. There are even some scientists who still think that identifiability and the calculation of causal effects is an open problem. Through this project we want to reach more people, and to make the extraction of causal effects from observational data an effortless procedure.

There is already one implementation of these algorithms for R, by Tikka and Karavanen [@Tikka:2017] under the name of ```causaleffect```, but we believe that implementing them in Python, a very popular programming language amongst data scientists, will make them more known worldwide. According to the TIOBE index \cite{tiobe}, at the moment of this writing Python is the third most popular programming language in the whole world just closely after C and Java, while R falls back to 12<sup>th</sup> place. We therefore strongly believe that developing this package for Python will boost the popularity of the results by Shpitser and Pearl.

The package presented in this work can be used in many different science branches, since causal models appear frequently in fields like econometrics, epidemiology, drug testing or sociology.

# References