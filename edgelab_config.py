"""
EdgeLab Config — Evolved Parameter Persistence
-----------------------------------------------
Saves and loads per-tier evolved params.

Storage: JSON file (edgelab_params.json) — human-readable, easy to inspect.
Schema: SQLite-forward. The JSON structure maps directly to what will become
        the `evolved_params` table in edgelab.db when we migrate to SQLite.

Usage:
    from edgelab_config import save_params, load_params
    from edgelab_dpol import LeagueParams

    # Save after a DPOL run
    save_params("E0", lp, accuracy=0.506, matches=3220, source="dpol_session4")

    # Load at start of next DPOL run as starting point
    params = load_params("E0")   # returns LeagueParams or None if not saved yet
"""

import json
import os
import hashlib
import logging
from datetime import datetime
from dataclasses import asdict
from typing import Optional

from edgelab_dpol import LeagueParams

logger = logging.getLogger(__name__)

# Default location — same directory as the scripts
DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "edgelab_params.json")


# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------

def save_params(
    tier: str,
    params: LeagueParams,
    accuracy: float,
    matches: int,
    source: str = "dpol",
    config_path: str = DEFAULT_CONFIG_PATH,
) -> None:
    """
    Save evolved params for a tier to the config file.
    Overwrites any existing entry for that tier.

    Args:
        tier:        League tier string e.g. "E0", "E1"
        params:      LeagueParams instance from DPOL
        accuracy:    Accuracy achieved with these params (e.g. 0.506)
        matches:     Number of matches this was validated on
        source:      Label for where these came from e.g. "dpol_session4"
        config_path: Path to JSON config file
    """
    # Load existing or create fresh
    config = _load_raw(config_path)

    config[tier] = {
        # The params themselves (maps directly to future SQLite columns)
        "params": asdict(params),
        # Metadata
        "accuracy": round(accuracy, 6),
        "matches": matches,
        "source": source,
        "saved_at": datetime.utcnow().isoformat(),
    }

    _write_raw(config, config_path)
    logger.info(f"[Config] Saved params for {tier} — accuracy={accuracy:.1%}, matches={matches}, source={source}")


def save_all_params(
    results: dict,
    config_path: str = DEFAULT_CONFIG_PATH,
) -> None:
    """
    Save evolved params for multiple tiers at once.

    Args:
        results: dict of {tier: {"params": LeagueParams, "accuracy": float, "matches": int}}
                 e.g. the output structure from a full DPOL run
        config_path: Path to JSON config file

    Example:
        save_all_params({
            "E0": {"params": lp_e0, "accuracy": 0.506, "matches": 3220},
            "E1": {"params": lp_e1, "accuracy": 0.444, "matches": 9575},
        })
    """
    for tier, data in results.items():
        save_params(
            tier=tier,
            params=data["params"],
            accuracy=data["accuracy"],
            matches=data["matches"],
            source=data.get("source", "dpol"),
            config_path=config_path,
        )


# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------

def load_params(
    tier: str,
    config_path: str = DEFAULT_CONFIG_PATH,
) -> Optional[LeagueParams]:
    """
    Load saved params for a tier. Returns LeagueParams or None if not found.

    Usage in runner/DPOL:
        saved = load_params("E0")
        starting_params = saved if saved else LeagueParams()
    """
    config = _load_raw(config_path)

    if tier not in config:
        logger.info(f"[Config] No saved params for {tier} — using defaults")
        return None

    entry = config[tier]
    p = entry["params"]

    # Build LeagueParams from saved values, falling back to defaults for
    # any missing keys (forward-compatible if we add params later)
    defaults = LeagueParams()
    lp = LeagueParams(
        w_form=p.get("w_form", defaults.w_form),
        w_gd=p.get("w_gd", defaults.w_gd),
        home_adv=p.get("home_adv", defaults.home_adv),
        dti_edge_scale=p.get("dti_edge_scale", defaults.dti_edge_scale),
        dti_ha_scale=p.get("dti_ha_scale", defaults.dti_ha_scale),
        draw_margin=p.get("draw_margin", defaults.draw_margin),
        coin_dti_thresh=p.get("coin_dti_thresh", defaults.coin_dti_thresh),
        draw_pull=p.get("draw_pull", defaults.draw_pull),
        dti_draw_lock=p.get("dti_draw_lock", defaults.dti_draw_lock),
        instinct_dti_thresh=p.get("instinct_dti_thresh", defaults.instinct_dti_thresh),
        skew_correction_thresh=p.get("skew_correction_thresh", defaults.skew_correction_thresh),
        # Draw intelligence layer — were falling to 0.0 silently (Gap B fix)
        w_draw_odds=p.get("w_draw_odds", 0.0),
        w_draw_tendency=p.get("w_draw_tendency", 0.0),
        w_h2h_draw=p.get("w_h2h_draw", 0.0),
        draw_score_thresh=p.get("draw_score_thresh", defaults.draw_score_thresh),
        # Score prediction — was falling to 0.0 silently (Gap B fix)
        w_score_margin=p.get("w_score_margin", 0.0),
        w_btts=p.get("w_btts", 0.0),
        # Composite draw signal layer — were falling to 0.0 silently (Gap B fix)
        w_xg_draw=p.get("w_xg_draw", 0.0),
        composite_draw_boost=p.get("composite_draw_boost", 0.0),
        # Phase 1 external signals — default 0.0 if not yet in saved params
        w_ref_signal=p.get("w_ref_signal", 0.0),
        w_travel_load=p.get("w_travel_load", 0.0),
        w_timing_signal=p.get("w_timing_signal", 0.0),
        w_motivation_gap=p.get("w_motivation_gap", 0.0),
        # Phase 2 external signals
        w_weather_signal=p.get("w_weather_signal", 0.0),
    )

    logger.info(
        f"[Config] Loaded params for {tier} — "
        f"accuracy={entry['accuracy']:.1%}, matches={entry['matches']}, "
        f"source={entry['source']}, saved={entry['saved_at'][:10]}"
    )
    return lp


def load_all_params(config_path: str = DEFAULT_CONFIG_PATH) -> dict:
    """
    Load all saved tier params. Returns dict of {tier: LeagueParams}.
    Tiers with no saved params are not included.
    """
    config = _load_raw(config_path)
    result = {}
    for tier in config:
        lp = load_params(tier, config_path=config_path)
        if lp:
            result[tier] = lp
    return result


# ---------------------------------------------------------------------------
# Inspect / summary
# ---------------------------------------------------------------------------

def show_config(config_path: str = DEFAULT_CONFIG_PATH) -> None:
    """Print a human-readable summary of all saved params."""
    config = _load_raw(config_path)

    if not config:
        print("[Config] No params saved yet.")
        return

    # Dataset hash
    if "_dataset" in config:
        d = config["_dataset"]
        print(f"\n  Dataset hash : {d['hash']}  (saved {d['saved_at'][:10]})")
    else:
        print(f"\n  Dataset hash : (none stored)")

    print(f"\n{'='*60}")
    print(f"  EdgeLab Evolved Params — {config_path}")
    print(f"{'='*60}")

    for tier, entry in sorted(config.items()):
        if tier.startswith("_"):
            continue  # skip metadata keys like _dataset
        p = entry["params"]
        print(f"\n  Tier: {tier}")
        print(f"    Accuracy : {entry['accuracy']:.1%}  ({entry['matches']} matches)")
        print(f"    Source   : {entry['source']}  |  Saved: {entry['saved_at'][:10]}")
        print(f"    w_form={p['w_form']:.3f}  w_gd={p['w_gd']:.3f}  home_adv={p['home_adv']:.3f}")
        print(f"    draw_margin={p['draw_margin']:.3f}  coin_dti_thresh={p['coin_dti_thresh']:.3f}")
        print(f"    draw_pull={p['draw_pull']:.3f}  dti_draw_lock={p['dti_draw_lock']:.3f}")
        print(f"    dti_edge_scale={p['dti_edge_scale']:.3f}  dti_ha_scale={p['dti_ha_scale']:.3f}")
        # Phase 1 external signal weights — show 0.000 explicitly so we know if they're dormant
        w_ref      = p.get("w_ref_signal",    0.0)
        w_travel   = p.get("w_travel_load",   0.0)
        w_timing   = p.get("w_timing_signal", 0.0)
        w_mot      = p.get("w_motivation_gap",0.0)
        # Phase 2 external signal weights
        w_weather  = p.get("w_weather_signal", 0.0)
        any_active = any(w > 0.0 for w in [w_ref, w_travel, w_timing, w_mot, w_weather])
        status     = "ACTIVE" if any_active else "dormant"
        print(f"    --- Phase 1 signals [{status}] ---")
        print(f"    w_ref_signal={w_ref:.3f}  w_travel_load={w_travel:.3f}  "
              f"w_timing_signal={w_timing:.3f}  w_motivation_gap={w_mot:.3f}")
        print(f"    --- Phase 2 signals ---")
        print(f"    w_weather_signal={w_weather:.3f}")

    print(f"\n{'='*60}\n")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_raw(config_path: str) -> dict:
    if not os.path.exists(config_path):
        return {}
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"[Config] Could not read {config_path}: {e} — starting fresh")
        return {}


def _write_raw(config: dict, config_path: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(config_path)), exist_ok=True)
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)


# ---------------------------------------------------------------------------
# Dataset hash safeguard
# ---------------------------------------------------------------------------

def compute_dataset_hash(csv_folder: str) -> str:
    """
    Fingerprint the CSV dataset so we know if it changes between sessions.

    Strategy: hash a sorted list of (filename, filesize, last-modified-time).
    Fast — doesn't read file contents. Catches new files, deleted files,
    and files that were replaced with different content (size/mtime changes).

    Returns a short hex digest string.
    """
    import glob

    csv_files = sorted(glob.glob(os.path.join(csv_folder, "*.csv")))
    if not csv_files:
        return "empty"

    h = hashlib.md5()
    for path in csv_files:
        fname = os.path.basename(path)
        try:
            stat = os.stat(path)
            entry = f"{fname}:{stat.st_size}:{stat.st_mtime}"
        except OSError:
            entry = f"{fname}:missing"
        h.update(entry.encode())

    return h.hexdigest()[:12]  # 12 chars — enough to detect any change


def save_dataset_hash(csv_folder: str, config_path: str = DEFAULT_CONFIG_PATH) -> str:
    """
    Compute and store the current dataset fingerprint in the config.
    Call this after a successful DPOL run so the hash reflects
    the data those params were trained on.

    Returns the hash string.
    """
    h = compute_dataset_hash(csv_folder)
    config = _load_raw(config_path)
    config["_dataset"] = {
        "hash": h,
        "folder": csv_folder,
        "saved_at": datetime.utcnow().isoformat(),
    }
    _write_raw(config, config_path)
    logger.info(f"[Config] Dataset hash saved: {h}  (folder: {csv_folder})")
    return h


def check_dataset_hash(csv_folder: str, config_path: str = DEFAULT_CONFIG_PATH) -> dict:
    """
    Compare current dataset against the stored hash.

    Returns a dict:
        {
            "status":   "ok" | "changed" | "no_hash",
            "current":  "<hash>",
            "stored":   "<hash>" | None,
            "message":  "<human-readable explanation>",
        }

    "ok"       — data unchanged, params are valid.
    "changed"  — data has changed since params were saved. Re-evolution recommended.
    "no_hash"  — no hash stored yet. Run a DPOL session and save_dataset_hash() to register.
    """
    current = compute_dataset_hash(csv_folder)
    config  = _load_raw(config_path)

    if "_dataset" not in config:
        return {
            "status":  "no_hash",
            "current": current,
            "stored":  None,
            "message": (
                "No dataset fingerprint stored yet. "
                "Run a DPOL session then call save_dataset_hash() to register the baseline."
            ),
        }

    stored = config["_dataset"]["hash"]
    saved_at = config["_dataset"].get("saved_at", "unknown")[:10]

    if current == stored:
        return {
            "status":  "ok",
            "current": current,
            "stored":  stored,
            "message": f"Dataset unchanged since {saved_at}. Params are valid.",
        }
    else:
        return {
            "status":  "changed",
            "current": current,
            "stored":  stored,
            "message": (
                f"Dataset has changed since params were saved ({saved_at}). "
                f"Stored hash: {stored}  Current hash: {current}. "
                "Re-run DPOL evolution to retrain on the updated data."
            ),
        }


# ---------------------------------------------------------------------------
# CLI — python edgelab_config.py show
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "show"
    path = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_CONFIG_PATH

    if cmd == "show":
        show_config(path)
    else:
        print(f"Usage: python edgelab_config.py show [path_to_params.json]")
