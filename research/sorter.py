import os
import shutil
import pickle
import time
import math
import numpy as np
import torch
from sentence_transformers import SentenceTransformer, util
import config
from utils import extract_text

class SortedEngine:
    def __init__(self):
        print("Loading Sorted Engine (Bi-Encoder)...")
        self.bi_encoder = SentenceTransformer(config.BI_ENCODER_MODEL)
        self.load_index()

    def load_index(self):
        if os.path.exists(config.INDEX_PATH):
            with open(config.INDEX_PATH, 'rb') as f:
                self.instances = pickle.load(f)
            if self.instances:
                self.vectors = np.array([i['vector'] for i in self.instances])
            else:
                self.vectors = None
        else:
            self.instances = []
            self.vectors = None

    def save_index(self):
        with open(config.INDEX_PATH, 'wb') as f:
            pickle.dump(self.instances, f)
            
    def predict_folder(self, file_path):
        """
        Rank-Weighted k-NN + Depth Bias Algorithm.
        Includes Open-Set Recognition (returns None if < Threshold).
        """
        start = time.time()
        
        text = extract_text(file_path)
        if not text: return None, 0, "Error:Empty"
        
        if self.vectors is None or len(self.vectors) == 0:
            return None, 0, "Error:NoIndex"
            
        # Contextual Embedding
        fname = os.path.basename(file_path)
        # Extract text already applies header+footer logic if needed
        full_text = f"{fname}\n{text}" 
        emb = self.bi_encoder.encode(full_text)
        
        # Step 1: Retrieval
        scores = util.cos_sim(emb, self.vectors)[0]
        
        # Top K
        k = min(config.K_NEIGHBORS, len(self.instances))
        top_res = torch.topk(scores, k=k)
        
        folder_votes = {}
        
        # Step 2: Scoring with Rank Decay
        indices = top_res.indices.tolist()
        values = top_res.values.tolist()
        
        for rank, (idx, raw_sim) in enumerate(zip(indices, values)):
            instance = self.instances[idx]
            folder = instance['path']
            
            # Logarithmic Decay: Rank 0 -> /1, Rank 1 -> /1.58 ...
            decay = math.log2(rank + 2)
            weighted_score = raw_sim / decay
            
            if folder not in folder_votes:
                folder_votes[folder] = 0.0
            folder_votes[folder] += weighted_score
            
        # Step 3: Depth Bias & Thresholding
        best_score = -float('inf')
        best_folder = None
        
        for folder, vote in folder_votes.items():
            depth = len(folder.split('/')) 
            bias = depth * config.DEPTH_WEIGHT
            final_score = vote + bias
            
            if final_score > best_score:
                best_score = final_score
                best_folder = folder
                
        latency = (time.time() - start) * 1000
        
        # Open-Set Recognition Check
        if best_score < config.CONFIDENCE_THRESHOLD:
            return None, latency, f"Rejected (Score {best_score:.2f} < {config.CONFIDENCE_THRESHOLD})"
            
        return best_folder, latency, f"Rank-Weighted k-NN ({best_score:.2f})"

    def sort_file(self, file_path):
        print(f"Sorting: {os.path.basename(file_path)}")
        folder, lat, method = self.predict_folder(file_path)
        
        if folder:
            print(f"  -> {folder} [{method}] ({lat:.1f}ms)")
            target_dir = os.path.join(config.DEST_DIR, folder)
            os.makedirs(target_dir, exist_ok=True)
            dest_path = os.path.join(target_dir, os.path.basename(file_path))
            try:
                shutil.move(file_path, dest_path)
                
                # Online Learning: Add new instance immediately
                new_text = f"{os.path.basename(file_path)}\n{extract_text(dest_path)}"
                new_vec = self.bi_encoder.encode(new_text)
                self.instances.append({
                    'path': folder.replace('\\', '/'),
                    'vector': new_vec,
                    'filename': os.path.basename(file_path)
                })
                if self.vectors is not None:
                    self.vectors = np.vstack([self.vectors, new_vec])
                else:
                    self.vectors = np.array([new_vec])
                self.save_index()
                
            except Exception as e:
                print(f"Error moving: {e}")
        else:
            print(f"  -> Classification failed/rejected. [{method}]")
