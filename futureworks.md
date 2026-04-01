# SortedPC: Research & Future Roadmap

The current implementation provides a stable, offline-first semantic sorting engine for text files with a professional, minimalist desktop interface. The ultimate vision is to build a system that seamlessly mimics the user's own mental model of file and knowledge organization.

## Current Core (v1.0 - Hybrid Desktop)

- **Presentation Layer**: Decoupled FastAPI bridge with a native OS-desktop window (`pywebview`).
- **Functional Parity**: Full feature sets for managing watch paths, destinations, and training history across CLI and UI.
- **System Service**: Robust Windows Task Scheduler integration for background persistence and native Windows toast notifications.
- **Optimization**: Fast startup with local model verification, bypassing server-side checks.

## Phase 1: OS Independence & Cross-Platform Support
*Goal: Decouple the Windows-specific background logic to enable seamless use across macOS and Linux.*

- **Service Management**: Migrating from Windows-specific `schtasks.exe` and `.bat` launchers to a unified, cross-platform service manager (e.g., `systemd` for Linux, `launchd` for macOS, and a robust Windows Service wrapper).
- **Notification Abstraction**: Standardizing the notification pipeline to move away from Windows-only toaster libraries to a generic, reliable cross-platform interface.
- **Path Portability**: Hardening path resolution logic to ensure the system handles different filesystem signatures and permissions across Unix-based and Windows-based environments.

## Phase 2: Multi-Modal Perception
*Goal: Expand the system's comprehension beyond bare text documents to mimic how users visually process images and media.*

- **Visual Embeddings**: Measuring the performance impact and feasibility of cross-modal models (like quantized CLIP). The objective is to embed images into the identical FAISS vector space used for text.
- **OCR Fallback**: Testing the efficiency of local OCR tools (EasyOCR/Tesseract) as a computationally cheaper alternative for receipts, scans, and documents.
- **Media Queuing**: Architecting asynchronous media processing workflows for heavier assets (e.g., audio/video) to prevent real-time sorting loops from blocking.

## Phase 3: Relational Context & Metadata
*Goal: Combine semantic meaning ("What is this?") with deterministic, relational context ("Who, When, Where?").*

- **Contextual Data Modeling**: Defining data structures to map relationships between files, specific projects, and timelines.
- **Hybrid Search Paradigm**: Determining the optimal storage for hard relational data. The architectural choice between an embedded relational database (SQLite/DuckDB) or a lightweight local graph will be made based on system load testing.
- **Weighted Scoring**: Formulating algorithms to mathematically combine a FAISS semantic guess with strict metadata constraints (like EXIF GPS or creation dates).

## Phase 4: Conversational Retrieval
*Goal: Evolve the sorter into an interactive, completely private knowledge assistant.*

- **Local RAG Modeling**: Drafting architectural models for a Retrieval-Augmented Generation system that operates entirely offline, using the FAISS index as the core knowledge base.
- **Constrained LLMs**: Assessing the integration of heavily quantized local models (e.g., `llama.cpp`). The engineering focus is strictly on using LLMs to translate user commands ("Find my medical documents") into exact SQL/Vector queries, rather than building a standard conversational chatbot.

---
*Note: This roadmap reflects long-term strategic objectives. The specific technical stack and execution methods discussed here are pending final prototyping, system evaluation, and architectural decision.*
