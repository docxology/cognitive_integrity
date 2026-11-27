# Method

The trust model is described in the program's formal foundations
[@friedman2026integrity]. The implementation combines component scores by
multiplying each by its configured weight and summing the products. With
nonnegative weights summing exactly to unity, a weighted combination of
unit-interval scores stays in that interval [@boyd2004convex]. The software
checks the weight sum with numerical tolerance. The fixture uses exactly
representable weights and inputs.

A delegation path score is the minimum edge score multiplied by the decay
factor raised to the number of edges. With edge scores in the unit interval
and a decay factor strictly between zero and unity, the path score is at
most the minimum edge score. Extending a nonempty path can only preserve or
reduce the minimum and multiplies the decay term by the same factor. This
gives the arithmetic non-amplification property for the stated inputs.

The fixture loads the existing trust module directly and evaluates a weighted
combination and consecutive prefixes of a fixed path. It tests a nonfinite
score and a negative depth as independent invalid-input controls.
