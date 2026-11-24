# UniAssist: A Retrieval-Augmented University Assistant - Design and Evaluation (IEEE-style skeleton)
**Authors:** [Your name], [Guide name], [Department, Institution]

**Abstract** - Reuse docs/academic/01. Then add 1-2 sentences with your *measured* headline result, e.g. "On a benchmark of N questions, RAG improved accuracy from X to Y and reduced hallucination from P% to Q%." **Leave blank until you have run the experiment.**

**Index Terms** - retrieval-augmented generation, large language models, educational chatbot, hallucination.

## I. Introduction
Problem, motivation, contributions (system, safeguards, evaluation module).
## II. Related Work
Condense 03_LITERATURE_REVIEW.md plus papers you read.
## III. System Design
A. Architecture (docs/DIAGRAMS.md). B. RAG pipeline: PyMuPDF/python-docx extraction, 800/120 character chunks, Gemini embeddings, ChromaDB cosine search, access filtering. C. Hallucination safeguards: similarity threshold, NOT_FOUND protocol, citations, low temperature. D. Prompt-injection mitigation. E. Other modules.
## IV. Experimental Setup
Benchmark (source, size, how reference answers were verified), documents indexed, LLM and embedding model names/versions, temperature, top-k, similarity threshold, metric definitions:
* Accuracy: 1/0.5/0 by LLM judge against reference. Relevance 0-1. Hallucination: judged unsupported/contradicting facts. Abstention counted as incorrect but not hallucination.
* Citation accuracy: fraction of RAG answers citing the reference document (and page when given). Retrieval precision: share of retrieved chunks from the reference document/page. Response time: end-to-end ms. User satisfaction: mean 1-5 rating from real users.
## V. Results
Insert tables/figures exported from the Research page (CSV/PDF). Report n, and mention that no statistical significance test was run unless you add one.
## VI. Discussion and Threats to Validity
LLM-as-judge bias; small benchmark; fictional/sample documents if used; single LLM; threshold tuning; scanned PDFs unsupported.
## VII. Conclusion and Future Work
OCR, hybrid search, re-ranking, evaluation with human raters, larger user study.
## References
Use verified entries only.
