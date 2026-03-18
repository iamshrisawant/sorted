# Sorted (SortedPC): Mirroring Human Logic via Local-First Semantic Organization

![Pipeline Diagram](assets/pipeline.png)

## Abstract
**Sorted** is a project designed to mirror human file organization logic using a **local-first, semantic approach**. Unlike traditional automation tools that rely on rigid regex or keyword matching, Sorted uses a **Bi-Encoder Neural Network (all-MiniLM-L6-v2)** to understand the *context* and *meaning* of your files.

It observes how you organize your files and learns to replicate that logic automatically. It features **FAISS (Facebook AI Similarity Search)** for efficient vector indexing, **Rank-Weighted k-NN classification**, **Depth Bias**, and a **Confidence Threshold** system to ensure high-precision sorting. In its new iteration, it also includes interactive CLI management, background watcher integration via Windows Scheduled Tasks, and a feedback loop for continuous reinforcement learning.

## Key Features

*   **🔒 Local-First & Privacy-Focused**: All processing happens on your device. No data is sent to the cloud.
*   **🧠 Semantic Understanding**: Understands file content (not just filenames) using state-of-the-art sentence transformers.
*   **� FAISS Vector Search**: Uses FAISS CPU for ultra-fast, scalable vector indexing and retrieval.
*   **🔁 Interactive Reinforcement Learning**: Includes a "View & Correct Moves" CLI menu. The system continuously adapts and refines its weights based on your corrections.
*   **🛡️ Open-Set Recognition**: Files with low confidence scores are explicitly **rejected** and left in the Inbox, preventing misclassification.
*   **📂 Hierarchical Awareness**: Implements a "Depth Bias" to prefer specific sub-folders over generic root folders when semantic similarity is close.
*   **⚡ Background Watcher & Windows Integration**: Runs seamlessly in the background using `pythonw.exe`. Includes automatic registration via Windows Scheduled Tasks so it monitors your folders from system startup, with desktop notifications to keep you informed.

## Architecture Pipeline

1.  **Inbox Monitoring**: The background watcher observes your configured inbox directory.
2.  **Extraction**: Text is extracted flexibly from documents (PDF, DOCX, TXT) and smartly truncated to maintain efficiency.
3.  **Encoding**: The models encode document context into a high-dimensional vector.
4.  **Retrieval**: FAISS queries the existing knowledge base for the semantically nearest neighbors.
5.  **Classification**: 
    *   **Rank-Weighted k-NN**: Neighbors are weighted by their rank (closer neighbors vote more).
    *   **Depth Bias**: Deeper folder paths get a slight score boost to encourage specific sorting.
6.  **Decision**:
    *   If `Score > Confidence Threshold`: **Move** to target folder.
    *   If `Score < Confidence Threshold`: **Reject** (leave in Inbox).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/sorted.git
    cd sorted
    ```

2.  **Install Dependencies**:
    Recommendation: Use a virtual environment.
    ```bash
    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt
    ```

3.  **Launch SortedPC**:
    ```bash
    python src/main.py
    ```

## Usage

SortedPC provides an interactive CLI (`src/main.py`) that governs the entire application lifecycle. 

### 1. Initialize the Knowledge Base 
When you start the app, you will be prompted to add **Organized Paths** (folders containing manually sorted files). The system uses these to build its initial FAISS vector index.

### 2. Manage the Watcher
Through the main menu, add your "Inbox" folder where new, unsorted files arrive. You can then:
*   Start or Stop the Background Watcher.
*   Register the Watcher to run on Windows Startup via scheduled tasks.

### 3. Correct & Reinforce
SortedPC allows you to view a history of automated file moves. If a file was sorted incorrectly:
*   Use the **View & Correct Moves** menu to correct the path.
*   Run the **Learn from Corrections** action so the system tweaks its ranking weights and learns your true preference.

### 4. Benchmarking & Calibration (For Researchers)
The original research scripts are preserved in the root directory:
*   `python benchmark.py`: Evaluates performance against synthetic and academic datasets (20 Newsgroups).
*   `python calibration.py`: Calculates the optimal F1 confidence threshold.

## Project Structure

```
Sorted/
├── src/
│   ├── main.py               # Interactive CLI and Application Entrypoint
│   ├── core/
│   │   ├── pipelines/        # Builder, Initializer, Sorter, Reinforcer, Watcher
│   │   └── utils/            # Indexing, Logging, Notifications, Path Mgmt
├── assets/                   # Project visual assets
├── benchmark.py              # Academic Benchmarking Suite
├── calibration.py            # Threshold Calibration Tool
├── requirements.txt          # Updated System Dependencies
└── config.py                 # Global Configuration fallback
```

## License
MIT License
