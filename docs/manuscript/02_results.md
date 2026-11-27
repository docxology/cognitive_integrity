# Results

The component scores were 0.25, 0.50, and 0.75, with respective weights
0.25, 0.50, and 0.25. The weighted score was 0.50. The path had edge scores
1.0, 0.75, and 0.50. With decay 0.50, its consecutive prefix scores were
0.50, 0.1875, and 0.0625. The nonfinite score and negative depth each raised
`ValueError`.

![The minimum edge and delegated scores for the fixed path prefixes.](../../output/figures/trust_fixture.png){#fig:trust-fixture width=90%}

The underlying JSON is written by `docs/verification/replay_trust.py`.
The figure pairs each delegated score with the minimum edge at that prefix.
