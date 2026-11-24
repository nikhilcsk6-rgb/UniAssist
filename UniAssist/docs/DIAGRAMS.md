# Diagrams (Mermaid)
Paste any block into https://mermaid.live or view in VS Code/GitHub to render, then export as image for the report.

## ER diagram
```mermaid
erDiagram
  ROLES ||--o{ USERS : has
  USERS ||--o{ DOCUMENTS : owns
  USERS ||--o{ CHAT_SESSIONS : starts
  CHAT_SESSIONS ||--o{ CHAT_MESSAGES : contains
  DOCUMENTS ||--o{ CHAT_SESSIONS : "scopes (document mode)"
  USERS ||--o{ GENERATED_QUESTIONS : generates
  DOCUMENTS ||--o{ GENERATED_QUESTIONS : "source of"
  USERS ||--o{ QUIZZES : creates
  QUIZZES ||--o{ QUIZ_RESULTS : has
  USERS ||--o{ QUIZ_RESULTS : takes
  USERS ||--o{ ANNOUNCEMENTS : publishes
  USERS ||--o{ FEEDBACK : submits
  CHAT_MESSAGES ||--o{ FEEDBACK : "rated by"
  USERS ||--o{ BENCHMARK_ITEMS : uploads
  USERS ||--o{ RESEARCH_EXPERIMENTS : runs
  RESEARCH_EXPERIMENTS ||--o{ EVALUATION_METRICS : records
  BENCHMARK_ITEMS ||--o{ EVALUATION_METRICS : "evaluated in"
  USERS ||--o{ ACTIVITY_LOGS : generates
```

## System architecture
```mermaid
flowchart LR
  U[Student / Faculty / Admin] --> FE[React + Tailwind SPA]
  FE -->|REST + JWT| API[Flask API]
  API --> DB[(MySQL)]
  API --> VS[(ChromaDB)]
  API -->|LLM + embeddings| G[Google Gemini API]
  API --> FS[(Upload folder)]
```

## DFD level 0
```mermaid
flowchart LR
  S[Student] -->|questions, files| P((UniAssist))
  F[Faculty] -->|materials, announcements| P
  A[Admin] -->|official docs, benchmark| P
  P -->|cited answers, notes, papers, quizzes| S
  P -->|papers, quizzes| F
  P -->|analytics, research results| A
  P <-->|prompts / responses| L[Gemini LLM]
```

## DFD level 1 (RAG)
```mermaid
flowchart TD
  D[Document upload] --> V[1. Validate file] --> X[2. Extract text per page] --> C[3. Chunk 800/120] --> E[4. Embed] --> VS[(ChromaDB)]
  Q[User question] --> QE[5. Embed query] --> R[6. Retrieve top-k with access filter] --> VS
  R --> T{similarity >= threshold?}
  T -- no --> NF[Return 'not available']
  T -- yes --> G[7. Gemini with untrusted-context prompt] --> CI[8. Answer + citations] --> M[(chat_messages)]
```

## Use case diagram
```mermaid
flowchart LR
  St((Student)) --- UC1[Ask chatbot] & UC2[Analyse document] & UC3[Generate questions / quiz] & UC4[Study tools] & UC5[View announcements] & UC6[Give feedback]
  Fa((Faculty)) --- UC2 & UC3 & UC5 & UC7[Upload study material] & UC8[Publish announcements]
  Ad((Admin)) --- UC9[Manage users] & UC10[Manage official knowledge base] & UC11[View analytics] & UC12[Run RAG vs non-RAG experiments] & UC8
```

## Sequence: RAG question answering
```mermaid
sequenceDiagram
  actor U as User
  participant FE as React
  participant API as Flask /chat
  participant VS as ChromaDB
  participant LLM as Gemini
  participant DB as MySQL
  U->>FE: type question
  FE->>API: POST /chat/sessions/{id}/messages (JWT)
  API->>VS: query(embedding, filter public OR owner)
  VS-->>API: top-k chunks + page metadata
  alt no chunk above threshold
    API-->>FE: "not available" (no LLM call)
  else relevant chunks
    API->>LLM: system rules + delimited untrusted sources + question
    LLM-->>API: answer with [n] citations (or NOT_FOUND)
    API->>DB: save messages, sources, latency
    API-->>FE: answer + sources (file, page)
  end
```

## Class diagram (backend models and services)
```mermaid
classDiagram
  class User{id; email; password_hash; role; preferred_language}
  class Document{id; owner_id; category; visibility; status; chunk_count}
  class ChatSession{id; mode; language; document_id}
  class ChatMessage{id; sender; content; sources; grounded; response_time_ms}
  class Quiz{id; questions}
  class ResearchExperiment{id; temperature; top_k; is_sample}
  class EvaluationMetric{variant; accuracy_score; hallucinated; citation_correct}
  class RagService{answer_question()}
  class Ingestion{index_document(); search()}
  class LLM{generate(); extract_json()}
  User "1" --> "*" Document
  User "1" --> "*" ChatSession
  ChatSession "1" --> "*" ChatMessage
  ResearchExperiment "1" --> "*" EvaluationMetric
  RagService --> Ingestion
  RagService --> LLM
```
