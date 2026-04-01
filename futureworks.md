# SortedPC: Future Work

The current implementation establishes a stable, offline-first semantic sorting engine for text-based files. To evolve this project into a comprehensive, multi-modal knowledge product, development must proceed incrementally. New additions will act as decoupled layers, latching onto the existing core (`sorter.py`, `builder.py`, `watcher.py`) without requiring foundational rewrites.

Here is a practical, grounded roadmap for sequenced development.

## Phase 1: Presentation & OS Abstraction Layer
*Decoupling background logic to enable visual interaction and cross-platform use.*

*   **Unified OS Daemon:** Transition away from standalone Windows `.bat` files and `schtasks.exe`. Implement cross-platform service management generating `systemd` (Linux), `launchd` (macOS), or native Windows Services for robust startup and lifecycle management.
*   **Local API / State Manager:** Introduce a lightweight local interface (e.g., an underlying FastAPI service or direct IPC). This layer will safely read configuration, index states, and `logs.jsonl` without directly interfering with the active file watchdog.
*   **The UI Dashboard:** Instead of generating entirely new application logic for the frontend, build a UI (Tauri, Electron, or PySide6) that acts as a client to the Local API. This provides a visual "Inbox" showing recently sorted items, allowing users to verify semantic choices, "Undo" mistakes (which actively feeds corrections back to the index), and manage folders without needing the CLI.

## Phase 2: Multi-Modal Support (Images & Multimedia)
*Expanding comprehension beyond text using established cross-modal embeddings.*

*   **Visual Vectorization:** Rather than overhauling the FAISS index, introduce a lightweight, cross-modal model (like a quantized `CLIP` using `sentence-transformers`). When the processor encounters an image, it skips text extraction, embeds the image directly, and passes the vector to the identical FAISS cluster used for text.
*   **Hybrid OCR Pipelines:** For distinct document images (receipts, scanned invoices), integrate local OCR (e.g., EasyOCR/Tesseract). Text parsing requires significantly less computational power than inference on a vision model, acting as a practical, lightweight fallback.
*   **Media Processing Queues:** Videos and large multimedia require heavy extraction (like Whisper for audio, or frame-sampling for video). Introduce an asynchronous, low-priority processing queue to ensure heavy inference doesn't block the real-time watchdog sorting of standard files.

## Phase 3: Relational Context & Deterministic Metadata
*Combining semantic meaning ("What") with factual context ("Who, When, Where").*

*   **Metadata Extraction Engine:** Before embedding semantics, extract standard metadata: EXIF GPS coordinates, ID3 tags, and standard OS creation/modification timestamps.
*   **Relational Mapping (SQLite):** Instead of forcing exact parameters into a vector space, store file relationships in a fast local relational format (SQLite).
*   **Hybrid Scoring:** When sorting files, system logic utilizes both scores. If a file is semantically categorized as "Party," but its metadata strictly links its time and location properties to the "Wedding 2024" folder, the deterministic context acts as an override or multiplier to the raw FAISS guess.

## Phase 4: Conversational Retrieval (Local RAG)
*Upgrading the file sorter into an interactive private knowledge assistant.*

*   **Semantic Search:** Expand the UI to include a localized search function that queries the FAISS index directly, allowing users to find files based on natural language concepts.
*   **Constrained Local LLM:** Introduce a heavily quantized local LLM (e.g., via `llama.cpp`) focusing purely on intent routing and query formulation, rather than acting as a loose chatbot.
*   **Conversational Operations:** When a user types *"Find my medical documents from last August"*, the local LLM parses the command to execute a hybrid retrieval: querying the SQLite database for `Time = August` and FAISS for `Context = Medical`. It returns the exact file references to the UI. Since everything remains fully offline, PII reasoning and retrieval remains completely secure.
