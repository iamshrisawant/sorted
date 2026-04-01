# Sorted (SortedPC): Mirroring Human Logic via Local-First Semantic Organization

![Pipeline Diagram](assets/pipeline.png)

**Sorted** is an intelligent, completely offline background watcher that semantically organizes your files exactly how you would, using State-of-the-Art Machine Learning. It now features a professional, minimalist desktop interface alongside its robust legacy CLI.

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

### 3. Launching the System
SortedPC dynamically chooses between a native Desktop UI or a terminal CLI based on your parameters.

*   **Default (Desktop UI):** `python src/main.py`
    *   Launches a standalone, minimalist window (via `pywebview`) powered by a local FastAPI bridge.
*   **Legacy (Terminal CLI):** `python src/main.py --cli`
    *   Boots the original interactive matrix-style CLI for terminal power users.

> **Note on Optimized Startup**: During the first boot, the system downloads the 80MB HuggingFace Bi-Encoder model into `src/core/models/`. On subsequent launches, the system bypasses network checks and performs an instant local verification for a 100% offline and high-performance experience.

---

## 💻 Features & Usage

### 1. Unified Management
Whether using the Desktop UI or the CLI, you can seamlessly manage your system:
*   **Knowledge Base**: Add destination folders and define "context rules" (e.g., "financial statements") to help the AI understand your organizational logic.
*   **Background Watcher**: Register the daemon to monitor folder events (like your `Downloads` folder).
*   **OS Integration**: Seamlessly register the system as a Windows Startup task for persistent background sorting.

### 2. Minimalist Aesthetic
The Desktop UI is designed with a warm, distraction-free monochrome aesthetic (inspired by Claude and Notion). 
*   **Multi-Theme Support**: Toggle between **Light**, **Dark**, or **System** themes in the Settings panel.
*   **Functional Colors**: Uses standardized indicators (Green/Red/Blue) for system status and active sorting tasks.

### 3. Review & Training Loop
If the AI ever misclassifies a file, use the **History & Training** panel (or CLI menu) to fix the mistake. When you specify a correct folder, the **Semantic Auto-Discovery** loop instantly indexes the new context so the AI never makes the same mistake again.

---

## 🧠 The Science Behind It

Unlike traditional automation tools that rely on rigid regex or keyword matching, Sorted uses a **Bi-Encoder Neural Network (all-MiniLM-L6-v2)** to understand the *true context* and *meaning* of your files.

It pairs this with **FAISS (Facebook AI Similarity Search)** for ultra-fast, scalable vector retrieval, and a **Rank-Weighted k-NN classification** algorithm integrated with a **Confidence Threshold**. This ensures high-precision sorting, meaning files with low semantic confidence are explicitly **rejected** back to your Inbox rather than misclassified.

## ✨ Technical Highlights

*   **🔒 Local-First & Privacy-Focused**: Processing happens entirely on your CPU. No data ever leaves your machine.
*   **⚡ Optimized FAISS Indexing**: Scalable retrieval even across massive folder hierarchies.
*   **🖥️ Hybrid Architecture**: Built with a FastAPI backend and a `pywebview` frontend, keeping the core ML logic decoupled from the presentation layer.
*   **🔁 Organic Feedback Loop**: Learns from manual corrections to dynamically expand its semantic sightline.

---

## 🔬 Research & Future
*   **Calibrations:** The `evaluation/` directory contains research testing suites used to benchmark the system against academic datasets. See [EVALUATIONS.md](EVALUATIONS.md).
*   **Roadmap:** See [futureworks.md](futureworks.md) for long-term objectives like Multi-Modal perception and Local RAG modeling.

## License
MIT License
