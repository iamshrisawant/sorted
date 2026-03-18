# Reproducibility Guide

This document outlines how the claims, datasets, and architecture discussed in the **Sorted** paper can be independently verified and reproduced using the code provided in this repository.

## 1. Synthetic Data Generation ("Torture Test")
To test the system against "digital clutter", we generated a synthetic dataset that mimics raw, unorganized user data (Phase A). 
The methodological code used to synthesize this noise is entirely transparent and available in [`research/benchmark.py`](research/benchmark.py). 
Specifically, the `generate_noise(text)` function:
- **Boilerplate Insertion:** Prepends tracking IDs and appends realistic corporate footers to simulate actual document formats.
- **OCR/Typo Emulation:** Loops through characters with a mathematical 5% probability to maliciously swap adjacent characters or replace them, mimicking noisy scans.

## 2. Replication of Evaluations
The performance metrics (Accuracy, Latency, and F1-Scores) presented in the paper can be reproduced with a single command. 
Running the benchmark suite will automatically download the required datasets (e.g., *20 Newsgroups*), generate the noisy "Phase A" data, and continuously log the evaluation comparisons between *LexicalSearchBaseline (TF-IDF)*, *NaiveBayesBaseline*, *SbertCentroidBaseline*, and our *SortedEngine*.

**Command to reproduce:**
```bash
python research/benchmark.py
```
*Note: Depending on your hardware, latencies may differ slightly from the paper, but relative algorithmic efficiencies and accuracy/F1 comparisons will remain strictly consistent.*

## 3. Local-First Deployment & Privacy
A core claim of *Sorted* is its ability to operate locally without compromising user privacy via cloud offloading. The code explicitly structures the system as an offline, device-bound process:
- **Zero-Cloud Embeddings:** The neural models are forcefully sandboxed using environment variables like `TRANSFORMERS_OFFLINE='1'` (visible in `src/config.py` and `research/benchmark.py`), proving that inferences happen purely on-device without external network calls.
- **Background Daemon Integration:** The system genuinely integrates into the host OS. In [`src/main.py`](src/main.py), the code creates a windowless execution layer (`pythonw.exe`), and natively hooks into Windows Task Scheduler (`schtasks.exe`), confirming its architecture as an autonomous, everyday background service.
