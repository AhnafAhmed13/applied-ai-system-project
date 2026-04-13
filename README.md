# Applied AI System

**Original Project: [DocuBot](https://github.com/AhnafAhmed13/ai110-module4tinker-docubot-starter)**

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

---

# TF Summary

The core concept students needed to understand is how a retrieval-augmented generation (RAG) pipeline differs from simply passing all documents to an LLM, specifically, how an inverted index narrows candidate documents before scoring and snippet extraction reduce noise for the model.

Students are most likely to struggle with the scoring and retrieval step, particularly the conceptual leap from "does this document contain any query word?" to "how relevant is this document overall?" Students also might run into issues setting up the Gemini API key, either hardcoding it directly in source files instead of using a `.env` file, or not understanding why exposing it in code is a security risk.

AI tools were genuinely helpful for generating boilerplate like tokenization loops and the inverted index structure. Overall, AI was more helpful than misleading in this project. It assisted with debugging tokenization logic, explaining how inverted indexes work conceptually, and comparing test queries to verify retrieval behavior.

To guide a student without giving the answer, ask them:
- How do you compute the inverted index? What maps to what, and why?
- How do you decide which words are relevant or important enough to use for matching?
- What should you actually include in your matched snippets? The whole document, the matching paragraph, or something in between?
