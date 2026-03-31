# Sorted (SortedPC): Mirroring Human Logic via Local-First Semantic Organization

![Pipeline Diagram](assets/pipeline.png)

**Sorted** is an intelligent, completely offline background watcher that semantically organizes your files exactly how you would, using State-of-the-Art Machine Learning. 

---

## 🚀 Quickstart & Setup

To get the watcher running on your local machine, follow these steps:

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/sorted.git
cd sorted
```

### 2. Prepare the Virtual Environment
It is highly recommended to isolate the dependencies using a Python virtual environment:
```powershell
# Windows
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 3. First Launch & Offline Initialization
```powershell
python src/main.py
```
> **Note on Offline-First Architecture**: During this very first boot, the Initializer will securely download the 80MB HuggingFace Bi-Encoder model directly into the project's internal `src/core/models/` folder. Once downloaded, **SortedPC is 100% portable and natively offline**, never requiring an internet connection or exposing your data again!

---

## 💻 Usage & CLI Guide

SortedPC is entirely managed through a simple, interactive CLI. 

### 1. Map your Knowledge Base
Before the AI can sort your files, it needs to see how you think. In the CLI, navigate to **Manage Sorting Destinations** and add existing folders that already contain your properly sorted documents. The system will read them and build its FAISS vector memory.

### 2. Start the Background Watcher
Navigate to **Manage Background Watcher**. Set your "Inbox" (like your `Downloads` folder). You can start the headless watcher manually, or register it seamlessly into Windows Task Scheduler so it boots silently in the background every time you log in.

### 3. Review History & Teach the AI
If the AI ever drops a file into an unexpected folder or falls back safely to the Unsorted bin, go to **Review Sorting History & Fix Mistakes**. 
Whenever you manually enter a new correct folder path to fix a mistake, the **Semantic Auto-Discovery** loop intercepts it, physically moves the file, dynamically maps the new folder into its tracking database, and instantly indexes it so it never makes the same mistake again!

---

## 🧠 Abstract & The Science Behind It

Unlike traditional automation tools that rely on rigid regex or keyword matching, Sorted uses a **Bi-Encoder Neural Network (all-MiniLM-L6-v2)** to understand the *true context* and *meaning* of your files.

It pairs this with **FAISS (Facebook AI Similarity Search)** for ultra-fast, scalable vector retrieval, and a **Rank-Weighted k-NN classification** algorithm integrated with a **Confidence Threshold**. This ensures high-precision sorting, meaning files with low semantic confidence are explicitly **rejected** back to your Inbox rather than misclassified.

## ✨ Key Features

*   **🔒 Local-First & Privacy-Focused**: All processing happens entirely on your CPU. No data is sent to the cloud.
*   **🧠 Semantic Understanding**: Maps document concepts (not just filenames) using modern sentence transformers.
*   **⚡ Ultra-Fast FAISS Memory**: Utilizes FAISS for scalable, split-second similarity search, even across massive folder hierarchies.
*   **🔁 Auto-Discovery Feedback Loop**: The system learns organically by observing the new folders you specify during manual corrections and immediately adding them to its semantic sightline.
*   **📂 Hierarchical Awareness**: Implements a "Depth Bias" to prefer specific sub-folders over generic root folders when semantic similarity is close.
*   **🖥️ Invisible Windows Integration**: Runs seamlessly in the background using `pythonw.exe`. Sends native Windows desktop notifications (via `plyer`) to alert you when background sorting completes.

## ⚙️ Architecture Pipeline

1.  **Inbox Monitoring**: The Windows background watcher monitors your designated unsorted folder via file-system events.
2.  **Extraction**: Text is flexibly extracted from documents (`.pdf`, `.docx`, `.pptx`, `.xlsx`, `.csv`, `.md`, `.txt`, `.html`) and system/code files are rigorously ignored.
3.  **Encoding**: The all-MiniLM-L6-v2 model encodes document text into a 384-dimensional mathematical vector.
4.  **Retrieval**: FAISS queries your existing destination folders for the closest semantic neighbors.
5.  **Classification**: 
    *   **Rank-Weighted k-NN**: Neighbors are weighted by their rank (closer neighbors vote more).
    *   **Depth Bias**: Deeper folder trees get a slight score boost to encourage specific organization.
6.  **Decision**:
    *   If `Score > Confidence Threshold`: **Move** seamlessly to target folder.
    *   If `Score < Confidence Threshold`: **Reject** (leave in Inbox).

## 🔬 Benchmarking & Future Roadmap

*   **Calibrations:** The `evaluation/` directory preserves the original research testing suites used to benchmark the system against academic datasets (20 Newsgroups). See [EVALUATIONS.md](EVALUATIONS.md) for complete quantitative analysis.
*   **Future Development:** See [futureworks.md](futureworks.md) for planned SOTA enhancements like Zero-Shot initialization and Hybrid Keyword Search.

## License
MIT License
