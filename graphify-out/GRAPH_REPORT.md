# Graph Report - .  (2026-07-04)

## Corpus Check
- Corpus is ~17,350 words - fits in a single context window. You may not need a graph.

## Summary
- 409 nodes · 635 edges · 36 communities (29 shown, 7 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 44 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Clinical Advisor UI|Clinical Advisor UI]]
- [[_COMMUNITY_Database Context & Connection|Database Context & Connection]]
- [[_COMMUNITY_Contraindications & Safety Logic|Contraindications & Safety Logic]]
- [[_COMMUNITY_RAG Pipeline Orchestrator & Embeddings|RAG Pipeline Orchestrator & Embeddings]]
- [[_COMMUNITY_Frontend Root Layout & Shell|Frontend Root Layout & Shell]]
- [[_COMMUNITY_API Schemas & Health Status|API Schemas & Health Status]]
- [[_COMMUNITY_Safety Interceptor Middleware|Safety Interceptor Middleware]]
- [[_COMMUNITY_Backend Settings & Configuration|Backend Settings & Configuration]]
- [[_COMMUNITY_Frontend Package Dependencies|Frontend Package Dependencies]]
- [[_COMMUNITY_TypeScript Configuration|TypeScript Configuration]]
- [[_COMMUNITY_Ollama AI Client & Suggestion Engine|Ollama AI Client & Suggestion Engine]]
- [[_COMMUNITY_PII Encryption Service|PII Encryption Service]]
- [[_COMMUNITY_Session Management API Router|Session Management API Router]]
- [[_COMMUNITY_RAG Background Worker Loop|RAG Background Worker Loop]]
- [[_COMMUNITY_Dashboard Analytics UI|Dashboard Analytics UI]]
- [[_COMMUNITY_FastAPI Logger Configuration|FastAPI Logger Configuration]]
- [[_COMMUNITY_Protocols Management UI|Protocols Management UI]]
- [[_COMMUNITY_Clinical System Prompts Configuration|Clinical System Prompts Configuration]]
- [[_COMMUNITY_ESLint Frontend Linter Configuration|ESLint Frontend Linter Configuration]]
- [[_COMMUNITY_Next.js Core Configuration|Next.js Core Configuration]]
- [[_COMMUNITY_PostCSS Style Configuration|PostCSS Style Configuration]]
- [[_COMMUNITY_Frontend Logging Module|Frontend Logging Module]]
- [[_COMMUNITY_Backend Test Fixtures Setup|Backend Test Fixtures Setup]]

## God Nodes (most connected - your core abstractions)
1. `get_db()` - 22 edges
2. `is_contraindicated()` - 17 edges
3. `TestContraindicationsRegistry` - 17 edges
4. `compilerOptions` - 16 edges
5. `fetchAPI()` - 15 edges
6. `semantic_search()` - 11 edges
7. `TestSafetyInterceptor` - 11 edges
8. `generate_suggestion()` - 10 edges
9. `SearchResultItem` - 10 edges
10. `extract_and_chunk()` - 10 edges

## Surprising Connections (you probably didn't know these)
- `SuggestionResult` --uses--> `SafetyResult`  [INFERRED]
  backend/ai/suggestion.py → backend/safety/interceptor.py
- `int` --uses--> `SafetyResult`  [INFERRED]
  backend/ai/suggestion.py → backend/safety/interceptor.py
- `str` --uses--> `SafetyResult`  [INFERRED]
  backend/ai/suggestion.py → backend/safety/interceptor.py
- `str` --uses--> `Settings`  [INFERRED]
  backend/rag/vector_store.py → backend/core/config.py
- `bool` --uses--> `DocumentChunk`  [INFERRED]
  backend/rag/pipeline.py → backend/rag/pdf_parser.py

## Import Cycles
- 1-file cycle: `backend/main.py -> backend/main.py`

## Communities (36 total, 7 thin omitted)

### Community 0 - "Clinical Advisor UI"
Cohesion: 0.07
Nodes (32): BODY_AREAS, RISK_FACTORS, checkSafety(), createPatient(), createSession(), deleteUpload(), fetchAPI(), getConfig() (+24 more)

### Community 1 - "Database Context & Connection"
Cohesion: 0.10
Nodes (36): str, bool, int, str, Connection, get_db(), Get an async database connection., PatientCreate (+28 more)

### Community 2 - "Contraindications & Safety Logic"
Cohesion: 0.10
Nodes (17): bool, str, get_all_protocols(), get_all_risk_factors(), get_blocked_protocols(), get_conflict_details(), is_contraindicated(), PhysioWave — Contraindications Registry (The "Redline" Safety Gate).  HIPAA Comp (+9 more)

### Community 3 - "RAG Pipeline Orchestrator & Embeddings"
Cohesion: 0.11
Nodes (29): float, str, bool, int, str, bool, int, str (+21 more)

### Community 4 - "Frontend Root Layout & Shell"
Cohesion: 0.08
Nodes (18): inter, metadata, outfit, Architecture, lifespan(), PhysioWave — FastAPI Application Entry Point.  HIPAA Compliance Note: All data s, Application startup/shutdown lifecycle., Root endpoint — API info. (+10 more)

### Community 5 - "API Schemas & Health Status"
Cohesion: 0.13
Nodes (23): check_ollama_status(), Check if Ollama is running and the required models are available., BaseModel, IntakeForm, HealthResponse, IntakeForm, PhysioWave — Pydantic Models (API schemas)., SafetyCheckRequest (+15 more)

### Community 6 - "Safety Interceptor Middleware"
Cohesion: 0.10
Nodes (14): str, ProtocolConflict, PhysioWave — Safety Interceptor.  HIPAA Compliance Note: This interceptor is the, Build user-facing warning message., A therapy protocol that conflicts with patient risk factors., Result of a safety validation check., Validates AI suggestions against the patient's risk profile.      HIPAA Complian, Validate an AI suggestion against patient risk factors.          Returns SafetyR (+6 more)

### Community 7 - "Backend Settings & Configuration"
Cohesion: 0.12
Nodes (23): Any, float, int, str, BaseSettings, PhysioWave — Application Configuration.  Loads settings from environment variabl, Application settings loaded from environment., Settings (+15 more)

### Community 8 - "Frontend Package Dependencies"
Cohesion: 0.08
Nodes (23): dependencies, next, pino, pino-pretty, react, react-dom, devDependencies, eslint (+15 more)

### Community 9 - "TypeScript Configuration"
Cohesion: 0.10
Nodes (19): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+11 more)

### Community 10 - "Ollama AI Client & Suggestion Engine"
Cohesion: 0.17
Nodes (17): chat(), chat_stream(), PhysioWave — Ollama LLM Client.  HIPAA Compliance Note: All inference runs 100%, Stream LLM response token-by-token.      Yields individual tokens as they are ge, Generate a complete (non-streaming) response., _build_search_query(), generate_suggestion(), generate_suggestion_stream() (+9 more)

### Community 11 - "PII Encryption Service"
Cohesion: 0.16
Nodes (11): bool, str, EncryptionService, PhysioWave — PII Encryption Service.  HIPAA Compliance Note: This module provide, AES-256 encryption for PII fields.      HIPAA Compliance Note: The encryption ke, Encrypt a plaintext string. Returns base64-encoded ciphertext., Decrypt a ciphertext string. Returns plaintext., Encrypt all PII fields in a dictionary. (+3 more)

### Community 12 - "Session Management API Router"
Cohesion: 0.23
Nodes (16): int, str, SessionCreate, SessionResponse, complete_session(), create_session(), get_session(), list_sessions() (+8 more)

### Community 13 - "RAG Background Worker Loop"
Cohesion: 0.20
Nodes (6): RAGWorker, PhysioWave — RAG Background Worker Pipeline.  This module replaces uncontrolled, Start the background worker loop., Find jobs hung in 'processing' and reset them to 'pending' for retry., Gracefully shutdown the worker., Check for pending or interrupted uploads and process one.

### Community 14 - "Dashboard Analytics UI"
Cohesion: 0.40
Nodes (3): QUICK_ACTIONS, STAT_CARDS, THERAPY_MODES

### Community 15 - "FastAPI Logger Configuration"
Cohesion: 0.50
Nodes (3): PhysioWave — HIPAA-Compliant Logger.  HIPAA Compliance Note: This logger automat, Configure the application logger with secure formatting and file output., setup_logging()

## Knowledge Gaps
- **62 isolated node(s):** `Connection`, `bool`, `bool`, `bool`, `eslintConfig` (+57 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `FastAPI` connect `Frontend Root Layout & Shell` to `Database Context & Connection`, `Session Management API Router`, `API Schemas & Health Status`?**
  _High betweenness centrality (0.107) - this node is a cross-community bridge._
- **Why does `semantic_search()` connect `RAG Pipeline Orchestrator & Embeddings` to `Database Context & Connection`, `Ollama AI Client & Suggestion Engine`, `Backend Settings & Configuration`?**
  _High betweenness centrality (0.084) - this node is a cross-community bridge._
- **Why does `get_db()` connect `Database Context & Connection` to `Session Management API Router`, `Frontend Root Layout & Shell`, `RAG Background Worker Loop`?**
  _High betweenness centrality (0.077) - this node is a cross-community bridge._
- **What connects `PhysioWave — Ollama LLM Client.  HIPAA Compliance Note: All inference runs 100%`, `Stream LLM response token-by-token.      Yields individual tokens as they are ge`, `Generate a complete (non-streaming) response.` to the rest of the system?**
  _156 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Clinical Advisor UI` be split into smaller, more focused modules?**
  _Cohesion score 0.07215541165587419 - nodes in this community are weakly interconnected._
- **Should `Database Context & Connection` be split into smaller, more focused modules?**
  _Cohesion score 0.09815078236130868 - nodes in this community are weakly interconnected._
- **Should `Contraindications & Safety Logic` be split into smaller, more focused modules?**
  _Cohesion score 0.10338680926916222 - nodes in this community are weakly interconnected._