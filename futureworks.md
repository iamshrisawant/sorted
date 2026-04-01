# SortedPC: Future Works

The current implementation provides a stable, offline-first semantic sorting engine for text files. The ultimate vision for this product is to build a system that seamlessly mimics the user's own mental model of file and knowledge organization. 

To achieve this, the project must evolve incrementally. However, the exact technical implementations for future phases are still pending technical evaluation and architectural decision.

The following serves as a strategic roadmap for incoming capabilities, rather than a definitive task list. New additions will be prototyped and benchmarked heavily to ensure they safely latch onto the existing core (`sorter.py`, `builder.py`, `watcher.py`) without disrupting its stability.

## Phase 1: Presentation & OS Independence
*Goal: Decouple the background logic to enable visual interaction and cross-platform use.*

*   **OS Service Management:** Evaluating robust alternatives to standalone Windows `.bat` files and `schtasks.exe`. The objective is to implement the most effective, lightweight mechanism to safely manage persistent background tasks across OS environments (e.g., Windows Services, `systemd`, `launchd`).
*   **API / State Abstraction:** Designing the structure for a local bridge (e.g., FastAPI, local IPC) capable of reading configuration and index states to serve a front-end without blocking the core Python watchdog loop.
*   **User Interface Options:** Benchmarking cross-platform desktop frameworks (Tauri, Electron, PySide6) to build a visual "Inbox." The goal is a UI that lets users correct the AI's sorting (to train it) without touching a terminal, with the final architectural binding and stack to be decided based on performance tests.

## Phase 2: Multi-Modal Percerption
*Goal: Expand the system's comprehension beyond bare text documents to mimic how users visually process images and media.*

*   **Visual Embeddings:** Measuring the local performance impact and feasibility of cross-modal models (like quantized CLIP). The objective is to embed images into the identical FAISS vector space used for text, pending rigorous benchmark testing.
*   **Fallback Pipelines & OCR:** For basic document constraints (receipts, scans), testing the efficiency of running local OCR tools (EasyOCR/Tesseract) as a computationally cheaper alternative to full vision models.
*   **Media Queuing Mechanisms:** Architecting asynchronous workflows. To handle processing for heavy audio (Whisper) or video, we need to establish queuing mechanisms that prevent system drain and ensure real-time sorting remains unblocked.

## Phase 3: Relational Context & Metadata
*Goal: Combine semantic meaning ("What is this?") with deterministic, relational context ("Who, When, Where?").*

*   **Contextual Data Modeling:** Defining data models to map relationships between files, specific projects, and timelines to mimic how a user naturally groups connected events.
*   **Hybrid Data Structures:** Determining the optimal paradigm for storing this hard data. The architectural choice between an embedded relational database (SQLite/DuckDB) or a lightweight local graph will be made based on system load testing.
*   **Weighted Scoring Systems:** Formulating algorithms to mathematically combine a FAISS semantic guess with strict metadata constraints (like EXIF GPS or creation dates) to prevent the AI from making logically impossible sorting decisions.

## Phase 4: Conversational Retrieval
*Goal: Evolve the sorter into an interactive, completely private knowledge assistant.*

*   **Local RAG Modeling:** Drafting architectural models for a Retrieval-Augmented Generation system that operates entirely offline, using the FAISS index as the core knowledge base.
*   **Constrained Local LLMs:** Assessing the integration of heavily quantized local models (e.g., `llama.cpp`). The engineering focus will be tightly constrained on whether a small LLM can reliably translate a user command (*"Find my medical documents from August"*) into an exact SQL/Vector query, avoiding the bloat of a standard conversational chatbot.

---
*Note: This roadmap reflects long-term strategic objectives. The specific technical stack and execution methods discussed here are pending final prototyping, system evaluation, and architectural decision.*
