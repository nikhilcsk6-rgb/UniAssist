# Literature review (starter)
> Every reference below is a real publication I am confident exists. **Before submitting, open each one and verify authors, venue, year, volume/pages/DOI**, and add the further papers you actually read. Do not cite anything you have not opened.

**Transformers and LLMs.** The Transformer architecture [2] enabled large pre-trained language models that perform many tasks with few or no examples [3]. These models generate fluent text but can produce statements not supported by any source, termed hallucination, surveyed in [4].

**Retrieval-Augmented Generation.** RAG conditions generation on passages retrieved from an external corpus, improving factuality and allowing knowledge to be updated without retraining [1]. Dense retrieval using learned embeddings is a key component [5]. UniAssist applies this pattern to a closed university corpus and adds a similarity threshold and an explicit "not available" response.

**Evaluation with LLMs as judges.** Using a strong LLM to grade answers correlates reasonably with human preference but has known biases [6]; UniAssist therefore reports LLM-judged metrics together with a manual spot-check recommendation.

**Security of LLM applications.** Indirect prompt injection shows that instructions hidden in retrieved content can hijack LLM-integrated applications [7]. UniAssist treats documents as untrusted data: delimiting, excluding flagged chunks, and a system prompt that forbids following in-document instructions. These are mitigations, not guarantees.

**Gap addressed.** Many campus chatbots are demonstrated without measured comparison against a non-retrieval baseline; UniAssist includes a reproducible experiment module for that comparison.

## References (verify before use)
[1] P. Lewis et al., "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks," in *Advances in Neural Information Processing Systems (NeurIPS)*, vol. 33, 2020.
[2] A. Vaswani et al., "Attention Is All You Need," in *Advances in Neural Information Processing Systems*, vol. 30, 2017.
[3] T. B. Brown et al., "Language Models are Few-Shot Learners," in *Advances in Neural Information Processing Systems*, vol. 33, 2020.
[4] Z. Ji et al., "Survey of Hallucination in Natural Language Generation," *ACM Computing Surveys*, vol. 55, no. 12, 2023.
[5] V. Karpukhin et al., "Dense Passage Retrieval for Open-Domain Question Answering," in *Proc. EMNLP*, 2020.
[6] L. Zheng et al., "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena," in *NeurIPS Datasets and Benchmarks Track*, 2023.
[7] K. Greshake et al., "Not what you've signed up for: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection," in *Proc. ACM Workshop on Artificial Intelligence and Security (AISec)*, 2023.
