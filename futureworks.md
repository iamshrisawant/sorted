## 1. Zero-Shot Folder Initialization (Semantic Sense)
Allow users to create empty folders and provide a **Natural Language Description** (e.g., "Medical prescriptions and pharmacy bills").
*   **Mechanism**: Encode the description as a "Prototype Vector" in FAISS.
*   **Impact**: Instant sorting capability without requiring existing files to "learn" the category.

## 2. Hybrid Semantic-Lexical Search (Precision Fusion)
Fusing deep semantic meaning with keyword-level exactness.
*   **Mechanism**: Combine FAISS vector results with a local BM25 keyword index via Reciprocal Rank Fusion (RRF).
*   **Impact**: Ensures high-fidelity matching for specific IDs (Invoice #101) while maintaining general semantic intelligence.

## 3. Relational Context (The "Activity Stream")
Files are often related by temporal proximity or cross-categorical linkage.
*   **Temporal Clustering**: weighting k-NN votes by file creation time proximity.
*   **Graph-Vector Hybrid**: Modeling folders as a semantic graph to refine the "Depth Bias" logic.

## 4. UI/UX & Interaction Layer
Enhancing user transparency and control via the CLI and OS integration.
*   **Undo & Resort**: A persistent move history allowing instant rollbacks of automated sorts.
*   **Windows Toast Notifications**: Real-time desktop alerts detailing *what* was moved and *why*.

## 5. Multi-Modality (Vision Integration)
*   **CLIP Research**: Integrating Contrastive Language-Image Pre-training to bring images (screenshots, receipts) into the same vector space as text documents.

## 6. Active Learning (Selection of Information)
*   **Entropy Sampling**: Automatically identifying "Edge Cases" (files that sit on the decision boundary between two folders) and proactively asking the user for clarification to improve model weights exponentially.
