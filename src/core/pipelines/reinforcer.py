import json
import logging
from collections import defaultdict
from pathlib import Path

from src.core.utils.paths import get_logs_path, get_config_file
from src.core.utils.locking import FileLock

# ─── Constants ───────────────────────────────────────────────────────────────
CATEGORY_CORRECTION = "corrections"
DEFAULT_WEIGHTS = {"alpha": 0.6, "beta": 0.3, "gamma": 0.05, "delta": 0.05}
LEARNING_RATE = 0.05

# ─── Logger Setup ────────────────────────────────────────────────────────────
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

# ─── Load Corrections ────────────────────────────────────────────────────────
def load_corrections() -> list:
    log_path = get_logs_path()
    if not log_path.exists():
        raise FileNotFoundError("[Reinforcer] logs.jsonl not found.")

    corrections = []
    with FileLock(log_path):
        with log_path.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if entry.get("category") == CATEGORY_CORRECTION:
                        corrections.append(entry)
                except json.JSONDecodeError:
                    continue
    return corrections

# ─── Load and Save Weights ───────────────────────────────────────────────────
def load_weights() -> dict:
    config_path = get_config_file()
    if not config_path.exists():
        return DEFAULT_WEIGHTS.copy()

    with FileLock(config_path):
        with config_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

    return {
        "alpha": float(data.get("alpha", DEFAULT_WEIGHTS["alpha"])),
        "beta": float(data.get("beta", DEFAULT_WEIGHTS["beta"])),
        "gamma": float(data.get("gamma", DEFAULT_WEIGHTS["gamma"])),
        "delta": float(data.get("delta", DEFAULT_WEIGHTS["delta"])),
    }

def save_weights(weights: dict):
    config_path = get_config_file()
    with FileLock(config_path):
        if config_path.exists():
            with config_path.open("r", encoding="utf-8") as f:
                config = json.load(f)
        else:
            config = {}

        config.update(weights)

        with config_path.open("w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

    logger.info(f"[Reinforcer] Updated weights saved to {config_path.name}")

# ─── Weight Utilities ────────────────────────────────────────────────────────
def normalize_weights(w: dict) -> dict:
    total = sum(w.values())
    return {k: round(v / total, 6) for k, v in w.items()}

def print_weight_diff(before: dict, after: dict):
    logger.info("[Reinforcer] Weight update summary:")
    for k in before:
        delta = round(after[k] - before[k], 6)
        logger.info(f"  {k}: {before[k]} → {after[k]}  ({'+' if delta >= 0 else ''}{delta})")

# ─── Adjustment Calculation ──────────────────────────────────────────────────
def compute_adjustments(corrections: list, current_weights: dict) -> dict:
    over_weight = defaultdict(float)
    under_weight = defaultdict(float)

    for entry in corrections:
        scoring = entry.get("scoring_breakdown", {})
        if not scoring:
            continue

        corrected = Path(entry["final_folder"]).name
        if corrected not in scoring:
            continue

        corrected_score = scoring[corrected].get("final_score")
        if corrected_score is None:
            continue

        for folder, score_data in scoring.items():
            if folder == corrected:
                continue
            original_score = score_data.get("final_score")
            if original_score is None:
                continue

            delta = corrected_score - original_score
            if delta > 0:
                under_weight["alpha"] += delta * score_data.get("mean_similarity", 0)
                under_weight["beta"] += delta * score_data.get("max_similarity", 0)
                under_weight["gamma"] += delta * score_data.get("normalized_match_count", 0)
                under_weight["delta"] += delta * (
                    0.5 * score_data.get("name_match_score", 0) +
                    0.5 * score_data.get("type_affinity_score", 0)
                )
            else:
                delta = -delta
                over_weight["alpha"] += delta * score_data.get("mean_similarity", 0)
                over_weight["beta"] += delta * score_data.get("max_similarity", 0)
                over_weight["gamma"] += delta * score_data.get("normalized_match_count", 0)
                over_weight["delta"] += delta * (
                    0.5 * score_data.get("name_match_score", 0) +
                    0.5 * score_data.get("type_affinity_score", 0)
                )
            break  # Only compare one original folder per correction

    # Apply learning rate to update weights
    new_weights = current_weights.copy()
    for k in new_weights:
        delta = LEARNING_RATE * (under_weight[k] - over_weight[k])
        new_weights[k] += delta
        new_weights[k] = max(0.01, min(1.0, new_weights[k]))

    return normalize_weights(new_weights)

# ─── Main Reinforcement Entry ────────────────────────────────────────────────
def reinforce():
    corrections = load_corrections()
    if not corrections:
        logger.info("[Reinforcer] No corrections to learn from.")
        return

    current_weights = load_weights()
    updated_weights = compute_adjustments(corrections, current_weights)

    print_weight_diff(current_weights, updated_weights)
    save_weights(updated_weights)

# ─── Entrypoints ─────────────────────────────────────────────────────────────
def run_reinforcer():
    reinforce()

if __name__ == "__main__":
    run_reinforcer()
