# Sorted (SortedPC)

![Pipeline Diagram](assets/pipeline.png)

**Sorted** is a local-first file organization utility that monitors directories and classifies incoming files based on semantic similarity. It operates entirely offline using a local embedding pipeline and vector retrieval engine.

---

## Technical Architecture

Sorted is built as a decoupled system featuring a Python-based background daemon and a management interface.

### 1. Event-Driven Monitoring
The system utilizes the `watchdog` library to intercept file system events in real-time. When a new file is detected in a watched directory, it is queued for processing without blocking the operating system's IO operations.

### 2. Semantic Inference Pipeline
For every file detected, the system extracts text context and generates a vector embedding using the `all-MiniLM-L6-v2` transformer. This process is handled locally on the CPU, ensuring data privacy and offline functionality.

### 3. Vector Routing & Classification
The system employs **FAISS (Facebook AI Similarity Search)** for vector retrieval.
- **Similarity Scoring**: Incoming file embeddings are compared against a local index of pre-defined category centroids.
- **Confidence Thresholding**: A rank-weighted classification algorithm determines the match. Files falling below a specified confidence threshold are rejected back to the source directory.

### 4. Background Orchestration
The background daemon is managed via native OS startup hooks, allowing for persistence across reboots without requiring elevated administrator privileges.
- **Windows**: Native VBScript in the user's Startup folder.
- **macOS/Linux**: `launchd` and `systemd` user-space services.

---

## Management Interface

The system features a dual-interface layer for configuration and training:
- **Management UI**: A standalone window (via `pywebview`) communicating with a FastAPI local bridge for path management and history review.
- **CLI**: A terminal-based interface for headless environments or manual interaction.

### Feedback Loop
Manual corrections through the management interface update the underlying FAISS index, allowing the system to refine its classification over time based on user feedback.

---

## Research & Verification
The `evaluation/` directory contains benchmarks used to measure classification accuracy. Results are available in [EVALUATIONS.md](EVALUATIONS.md).

Future technical objectives are documented in [futureworks.md](futureworks.md).

---

## License
MIT License
