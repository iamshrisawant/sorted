# Sorted (SortedPC)

![Pipeline Diagram](assets/pipeline.png)

**Sorted** is a local-first, file organization engine that transforms your cluttered directories into a semantically organized digital library. It monitors your inbox, extracts deep context (including OCR from images), and routes files into your Knowledge Hubs using local vector embeddings.

---

## 💎 Core Experience

### 1. Hands-Free Organization (The Wait Queue)
New to Sorted? Just point it at your cluttered folders. The system automatically stages your files in a **Wait Queue** while you establish your Knowledge Hubs. As soon as you define a destination, the AI automatically re-processes and routes your pending files—no manual re-submission required.

### 2. Semantic Dashboard
A minimalist, warm-monochrome interface (built with `pywebview` and FastAPI) provides a real-time overview of your local digital memory. Monitor the **Watcher**, triage files in the **Review Queue**, and prune your sorting **History** with ease.

### 3. Manual Deep Scan
Need to organize a massive existing archive? Use the **Manual Deep Scan** to recursively analyze entire directory trees. The AI will classify every supported file type, leaving your file system perfectly structured.

### 4. Local-First Visual Intelligence
Sorted features integrated **OCR and visual extraction**. It reads text from screenshots, scanned PDFs, and photos entirely on your CPU. Your data never leaves your machine.

---

## 🛠 Technical Architecture

### 1. Event-Driven Monitoring
The system utilizes `watchdog` to intercept file system events in real-time. Incoming files are queued for processing without blocking system IO.

### 2. Transformer-Based Inference
Every file is processed using the `all-MiniLM-L6-v2` transformer. The system auto-provisions these models on first run, ensuring a "plug-and-play" experience.

### 3. Vector Routing (FAISS)
Sorted uses **FAISS** (Facebook AI Similarity Search) to compare file embeddings against your Knowledge Hubs. 
- **Wait Queue**: Files staged during untrained states are auto-sorted upon hub creation.
- **Review Queue**: Files with low semantic confidence are held for manual verification, improving the AI's future accuracy.

---

## 🚀 Getting Started

1. **Clone & Virtual Env**   ```bash
   git clone <repo-url>
   python -m venv venv
   source venv/bin/activate  # Or .\venv\Scripts\activate on Windows
   ```
2. **Install**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Run**:
   ```bash
   python src/main.py
   ```
   *Models and base directories will be automatically provisioned on launch.*

---

## 🔬 Research & Vision
Detailed benchmarks using the SROIE dataset are available in [evaluation/](evaluation/).
For the long-term vision of Sorted as a localized digital brain, see [futureworks.md](futureworks.md).