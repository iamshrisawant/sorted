import os
import shutil
import random
import sys
import numpy as np
from sklearn.metrics import f1_score

os.environ["SORTED_TEST_DATA_DIR"] = os.path.abspath("calibration_data")

# Add project root to sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.core.pipelines.builder import build_from_paths
from src.core.pipelines.sorter import sort_file
from src.core.utils.processor import process_file
from benchmark import setup_env

def normalize(path):
    if not path: return "None"
    return os.path.normpath(path).replace('\\', '/')

def calibrate():
    print("===============================================================")
    print("   AUTOMATED THRESHOLD CALIBRATION (MAINLINE)")
    print("===============================================================")
    
    tr_docs, tr_labels = setup_env()
    
    val_set = []
    base_cases = [("invoice.txt", "Invoice for Services", "Work/Finance"), ("stack_trace.txt", "Python Error Log", "Work/Engineering")]
    for _ in range(10):
        for fname, txt, label in base_cases:
             val_set.append((txt, label))
             
    noise_txts = ["Recipe for Cake", "Lyrics to a Song", "Jokes about programmers", "Shopping List"]
    for _ in range(20):
        val_set.append((random.choice(noise_txts), "None"))
        
    print(f"[Setup] Validation Set: {len(val_set)} files (50% Noise).")
    
    # 2. Grid Search
    thresholds = [0.2, 0.4, 0.5, 0.6, 0.7, 0.8]
    best_f1 = -1
    best_thresh = 0.5
    
    # Build FAISS Cloud using Mainline Builder
    print("Building Vector Index via Mainline Builder...")
    build_from_paths([os.path.abspath("benchmark_env")])
    
    print(f"\n{'Threshold':<10} | {'F1-Score':<10}")
    print("-" * 30)

    for thresh in thresholds:
        y_true = []
        y_pred = []
        
        for text, label in val_set:
            tmp_path = os.path.abspath("temp_calib.txt")
            with open(tmp_path, "w", encoding="utf-8") as f: f.write(text)
            
            processed = process_file(tmp_path)
            if not processed or not processed.get("embeddings"):
                pred_label = "None"
            else:
                sorted_data = sort_file(processed)
                # We simulate checking if best_score < thresh
                best_score = 0
                for f, details in sorted_data.get("scoring_breakdown", {}).items():
                    if details["final_score"] > best_score:
                         best_score = details["final_score"]

                if best_score < thresh:
                    pred_label = "None"
                else:
                    rel_dest = os.path.relpath(sorted_data["final_folder"], os.path.abspath("benchmark_env"))
                    pred_label = normalize(rel_dest)

            y_true.append(normalize(label))
            y_pred.append(pred_label)
            if os.path.exists(tmp_path): os.remove(tmp_path)

        f1 = f1_score(y_true, y_pred, average='weighted', zero_division=0)
        print(f"{thresh:<10} | {f1:.4f}")
        if f1 > best_f1:
            best_f1 = f1
            best_thresh = thresh

    print("-" * 30)
    print(f"🏆 Optimal Threshold Found: {best_thresh} (F1: {best_f1:.3f})")
    print("NOTE: You must manually update `threshold` inside `src/core/pipelines/sorter.py` if you wish to apply this.")
    
    # Cleanup
    if os.path.exists("benchmark_env"): shutil.rmtree("benchmark_env")

if __name__ == "__main__":
    calibrate()
