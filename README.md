# SortedPC

SortedPC is an offline utility that monitors specified directories and moves incoming files into predefined destination folders based on semantic text similarity.

## Usage Setup

To deploy SortedPC locally:
1. **Clone the repository** to your local machine.
2. **Setup a virtual environment** to isolate dependencies.
3. **Install dependencies** using the provided `requirements.txt`.
4. **Launch the application** by executing `python src/main.py`.

The system will automatically provision necessary directories and present the desktop interface for initial configuration. For a headless or terminal-exclusive experience, launch with the `--cli` argument.

## System Architecture

### Event-Driven Monitoring
The application uses the `watchdog` library to intercept real-time file system events. Newly created or modified files in designated watch paths are placed into a processing queue, executing asynchronously.

### Inference Pipeline
When a file is processed, its text content is extracted—using embedded local OCR for images and scanned PDFs—and passed through a local transformer (`all-MiniLM-L6-v2`). The model produces a vector embedding representing the semantic content of the document.

### Vector Routing and Classification
The embedding is queried against a local FAISS (Facebook AI Similarity Search) index containing embeddings of known target contexts.
- **Confidence Threshold**: A rank-weighted approach evaluates the FAISS results. If the similarity score falls below the required threshold, the file remains in an unprocessed state (Wait Queue).
- **Manual Deep Scan**: The system provides a recursive scan utility to index and route pre-existing file archives in bulk.
- **Review and Training Loop**: Misclassified files or files left in the Wait Queue can be manually managed. The system indexes these manual corrections to update the FAISS index and improve subsequent classification tasks.

## Execution and Interface

The core logic operates locally. Operations evaluate entirely on the host machine processor. Management and configuration are handled via a local desktop frontend (built with FastAPI and `pywebview`), which provides an overview of the Wait Queue, recent actions, and index state.

## Research and Evaluation
System benchmarks and evaluations on precision and latency against datasets are recorded in `EVALUATIONS.md`.