# SortedPC: Technical Roadmap

The current implementation provides an offline-first semantic sorting engine for text files managed via a decoupled GUI/CLI architecture. The objective is to refine the system's ability to mirror diverse organizational contexts.

- **Presentation Layer**: Decoupled FastAPI bridge with a native OS-desktop window (`pywebview`).
- **Functional Parity**: Unified feature sets for path management and training across both interface layers.
- **Service Orchestration**: Zero-friction background hooks (VBScript, systemd, launchd) for persistent execution without requirement for administrative privileges.

---

## Technical Objectives

### Local OCR & Non-Text Extraction
*Goal: Expand the system's ability to process non-plaintext assets by incorporating local extraction layers.*
- **Library Analysis**: Evaluating the performance impact of lightweight OCR engines (e.g., EasyOCR or Tesseract) for metadata extraction from scans and images.
- **Asynchronous Queuing**: Designing a media processing queue to prevent long-running extraction tasks from blocking the real-time event loop.

### Relational Metadata & Context Persistence
*Goal: Supplement semantic similarity with deterministic metadata for more rigid organizational rules.*
- **Relational Storage**: Implementing a local relational database (SQLite/DuckDB) to handle complex history tracking and directory relationship mapping.
- **Hybrid Scoring**: Formulating retrieval logic that weights FAISS semantic scores against file metadata (e.g., creation dates, file extensions, or project tags).

### Contextual Knowledge Retrieval
*Goal: Move from passive sorting to active information retrieval within the local index.*
- **Local RAG Integration**: Prototyping a retrieval-augmented generation layer that utilizes the existing FAISS index as a knowledge base for specific query handling.
- **Quantized Inferencing**: Researching the integration of highly quantized local language models for query translation into vector search operations.

---
*Note: This roadmap reflects development objectives. Implementation choices are subject to local performance benchmarking and architectural evaluation.*
