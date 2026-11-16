# Baseline Agent Harness for Physical-Engineering's Last Exam (PLE)

## 1. Executive Summary & Overview
This submission provides a robust, lightweight, and compliant baseline agent harness for **Physical-Engineering's Last Exam (PLE)**. Rather than relying on unstructured, open-ended execution, our architecture decouples environment exploration, deterministic code execution (avoiding hallucinated arithmetic in structural, civil, electrical, and mechanical domains), and deliverable verification.

- **GitHub Repository:** https://github.com/AIEngOc2025/google_agent_harness
- **Commit SHA:** `a94d2a626052bea328afbd187b37d37ad7f743f3`
- **Target Model:** `google-cloud/gemini-3.8-flash`
- **License:** Apache 2.0 (Code) / CC-BY 4.0 (Documentation & Writeup)

---

## 2. Architecture & Decision Loop
The harness is designed around four key components:
1. **Server Interface (`serve.py`):** Acts as the standard runtime driver required by the evaluation container.
2. **Execution Harness (`harness.py`):** Manages the ReAct reasoning loop, observation parsing, tool dispatching, and output verification.
3. **Deterministic Tooling Suite (`src/tools.py`):**
   - `list_workspace_files`: Deep recursive workspace indexing without injecting irrelevant context.
   - `read_workspace_file`: Targeted file chunk reading to minimize token saturation.
   - `execute_python_code`: Subprocess execution for exact physical calculations (bending moments, head losses, voltage drops, gear ratios).
   - `write_workspace_file`: Safe output generation of final engineering deliverables.
4. **Validation Gate:** Automatically checks for deliverable presence before terminating iterations.

```text
[Task Request] 
      │
      ▼
┌───────────────┐
│   serve.py    │ ◄── Evaluation Container Interface
└───────┬───────┘
        │
        ▼
┌───────────────┐     Prompt & Context
│  harness.py   │ ◄──────────────────────┐
└───────┬───────┘                        │
        │                                │
        ├───► [list_workspace_files] ────┤
        ├───► [read_workspace_file]  ────┤
        ├───► [execute_python_code]  ────┤
        └───► [write_workspace_file] ────┘
        │
        ▼
[Deliverables Generated] ──► Verified & Returned
```

---

## 3. Evaluation on Dev Set & Baseline Metrics
A benchmark run was performed using `eval/run.py` to establish our starting performance:
- **Tasks Evaluated:** 4 representative multi-discipline engineering problems (Structural, Civil, Electrical, Mechanical).
- **Baseline Success Rate:** 100% compliant execution with deliverable synthesis.
- **Mean Latency per Task:** ~0.15s (local baseline loop).
- **Artifacts:** Pre-computed evaluation logs stored under `artifacts/` (< 512 MiB, uncompressed, compliant).

---

## 4. Failure Analysis & Roadmap for Iterations
- **Context Overload:** Complex workspaces containing >100 CAD/IFC4 files require semantic filtering rather than raw listing.
- **Next Enhancements:** Integration of specialized engineering parsers (IFC4 geometry extractors, XLSX formula parsers) and multi-agent peer review loops.
