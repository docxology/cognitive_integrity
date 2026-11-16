# Cognitive Security Source Modules - Quick Reference

Core implementations for the Cognitive Integrity Framework (CIF).

## Modules

| Module | Purpose | Key Exports |
|--------|---------|-------------|
| `trust.py` | Trust calculus with decay | `TrustCalculus`, `TrustMatrix`, `ReputationTracker` |
| `firewall.py` | Input classification | `CognitiveFirewall`, `PatternDetector`, `Classification` |
| `semantic_backend.py` | Explicit pinned, offline MiniLM encoder | `PinnedSentenceTransformerEncoder` |
| `consensus.py` | Byzantine agreement | `ByzantineConsensus`, `QuorumVerification`, `Vote` |
| `tripwire.py` | Canary monitoring | `CognitiveTripwire`, `Canary`, `TripwireAlert` |
| `provenance.py` | Information flow | `ProvenanceChain`, `TaintLabel`, `CausalAttribution` |
| `detection.py` | Anomaly detection | `DriftDetector`, `AnomalyScorer`, `DetectionConfig` |
| `invariants.py` | Behavioral checking | `InvariantChecker`, `RuntimeMonitor`, `AgentAction` |
| `sandbox.py` | Belief partitioning | `SandboxManager`, `BeliefState`, `PromotionCriteria` |

## Quick Usage

### Trust Evaluation
```python
from src.trust import TrustCalculus
calc = TrustCalculus()
trust = calc.compute_trust(base_trust=0.8, reputation=0.9, context_trust=0.7)
```

### Firewall Classification
```python
from src.firewall import CognitiveFirewall, Classification
fw = CognitiveFirewall()
result = fw.classify("Hello world")  # Classification.ACCEPT
```

### Explicit Semantic Backend

`SemanticSimilarityDetector` and `MultiStageClassifier` require
`embedding_fn=encode`. `EnhancedCognitiveFirewall(use_semantic=True, ...)`
requires the same callable; its default non-semantic mode needs no backend.
There is no default encoder, model download, hash embedder or heuristic fallback.

The optional `semantic` extra pins **sentence-transformers==6.3.0**. The provided
`PinnedSentenceTransformerEncoder(model_dir)` accepts only an explicit local
directory containing **sentence-transformers/all-MiniLM-L6-v2**, immutable revision
**1110a243fdf4706b3f48f1d95db1a4f5529b4d41** ([model files](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/tree/1110a243fdf4706b3f48f1d95db1a4f5529b4d41),
Apache-2.0). It verifies the installed backend version and local provenance before
loading with `device="cpu"`, `backend="torch"`, `local_files_only=True`,
`trust_remote_code=False`, `token=False` and `use_safetensors=True`.
Imports and non-semantic mode do not import the optional backend or load a model.

```python
from pathlib import Path
from src import EnhancedCognitiveFirewall, PinnedSentenceTransformerEncoder

# The application must explicitly select a previously provisioned directory.
def classify_with_local_model(message, model_dir: Path):
    encode = PinnedSentenceTransformerEncoder(model_dir)
    firewall = EnhancedCognitiveFirewall(use_semantic=True, embedding_fn=encode)
    return firewall.classify_detailed(message)
```

For repeated messages, construct and retain one encoder/firewall rather than
reloading the weights. Encoding uses the pinned tokenizer, truncation, pooling
and normalization configuration with float32 sentence embeddings and no added
prompt. The model's `Normalize` module is retained; `normalize_embeddings=False`
disables only additional encode-level normalization. The detector normalizes each
finite, nonzero 384-dimensional vector and scores nonnegative cosine similarity
to registered patterns. Other caller-supplied trained encoders remain supported
under the same one-dimensional, real, consistent-dimension vector contract.

#### Model provenance and offline loading

Provision model files separately from the exact revision above. No runtime path
downloads files or tries another model. Required files are `config.json`,
`config_sentence_transformers.json`, `modules.json`, `sentence_bert_config.json`,
`tokenizer_config.json`, `tokenizer.json`, `special_tokens_map.json`, `vocab.txt`,
`1_Pooling/config.json`, `model.safetensors`, and the model's `README.md`.
Record acquisition from the immutable Hugging Face revision metadata, checking
ordinary files against their Git blob SHA1 and weights against the published LFS
SHA256. The pinned weights have **90,868,376 bytes** and SHA256
`53aa51172d142c89d9012cce15ae4d6cc0ca6895895114379cacb4fab128d9db`.

Place `model_manifest.json` beside these files with this minimal JSON contract:
`schema_version` is integer `1`; `model_id` and `revision` are the exact strings
above; `files` maps each POSIX relative file name to an object containing integer
`bytes` and lowercase hexadecimal `sha256`. Optional per-file `git_blob` records
the acquisition metadata. List every downloaded file except the manifest itself.
Construction checks the pinned identity, known weight digest/size, exact local
file set and every file's byte count/SHA256; symlinks and unsafe paths are rejected.
The manifest is a trusted acquisition receipt, not an author signature; it does
not independently authenticate editable metadata against Hugging Face.
Keep the provisioned directory immutable after verification/loading. Neither
model weights nor environment-local acquisition receipts belong in source control.

With the optional dependency closure already cached and the model provisioned:

```bash
uv sync --frozen --extra semantic --offline
COGSEC_EMBEDDING_MODEL_DIR="$PWD/.venv/offline-models/all-MiniLM-L6-v2-1110a243" \
  HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  .venv/bin/python -m pytest tests/test_firewall.py -q
```

The real-model tests skip only when `COGSEC_EMBEDDING_MODEL_DIR` is unset. Selecting
an empty, missing or invalid directory, missing dependency, wrong backend version,
or failed model load is an error, not a skip. They compare trained-vector rankings
for reworded malicious examples against unrelated benign messages and exercise
firewall calls without retuning thresholds; this is a narrow regression, not
field-effectiveness evidence. Isolated vector doubles cover only boundary behavior.
Missing/noncallable `embedding_fn` raises `ValueError`; malformed, zero, nonfinite
or dimension-changing vectors do too. Encoder execution failures propagate as
`RuntimeError` with the original cause, never ACCEPT or a zero-risk fallback.

### Byzantine Consensus
```python
from src.consensus import ByzantineConsensus, Vote
consensus = ByzantineConsensus(n_agents=7)
consensus.submit_vote(Vote("agent-0", "prop", 0.9))
```

### Tripwire Detection
```python
from src.tripwire import CognitiveTripwire
tw = CognitiveTripwire()
tw.add_identity_canary("agent-1")
alerts = tw.check({"I am agent agent-1": 0.3})  # Returns alerts
```

## Dependencies

- `numpy>=1.22` - Numerical computations for trust matrices and statistics
- Standard library: `dataclasses`, `datetime`, `enum`, `re`, `logging`
- Optional `semantic` extra: `sentence-transformers==6.3.0` and its locked dependencies;
  a separately provisioned pinned model is also required.

## All modules follow the thin orchestrator pattern - they implement algorithms, scripts coordinate.
