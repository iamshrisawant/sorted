import os
import shutil
import time
import random
import string
import numpy as np
from sklearn.metrics import f1_score
from scanner import DynamicScanner
from sorter import SemantiSorter
import config
from benchmark import setup_env, generate_noise

def calibrate():
    print("===============================================================")
    print("   AUTOMATED THRESHOLD CALIBRATION")
    print("===============================================================")
    
    # 1. Setup Validation Set (Small, fast)
    tr_docs, tr_labels = setup_env()
    
    # Validation Data: 50% Valid, 50% Noise (None)
    val_set = []
    
    # Valid Cases
    base_cases = [
        ("invoice.txt", "Invoice for Services", "Work/Finance"),
        ("stack_trace.txt", "Python Error Log", "Work/Engineering")
    ]
    for _ in range(10):
        for fname, txt, label in base_cases:
             val_set.append((txt, label))
             
    # Invalid Cases (Noise)
    noise_txts = ["Recipe for Cake", "Lyrics to a Song", "Jokes about programmers", "Shopping List"]
    for _ in range(20):
        txt = random.choice(noise_txts)
        val_set.append((txt, "None"))
        
    print(f"[Setup] Validation Set: {len(val_set)} files (50% Noise).")
    
    # 2. Grid Search
    thresholds = [0.2, 0.3, 0.4, 0.5, 0.6]
    best_f1 = -1
    best_thresh = 0.4
    
    # Initialize Sorter
    config.DEST_DIR = "calibration_env"
    if os.path.exists(config.DEST_DIR): shutil.rmtree(config.DEST_DIR)
    os.makedirs(config.DEST_DIR)
    
    # Scan seeds into calibration env
    # (We need to copy seeds to calibration_env first)
    seed_src = "benchmark_env" # Assuming setup_env created this
    DynamicScanner().scan_directory(seed_src) 
    sorter = SemantiSorter()
    
    results = []

    print(f"\n{'Threshold':<10} | {'F1-Score':<10} | {'Precision':<10} | {'Recall':<10}")
    print("-" * 50)

    for thresh in thresholds:
        config.CONFIDENCE_THRESHOLD = thresh
        y_true = []
        y_pred = []
        
        for text, label in val_set:
            # We create a temp file to satisfy predict_folder interface
            tmp_path = os.path.abspath("temp_calib.txt")
            with open(tmp_path, "w") as f: f.write(text)
            
            p_folder, _, _ = sorter.predict_folder(tmp_path)
            
            # Map Prediction to Class
            pred_label = p_folder if p_folder else "None"
            
            # Binary Classification for Calibration: "Valid" vs "None"
            # Or Multi-class. Let's do Weighted F1 for robustness.
            y_true.append(label)
            y_pred.append(pred_label)
            
            if os.path.exists(tmp_path): os.remove(tmp_path)

        # Calculate Metric
        f1 = f1_score(y_true, y_pred, average='weighted', zero_division=0)
        results.append((thresh, f1))
        
        print(f"{thresh:<10} | {f1:.4f}")
        
        if f1 > best_f1:
            best_f1 = f1
            best_thresh = thresh

    print("-" * 50)
    print(f"🏆 Optimal Threshold Found: {best_thresh} (F1: {best_f1:.3f})")
    
    # 3. Auto-Update Config
    update_config(best_thresh)

def update_config(threshold):
    config_path = "config.py"
    with open(config_path, "r") as f:
        lines = f.readlines()
        
    with open(config_path, "w") as f:
        for line in lines:
            if "CONFIDENCE_THRESHOLD =" in line:
                f.write(f"CONFIDENCE_THRESHOLD = {threshold} # Auto-calibrated\n")
            else:
                f.write(line)
    
    print(f"[Auto-Update] Updated config.py with threshold {threshold}.")

if __name__ == "__main__":
    calibrate()
