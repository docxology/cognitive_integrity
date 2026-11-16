"""Explicit, provenance-checked local MiniLM encoder for the semantic firewall."""

from __future__ import annotations

import hashlib
import json
import re
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import numpy as np

BACKEND_VERSION = "6.3.0"
MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
MODEL_WEIGHTS_SHA256 = "53aa51172d142c89d9012cce15ae4d6cc0ca6895895114379cacb4fab128d9db"
MODEL_WEIGHTS_BYTES = 90868376
MANIFEST_NAME = "model_manifest.json"
_REQUIRED_FILES = frozenset(
    {
        "1_Pooling/config.json",
        "README.md",
        "config.json",
        "config_sentence_transformers.json",
        "model.safetensors",
        "modules.json",
        "sentence_bert_config.json",
        "special_tokens_map.json",
        "tokenizer.json",
        "tokenizer_config.json",
        "vocab.txt",
    }
)


def _verified_model_directory(model_dir: str | Path) -> Path:
    """Check a trusted acquisition manifest and its complete local file set."""
    root = Path(model_dir).expanduser()
    if not root.is_dir():
        raise FileNotFoundError(f"Configured semantic model directory is unavailable: {root}")
    root = root.resolve()
    manifest_path = root / MANIFEST_NAME
    if manifest_path.is_symlink():
        raise ValueError(f"Semantic model manifest must not be a symlink: {manifest_path}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError(f"Invalid semantic model manifest: {manifest_path}") from exc
    if (
        not isinstance(manifest, dict)
        or type(manifest.get("schema_version")) is not int
        or manifest["schema_version"] != 1
        or manifest.get("model_id") != MODEL_ID
        or manifest.get("revision") != MODEL_REVISION
    ):
        raise ValueError(
            f"{manifest_path}: expected schema 1 and pinned {MODEL_ID}@{MODEL_REVISION}"
        )
    files = manifest.get("files")
    if not isinstance(files, dict) or not _REQUIRED_FILES.issubset(files):
        raise ValueError(f"{manifest_path}: files must include all required model/tokenizer files")
    weights = files["model.safetensors"]
    if (
        not isinstance(weights, dict)
        or weights.get("sha256") != MODEL_WEIGHTS_SHA256
        or weights.get("bytes") != MODEL_WEIGHTS_BYTES
    ):
        raise ValueError(f"{manifest_path}: model.safetensors does not identify the pinned weights")

    present = set()
    for entry in root.rglob("*"):
        if entry.is_symlink():
            raise ValueError(f"Semantic model files must not be symlinks: {entry}")
        if entry.is_file():
            present.add(entry.relative_to(root).as_posix())
    if present - {MANIFEST_NAME} != set(files):
        raise ValueError(f"{manifest_path}: local file set differs from the acquisition manifest")
    for name, record in files.items():
        relative = Path(name)
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or relative.as_posix() != name
            or name == MANIFEST_NAME
        ):
            raise ValueError(f"{manifest_path}: unsafe model file path {name!r}")
        if (
            not isinstance(record, dict)
            or type(record.get("bytes")) is not int
            or record["bytes"] < 0
            or not isinstance(record.get("sha256"), str)
            or re.fullmatch(r"[0-9a-f]{64}", record["sha256"]) is None
        ):
            raise ValueError(f"{manifest_path}: invalid byte/hash record for {name!r}")
        path = root / relative
        if path.stat().st_size != record["bytes"]:
            raise ValueError(f"Semantic model byte count mismatch: {path}")
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        if digest != record["sha256"]:
            raise ValueError(f"Semantic model SHA256 mismatch: {path}")
    return root


class PinnedSentenceTransformerEncoder:
    """Load the pinned trained model from an explicit, immutable local directory.

    Install the ``semantic`` extra separately. Construction verifies
    ``model_manifest.json`` and every file before loading only safetensors on
    CPU. There is no Hub lookup, download, remote code or fallback encoder.
    Keep the directory unchanged after construction. The manifest is an audit
    receipt from trusted acquisition, not a signature authenticating its author.
    """

    def __init__(self, model_dir: str | Path):
        root = _verified_model_directory(model_dir)
        try:
            installed = version("sentence-transformers")
        except PackageNotFoundError as exc:
            raise RuntimeError(
                f"Semantic backend requires sentence-transformers=={BACKEND_VERSION}; "
                "install the semantic extra before loading the local model."
            ) from exc
        if installed != BACKEND_VERSION:
            raise RuntimeError(
                f"Semantic backend requires sentence-transformers=={BACKEND_VERSION}; "
                f"found {installed}."
            )
        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(
                str(root),
                device="cpu",
                revision=MODEL_REVISION,
                local_files_only=True,
                trust_remote_code=False,
                token=False,
                backend="torch",
                model_kwargs={"use_safetensors": True},
            )
        except Exception as exc:
            raise RuntimeError(
                f"Cannot load the pinned semantic model from {root}; "
                "all model files and semantic dependencies must be provisioned offline."
            ) from exc

    def __call__(self, text: str) -> np.ndarray:
        """Encode one text using the model's pinned tokenizer and pooling config."""
        return np.asarray(
            self._model.encode(
                text,
                device="cpu",
                precision="float32",
                convert_to_numpy=True,
                convert_to_tensor=False,
                normalize_embeddings=False,
                show_progress_bar=False,
            )
        )
