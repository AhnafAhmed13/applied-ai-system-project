# Applied AI System

> **Original Project: [DocuBot](https://github.com/AhnafAhmed13/ai110-module4tinker-docubot-starter)**

#### New Feature

**Confidence Scoring (all 3 modes)**

Each mode now displays a confidence score (0–1) alongside matched words and a visual progress bar, but the scoring method differs per mode because each mode has a different source of uncertainty:

- **Mode 1 (Naive LLM):** Compares the LLM's response tokens against the retrieved snippet tokens. Measures how grounded the free-form answer is in the actual docs — a low score suggests hallucination.
- **Mode 2 (Retrieval only):** Compares the query tokens against the matched document tokens. Measures how well the docs cover the query — a low score means the corpus may lack relevant content.
- **Mode 3 (RAG):** Compares the query tokens against the LLM's response tokens. Measures whether the LLM actually addressed the question — a low score often means the model returned an "I do not know" refusal.

---

# DocuBot

DocuBot is a small documentation assistant that helps answer developer questions about a codebase.  
It can operate in three different modes:

1. **Naive LLM mode**  
   Sends the entire documentation corpus to a Gemini model and asks it to answer the question.

2. **Retrieval only mode**  
   Uses a simple indexing and scoring system to retrieve relevant snippets without calling an LLM.

3. **RAG mode (Retrieval Augmented Generation)**  
   Retrieves relevant snippets, then asks Gemini to answer using only those snippets.

The docs folder contains realistic developer documents (API reference, authentication notes, database notes), but these files are **just text**. They support retrieval experiments and do not require students to set up any backend systems.

---

# System Architecture

```
╔═════════════════════════════════════════════════════════════════════════════════════════╗
║                              DOCUBOT — 3 MODES OVERVIEW                                 ║
╚═════════════════════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│  SHARED INFRASTRUCTURE                                                                  │
│                                                                                         │
│   docs/ folder                                                                          │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐                                              │
│   │  AUTH.md │  │  API.md  │  │  DB.md   │  ...                                         │
│   └────┬─────┘  └────┬─────┘  └────┬─────┘                                              │
│        └─────────────┴─────────────┘                                                    │
│                       │  load_documents()                                               │
│                       ▼                                                                 │
│              build_index()  →  { "token": ["AUTH.md", ...], ... }                       │
└─────────────────────────────────────────────────────────────────────────────────────────┘
                                        │
              ┌─────────────────────────┼──────────────────────────┐
              │                         │                          │
              ▼                         ▼                          ▼
╔═════════════════════╗   ╔══════════════════════╗   ╔══════════════════════════╗
║   MODE 1            ║   ║   MODE 2             ║   ║   MODE 3                 ║
║   Naive LLM         ║   ║   Retrieval Only     ║   ║   RAG                    ║
╚═════════════════════╝   ╚══════════════════════╝   ╚══════════════════════════╝

  query                      query                       query
    │                          │                           │
    │                          ▼                           ▼
    │                    _tokenize()                 _tokenize()
    │                          │                           │
    │                          ▼                           ▼
    │                   index lookup                index lookup
    │                   (candidate docs)            (candidate docs)
    │                          │                           │
    │                          ▼                           ▼
    │                  score_document()            score_document()
    │                  per candidate               per candidate
    │                          │                           │
    │                          │                           |
    │                          ▼                           ▼
    │                   top-K snippets               top-K snippets
    │                          │                           │
    │                  (no LLM involved)                   ▼
    │                                            answer_from_snippets()
    ▼                                                  (Gemini)
full_corpus_text()                                         │
    │                                                      ▼
    ▼                                               LLM Response
naive_answer_over_full_docs()
(Gemini, no retrieval context)
    │
    ▼
LLM Response


───────────────────────────────  CONFIDENCE SCORING  ────────────────────────────────────

  MODE 1                              MODE 2                         MODE 3
  ──────                              ──────                         ──────

  LLM Response                         query                         query
       │                                 │                             │
  _tokenize()                        _tokenize()                   _tokenize()
       │                                 │                             │
       │     ←── intersect ──→       doc tokens                        │
       │         (retrieved              │                             │
       │          snippets)          _tokenize()               LLM Response tokens
       │                                 │                             │
       ▼                                 ▼                             ▼
  matched =                         matched =                     matched =
  response_tokens                   query_tokens                  query_tokens
        ∩                                ∩                             ∩
  snippet_tokens                    doc_tokens                    response_tokens

  confidence =                      confidence =                 confidence =
  |matched|                         |matched|                    |matched|
  ─────────                         ─────────                    ─────────
  |response_tokens|                 |query_tokens|               |query_tokens|

  "What fraction of                 "What fraction of            "Did the LLM's answer
  the LLM's answer                  the query's key terms        address the query's
  is grounded in                    appear in the doc?"          key terms?"
  the docs?"


───────────────────────────  WHAT EACH SCORE TELLS YOU  ─────────────────────────────────

  MODE 1 low score  →  LLM may be hallucinating (answer not in docs)
  MODE 1 high score →  LLM's free answer aligns with retrieved docs

  MODE 2 low score  →  docs don't cover this query well
  MODE 2 high score →  strong keyword overlap between query and docs

  MODE 3 low score  →  LLM dodged or couldn't answer ("I do not know...")
  MODE 3 high score →  LLM directly addressed all parts of the query
```

---

## Setup

### 1. Install Python dependencies

    pip install -r requirements.txt

### 2. Configure environment variables

Copy the example file:

    cp .env.example .env

Then edit `.env` to include your Gemini API key:

    GEMINI_API_KEY=your_api_key_here

If you do not set a Gemini key, you can still run retrieval only mode.

---

## Running DocuBot

Start the program:

    python main.py

Choose a mode:

- **1**: Naive LLM (Gemini reads the full docs)  
- **2**: Retrieval only (no LLM)  
- **3**: RAG (retrieval + Gemini)

You can use built in sample queries or type your own.

---

## Running Retrieval Evaluation (optional)

    python evaluation.py

This prints simple retrieval hit rates for sample queries.

---

## Modifying the Project

You will primarily work in:

- `docubot.py`  
  Implement or improve the retrieval index, scoring, and snippet selection.

- `llm_client.py`  
  Adjust the prompts and behavior of LLM responses.

- `dataset.py`  
  Add or change sample queries for testing.

---

## Requirements

- Python 3.9+
- A Gemini API key for LLM features (only needed for modes 1 and 3)
- No database, no server setup, no external services besides LLM calls
