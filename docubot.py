"""
Core DocuBot class responsible for:
- Loading documents from the docs/ folder
- Building a simple retrieval index (Phase 1)
- Retrieving relevant snippets (Phase 1)
- Supporting retrieval only answers
- Supporting RAG answers when paired with Gemini (Phase 2)
"""

import os
import glob

class DocuBot:
    def __init__(self, docs_folder="docs", llm_client=None):
        """
        docs_folder: directory containing project documentation files
        llm_client: optional Gemini client for LLM based answers
        """
        self.docs_folder = docs_folder
        self.llm_client = llm_client

        # Load documents into memory
        self.documents = self.load_documents()  # List of (filename, text)

        # Build a retrieval index (implemented in Phase 1)
        self.index = self.build_index(self.documents)

    # -----------------------------------------------------------
    # Document Loading
    # -----------------------------------------------------------

    def load_documents(self):
        """
        Loads all .md and .txt files inside docs_folder.
        Returns a list of tuples: (filename, text)
        """
        docs = []
        pattern = os.path.join(self.docs_folder, "*.*")
        for path in glob.glob(pattern):
            if path.endswith(".md") or path.endswith(".txt"):
                with open(path, "r", encoding="utf8") as f:
                    text = f.read()
                filename = os.path.basename(path)
                docs.append((filename, text))
        return docs

    # -----------------------------------------------------------
    # Index Construction (Phase 1)
    # -----------------------------------------------------------

    STOP_WORDS = {
        "a", "an", "the", "and", "or", "but", "in", "on", "at", "to",
        "for", "of", "with", "by", "from", "is", "are", "was", "were",
        "be", "been", "being", "have", "has", "had", "do", "does", "did",
        "will", "would", "could", "should", "may", "might", "it", "its",
        "this", "that", "these", "those", "i", "you", "we", "they", "he",
        "she", "not", "no", "if", "as", "any", "all", "there", "so",
        "what", "which", "who", "how", "where", "when", "why",
    }

    def _depluralize(self, word):
        if word.endswith('ies') and len(word) > 4:
            return word[:-3] + 'y'          # "queries" → "query"
        if word.endswith('s') and len(word) > 3 and not word.endswith('ss'):
            return word[:-1]                # "tokens" → "token", guards "access"/"process"
        return word

    def _tokenize(self, text):
        cleaned = text.lower()
        for ch in '.,!?;:"\'/\\()[]{}':
            cleaned = cleaned.replace(ch, ' ')
        return [self._depluralize(w) for w in cleaned.split()
                if w not in self.STOP_WORDS]

    def build_index(self, documents):
        """
        TODO (Phase 1):
        Build a tiny inverted index mapping lowercase words to the documents
        they appear in.

        Example structure:
        {
            "token": ["AUTH.md", "API_REFERENCE.md"],
            "database": ["DATABASE.md"]
        }

        Keep this simple: split on whitespace, lowercase tokens,
        ignore punctuation if needed.
        """
        index = {}
        for filename, text in documents:
            for word in self._tokenize(text):
                if word not in index:
                    index[word] = []
                if filename not in index[word]:
                    index[word].append(filename)
        return index

    # -----------------------------------------------------------
    # Scoring and Retrieval (Phase 1)
    # -----------------------------------------------------------

    def score_document(self, query, text):
        """
        TODO (Phase 1):
        Return a simple relevance score for how well the text matches the query.

        Suggested baseline:
        - Convert query into lowercase words
        - Count how many appear in the text
        - Return the count as the score
        """
        score, _ = self._score_document_with_matches(query, text)
        return score

    def _score_document_with_matches(self, query, text):
        """
        Returns (score, matched_words) where matched_words is the set of
        query tokens that appear in the document text.
        """
        text_words = set(self._tokenize(text))
        matched = set()
        for word in self._tokenize(query):
            if word in text_words:
                matched.add(word)
        return len(matched), matched

    def _confidence(self, query, matched_words):
        """
        Returns a confidence score in [0, 1]: the fraction of unique
        non-stop query tokens that were found in the document.
        """
        query_tokens = set(self._tokenize(query))
        if not query_tokens:
            return 0.0
        return round(len(matched_words) / len(query_tokens), 4)

    def retrieve(self, query, top_k=3, min_score=1):
        """
        TODO (Phase 1):
        Use the index and scoring function to select top_k relevant document snippets.

        Return a list of (filename, text) sorted by score descending.

        min_score: minimum number of query words that must appear in a document
        for it to be considered meaningful evidence. Documents below this
        threshold are excluded — they likely matched only on stop words.
        """
        candidate_filenames = set()
        for word in self._tokenize(query):
            if word in self.index:
                candidate_filenames.update(self.index[word])

        results = []
        for filename, text in self.documents:
            if filename in candidate_filenames:
                score, _ = self._score_document_with_matches(query, text)
                if score >= min_score:
                    results.append((score, filename, text))

        results.sort(key=lambda x: x[0], reverse=True)
        return [(filename, self._extract_snippet(query, text))
                for _, filename, text in results[:top_k]]

    def retrieve_with_scores(self, query, top_k=3, min_score=1):
        """
        Like retrieve(), but each result also includes a confidence score
        (0-1) and the set of matched words between the query and document.

        Returns a list of (filename, snippet, confidence, matched_words).
        """
        candidate_filenames = set()
        for word in self._tokenize(query):
            if word in self.index:
                candidate_filenames.update(self.index[word])

        results = []
        for filename, text in self.documents:
            if filename in candidate_filenames:
                score, matched = self._score_document_with_matches(query, text)
                if score >= min_score:
                    results.append((score, matched, filename, text))

        results.sort(key=lambda x: x[0], reverse=True)
        return [
            (filename, self._extract_snippet(query, text),
             self._confidence(query, matched), matched)
            for _, matched, filename, text in results[:top_k]
        ]

    def _extract_snippet(self, query, text):
        query_words = set(self._tokenize(query))
        paragraphs = text.split('\n\n')
        collected = []
        for i, p in enumerate(paragraphs):
            p = p.strip()
            if any(w in self._tokenize(p) for w in query_words):
                if p.startswith('#') and i + 1 < len(paragraphs):
                    collected.append(p + '\n\n' + paragraphs[i + 1].strip())
                else:
                    collected.append(p)
        return '\n\n'.join(collected[:3]) if collected else text[:500]

    # -----------------------------------------------------------
    # Answering Modes
    # -----------------------------------------------------------

    def answer_retrieval_only(self, query, top_k=3):
        """
        Phase 1 retrieval only mode.
        Returns raw snippets and filenames with no LLM involved.
        Includes a confidence score (0-1) and matched words for each result.
        """
        results = self.retrieve_with_scores(query, top_k=top_k)

        if not results:
            return "I do not know based on these docs."

        formatted = []
        for filename, text, confidence, matched_words in results:
            matched_display = ", ".join(sorted(matched_words)) if matched_words else "(none)"
            bar_len = 20
            filled = round(confidence * bar_len)
            bar = "[" + "#" * filled + "-" * (bar_len - filled) + "]"
            header = (
                f"[{filename}]\n"
                f"Confidence: {bar} {confidence:.2f}  "
                f"({len(matched_words)} / {len(set(self._tokenize(query)))} query words matched)\n"
                f"Matched words: {matched_display}"
            )
            formatted.append(f"{header}\n\n{text}\n")

        return "\n---\n".join(formatted)

    def answer_rag(self, query, top_k=3):
        """
        Phase 2 RAG mode.
        Uses student retrieval to select snippets, then asks Gemini
        to generate an answer using only those snippets.
        """
        if self.llm_client is None:
            raise RuntimeError(
                "RAG mode requires an LLM client. Provide a GeminiClient instance."
            )

        snippets = self.retrieve(query, top_k=top_k)

        if not snippets:
            return "I do not know based on these docs."

        return self.llm_client.answer_from_snippets(query, snippets)

    # -----------------------------------------------------------
    # Bonus Helper: concatenated docs for naive generation mode
    # -----------------------------------------------------------

    def full_corpus_text(self):
        """
        Returns all documents concatenated into a single string.
        This is used in Phase 0 for naive 'generation only' baselines.
        """
        return "\n\n".join(text for _, text in self.documents)
