# DocuBot Model Card

This model card is a short reflection on your DocuBot system. Fill it out after you have implemented retrieval and experimented with all three modes:

1. Naive LLM over full docs  
2. Retrieval only  
3. RAG (retrieval plus LLM)

Use clear, honest descriptions. It is fine if your system is imperfect.

---

## 1. System Overview

**What is DocuBot trying to do?**  
Describe the overall goal in 2 to 3 sentences.

> DocuBot is a question-answering system for project documentation. It loads `.md` and `.txt` files from a `docs/` folder, builds a retrieval index, and answers developer questions either by returning raw snippets or by passing those snippets to a Gemini LLM for a synthesized answer.

**What inputs does DocuBot take?**  
For example: user question, docs in folder, environment variables.

> A natural language question from the user, `.md`/`.txt` files from the `docs/` folder, and optionally a `GEMINI_API_KEY` environment variable to enable LLM-powered modes.

**What outputs does DocuBot produce?**

> Depending on the mode: raw document snippets with filenames (retrieval only), a synthesized natural language answer grounded in those snippets (RAG), or an unconstrained LLM answer (naive LLM).

---

## 2. Retrieval Design

**How does your retrieval system work?**  
Describe your choices for indexing and scoring.

- How do you turn documents into an index?
- How do you score relevance for a query?
- How do you choose top snippets?

> **Indexing:** Each document is tokenized (lowercased, punctuation stripped, stop words removed, simple depluralization applied) and stored in an inverted index mapping words to the filenames that contain them.
>
> **Scoring:** For a given query, candidate documents are identified via the index, then scored by counting how many unique query tokens appear in the document text. A `min_score` threshold (default 1) filters out near-misses.
>
> **Snippet selection:** The top-k scored documents are returned. For each, `_extract_snippet` splits the document into paragraphs and collects only those containing query words. If a matching paragraph is a heading, the following paragraph is included too. Up to 3 such blocks are joined and returned.

**What tradeoffs did you make?**  
For example: speed vs precision, simplicity vs accuracy.

> Speed and simplicity over precision. The inverted index and word-count scoring are very fast but have no notion of term frequency, document length, or semantic meaning. Depluralization catches basic morphology but misses synonyms entirely. The snippet extractor can miss answers that are phrased differently from the query.

---

## 3. Use of the LLM (Gemini)

**When does DocuBot call the LLM and when does it not?**  
Briefly describe how each mode behaves.

- Naive LLM mode: Calls Gemini with just the question — the full docs text is passed in but the current prompt actually **ignores it**, so the model answers purely from its training data.
- Retrieval only mode: No LLM call at all. The system returns raw matched snippets directly to the user.
- RAG mode: Runs retrieval first, then passes only the top-k snippets to Gemini with a grounding prompt.

**What instructions do you give the LLM to keep it grounded?**  
Summarize the rules from your prompt. For example: only use snippets, say "I do not know" when needed, cite files.

> The RAG prompt instructs Gemini to: (1) answer using only the provided snippets, (2) never invent functions, endpoints, or config values not present in the snippets, (3) reply with exactly "I do not know based on the docs I have." if the snippets are insufficient, and (4) mention which files were used in the answer.

---

## 4. Experiments and Comparisons

Run the **same set of queries** in all three modes. Fill in the table with short notes.

You can reuse or adapt the queries from `dataset.py`.

| Query | Naive LLM: helpful or harmful? | Retrieval only: helpful or harmful? | RAG: helpful or harmful? | Notes |
|------|---------------------------------|--------------------------------------|---------------------------|-------|
| Where is the auth token generated? | Harmful — gave a generic textbook explanation of JWTs and OAuth, completely ignoring the docs | Helpful — surfaced the exact line from AUTH.md naming `generate_access_token` in `auth_utils.py` | Helpful — one-sentence answer citing AUTH.md | Best case for RAG |
| How do I connect to the database? | Harmful — generic database connection tutorial unrelated to this project | Helpful — returned relevant SETUP.md snippet about `DATABASE_URL` and SQLite fallback | Helpful — synthesized a clear two-case answer (SQLite vs PostgreSQL) from SETUP.md and DATABASE.md | RAG added clarity over raw snippets |
| Which endpoint lists all users? | Harmful — admitted it didn't know which API and gave generic REST patterns | Partially helpful — retrieved API_REFERENCE.md but the snippet extractor returned the auth header section, not the users endpoint | Harmful — said "I do not know" even though the answer (`GET /api/users`) exists in the docs | Snippet extraction failure: query words matched a different paragraph than the actual answer |
| How does a client refresh an access token? | Harmful — gave a generic OAuth refresh token flow unrelated to this codebase | Partially helpful — returned AUTH.md token generation section but not the specific `/api/refresh` client workflow | Harmful — said "I do not know" despite the answer being present in AUTH.md | Same root cause: snippet extractor picked the wrong paragraph |

**What patterns did you notice?**  

- When does naive LLM look impressive but untrustworthy?  
- When is retrieval only clearly better?  
- When is RAG clearly better than both?

> **Naive LLM looks impressive but is untrustworthy** when the question sounds generic (e.g., "how do I connect to a database?"). The answer is fluent, detailed, and plausible — but it describes general conventions, not this specific project.
>
> **Retrieval only is clearly better** when the user needs to see the source of truth with a citation. It's also more reliable than RAG when snippet extraction works, because it cannot fabricate an answer.
>
> **RAG is clearly better than both** when retrieval finds the right paragraph and the LLM just needs to synthesize it into a direct sentence. "Where is the auth token generated?" is a clean example: RAG collapsed three snippets into one precise answer with a source citation.

---

## 5. Failure Cases and Guardrails

**Describe at least two concrete failure cases you observed.**  
For each one, say:

- What was the question?  
- What did the system do?  
- What should have happened instead?

> **Failure case 1 — Snippet extractor picks the wrong paragraph**
> - Question: “Which endpoint lists all users?”
> - What happened: Retrieval correctly fetched API_REFERENCE.md, but `_extract_snippet` returned the authentication header section because the word “token” matched query words. The `GET /api/users` line was never surfaced. RAG then said “I do not know.”
> - What should have happened: The snippet should have included the users endpoint section from API_REFERENCE.md.

> **Failure case 2 — Naive LLM ignores the docs entirely**
> - Question: “Where is the auth token generated?”
> - What happened: The naive LLM mode is passed `all_text` but the prompt in `llm_client.py` doesn't include it — the model answered from general knowledge, describing JWTs, OAuth, and refresh tokens with no reference to `generate_access_token` or `auth_utils.py`.
> - What should have happened: The prompt should inject `all_text` as context, or this mode should be clearly labeled as “no docs used.”

**When should DocuBot say “I do not know based on the docs I have”?**  
Give at least two specific situations.

> 1. When the query asks about a topic that does not appear in any loaded document (e.g., “Is there any mention of payment processing?” — there is none in these docs).
> 2. When retrieval finds candidate documents but the retrieved snippets do not actually contain an answer to the specific question asked.

**What guardrails did you implement?**  
Examples: refusal rules, thresholds, limits on snippets, safe defaults.

> - `min_score=1` threshold in `retrieve()` — documents that match zero query tokens are excluded.
> - The RAG prompt instructs Gemini to refuse with a fixed phrase rather than guess.
> - `answer_retrieval_only` and `answer_rag` both return “I do not know based on these docs.” if `retrieve()` returns an empty list.
> - Snippet extraction caps output at 3 paragraphs and falls back to the first 500 characters if no matching paragraph is found.

---

## 6. Limitations and Future Improvements

**Current limitations**  
List at least three limitations of your DocuBot system.

1. Keyword-only retrieval — no semantic understanding. A query using synonyms or different phrasing from the docs will score zero even if the answer is present.
2. Snippet extraction is paragraph-boundary dependent — if the answer spans sections or sits in a paragraph whose other words don't match query tokens, it gets silently dropped.
3. The naive LLM mode does not actually inject the docs into its prompt, making it purely a general-knowledge query with no grounding at all.

**Future improvements**  
List two or three changes that would most improve reliability or usefulness.

1. Replace word-count scoring with TF-IDF or a small embedding model so semantically similar queries find the right documents even without exact word matches.
2. Fix the naive LLM prompt to actually include `all_text` as context, or replace paragraph-level snippet extraction with sentence-level chunking to reduce the risk of the answer falling in the wrong paragraph.
3. Add a confidence signal to retrieval-only mode (e.g., show the score alongside each snippet) so users can judge how much to trust an answer.

---

## 7. Responsible Use

**Where could this system cause real world harm if used carelessly?**  
Think about wrong answers, missing information, or over trusting the LLM.

> If used for security-sensitive docs (e.g., how to configure auth, which endpoints are protected), a hallucinated or misretrieved answer could lead a developer to misconfigure access controls. In naive LLM mode the model answers with general knowledge that sounds authoritative but describes a different system entirely — a developer who trusts that answer could introduce a real vulnerability.

**What instructions would you give real developers who want to use DocuBot safely?**  
Write 2 to 4 short bullet points.

- Always verify answers against the actual source file before acting on them, especially for security or infrastructure configuration.
- Never use naive LLM mode for production queries — the prompt does not include the docs, so answers reflect general training data, not your project.
- Treat "I do not know based on the docs I have." as authoritative: it means the docs don't cover this, not that the answer doesn't exist.
- Keep the `docs/` folder up to date; stale documentation will produce confidently wrong answers with no warning.

---
