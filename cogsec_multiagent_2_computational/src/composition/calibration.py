"""Per-module decision thresholds, and why calibrating them does not rescue detection.

Every defense adapter ships ``threshold = 0.5``. They do not share a score
scale, so one number cannot be right for all of them, and the obvious next move
is to calibrate each against benign traffic. That move was made, and it failed
for a reason worth recording.

The trap
--------
``ablation.runner.BENIGN_MESSAGES`` is a 50-message convenience set of plainly
innocuous text. Calibrated against it, the modules look badly mis-set: six never
score it above 0.0, and moving each threshold to its own benign ceiling appears
to lift whole-pipeline detection from 17% to 74%. That number is an artifact of
the negative set, not a property of the detectors.

``evaluation.benign_corpus.BenignCorpus`` is the designed negative arm: 120
items, half of them a ``hard`` stratum of legitimate messages that deliberately
carry attack-adjacent vocabulary. Against it the picture inverts. The tripwire
adapter scores benign text at 1.000. The firewall reaches 0.560 and the
detection module 0.514 -- both above the very threshold they ship with. And at
the pipeline level, Youden's J is *negative* at every threshold below 0.56:
raising detection raises false positives faster than it raises recall.

    tau     TPR    FPR(all)   FPR(hard stratum)
    0.30   0.778     0.900         0.867
    0.40   0.285     0.358         0.550
    0.50   0.142     0.192         0.300
    0.60   0.039     0.000         0.000

The conclusion is not "the thresholds are mis-set". It is that the score
distributions of attacks and of hard benign text overlap almost completely, so
no threshold separates them. Peak J across the whole range is 0.043.

Which is why the defaults are left at 0.5. A calibrated threshold cannot buy
detection that the scores do not contain, and shipping one derived from the
easy negative set would have encoded a 74% claim that the hard set refutes.
:func:`calibrate` remains available for deployments with real benign traffic,
with the warning attached.
"""

from __future__ import annotations

from typing import Iterable

#: Added above the observed benign ceiling, so that a module scoring benign
#: traffic at exactly zero does not end up firing on arbitrarily small noise.
MARGIN: float = 0.01

#: What every adapter ships. Uniform across eight different score scales, which
#: is not a calibration -- but see the module docstring for why replacing it
#: with per-module thresholds does not help on this corpus.
DEFAULT_THRESHOLD: float = 0.5

#: Thresholds derived from the *hard* negative arm, for reference. They are not
#: the shipped defaults: against that corpus they cost more detection than they
#: save in false positives, which is the finding rather than a tuning failure.
BENIGN_CEILING_THRESHOLDS = {
    "firewall": 0.5699,
    "detection": 0.5244,
    "invariants": 0.5100,
    "trust": 0.4100,
    "consensus": 0.3475,
    "sandbox": 0.1600,
    "provenance": 0.0100,
    # The tripwire adapter scores legitimate text at 1.000, so a threshold that
    # avoids false positives on the hard stratum also makes it unable to fire
    # at all. That is a defect in the adapter, not a calibration to ship.
    "tripwire": 1.0100,
}


def calibrate(scorer, benign: Iterable[str], *, margin: float = MARGIN) -> float:
    """Derive a threshold as the benign ceiling plus a margin.

    The result is only as good as *benign*. Calibrating against easy negative
    examples produces a threshold that looks excellent and fails on traffic
    that merely mentions the words an attack would use; that is precisely the
    error this module documents. Use the hardest legitimate traffic available.
    """
    scores = [scorer.evaluate(message).score for message in benign]
    return round((max(scores) if scores else 0.0) + margin, 4)
