"""Deterministic hashing for config-driven corpus naming.

Single responsibility: produce stable SHA256 hashes of serialization configs
so that corpus directories are named by their exact configuration.
Must NOT read or write data files.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from omegaconf import DictConfig, OmegaConf


def hash_config(cfg: DictConfig | dict) -> str:
    """Return the first 12 hex characters of SHA256(canonical JSON of cfg).

    The hash is stable across runs because:
    - JSON keys are sorted
    - OmegaConf is resolved before serialisation (no interpolations)
    - Floats are rounded to 8 significant figures to avoid platform drift

    Args:
        cfg: Hydra DictConfig or plain dict.

    Returns:
        12-character hex string (48 bits — collision-safe for corpus directories).
    """
    if isinstance(cfg, DictConfig):
        cfg = OmegaConf.to_container(cfg, resolve=True)

    canonical = json.dumps(cfg, sort_keys=True, default=_json_default)
    return hashlib.sha256(canonical.encode()).hexdigest()[:12]


def _json_default(obj: object) -> object:
    if isinstance(obj, float):
        return round(obj, 8)
    raise TypeError(f"Not JSON serialisable: {type(obj)}")


def corpus_dir(base: Path, config_hash: str) -> Path:
    """Return the path where a corpus with this config hash should be written."""
    return base / f"corpus_{config_hash}"
