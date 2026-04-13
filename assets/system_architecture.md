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