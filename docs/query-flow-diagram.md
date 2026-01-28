# RAG Chatbot Query Flow Diagram

## Complete User Query Processing Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                   FRONTEND                                       │
│                              (frontend/script.js)                                │
└─────────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       │ 1. User types query
                                       │    "What is prompt caching?"
                                       ▼
                        ┌──────────────────────────────┐
                        │   sendMessage()              │
                        │   - Get query from input     │
                        │   - Show loading animation   │
                        │   - Prepare HTTP request     │
                        └──────────────┬───────────────┘
                                       │
                                       │ 2. POST /api/query
                                       │    Body: {query, session_id}
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              FASTAPI BACKEND                                     │
│                                (backend/app.py)                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       │ 3. Endpoint: query_documents()
                                       ▼
                        ┌──────────────────────────────┐
                        │   Create/Get Session ID      │
                        │   - Generate if new          │
                        │   - Use existing if provided │
                        └──────────────┬───────────────┘
                                       │
                                       │ 4. Call rag_system.query()
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              RAG ORCHESTRATOR                                    │
│                            (backend/rag_system.py)                               │
└─────────────────────────────────────────────────────────────────────────────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                  │
                    ▼                  ▼                  ▼
         ┌──────────────────┐  ┌─────────────┐  ┌──────────────────┐
         │ Session Manager  │  │ Build Prompt│  │  Tool Manager    │
         │ Get conversation │  │ with context│  │  Get tool defs   │
         │ history          │  │             │  │  for Claude      │
         └──────────────────┘  └─────────────┘  └──────────────────┘
                    │                  │                  │
                    └──────────────────┼──────────────────┘
                                       │
                                       │ 5. Call ai_generator.generate_response()
                                       │    (query, history, tools, tool_manager)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              AI GENERATOR                                        │
│                          (backend/ai_generator.py)                               │
└─────────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       │ 6. First Claude API Call
                                       ▼
                        ┌──────────────────────────────┐
                        │   Anthropic API Call #1      │
                        │   ┌────────────────────────┐ │
                        │   │ System: Course Q&A     │ │
                        │   │ History: [prev msgs]   │ │
                        │   │ Tools: [search_tool]   │ │
                        │   │ User: "What is prompt  │ │
                        │   │        caching?"       │ │
                        │   └────────────────────────┘ │
                        └──────────────┬───────────────┘
                                       │
                                       │ 7. Response: stop_reason="tool_use"
                                       ▼
                        ┌──────────────────────────────┐
                        │   Claude Decides to Use      │
                        │   search_course_content      │
                        │   with query="prompt caching"│
                        └──────────────┬───────────────┘
                                       │
                                       │ 8. _handle_tool_execution()
                                       ▼
                        ┌──────────────────────────────┐
                        │   tool_manager.execute_tool  │
                        │   ("search_course_content",  │
                        │    query="prompt caching")   │
                        └──────────────┬───────────────┘
                                       │
                                       │ 9. Execute search tool
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              SEARCH TOOL                                         │
│                          (backend/search_tools.py)                               │
└─────────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       │ 10. CourseSearchTool.execute()
                                       ▼
                        ┌──────────────────────────────┐
                        │   vector_store.search()      │
                        │   - query: "prompt caching"  │
                        │   - course_name: None        │
                        │   - lesson_number: None      │
                        └──────────────┬───────────────┘
                                       │
                                       │ 11. Perform vector search
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              VECTOR STORE                                        │
│                          (backend/vector_store.py)                               │
└─────────────────────────────────────────────────────────────────────────────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                  │
                    ▼                  ▼                  ▼
         ┌──────────────────┐  ┌─────────────┐  ┌──────────────────┐
         │ Embed query with │  │   ChromaDB  │  │ Return top 5     │
         │ SentenceTransf.  │→ │   Cosine    │→ │ matching chunks  │
         │ → 384-dim vector │  │  Similarity │  │ with metadata    │
         └──────────────────┘  └─────────────┘  └──────────────────┘
                                                          │
                                       ┌──────────────────┘
                                       │ 12. Return SearchResults
                                       ▼
                        ┌──────────────────────────────┐
                        │   Results contain:           │
                        │   - documents: [chunk texts] │
                        │   - metadata: [{course,      │
                        │      lesson_number}]         │
                        │   - distances: [0.23, 0.31]  │
                        └──────────────┬───────────────┘
                                       │
                                       │ 13. Back to Search Tool
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              SEARCH TOOL                                         │
└─────────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       │ 14. Format results with context
                                       ▼
                        ┌──────────────────────────────┐
                        │   _format_results()          │
                        │   ┌────────────────────────┐ │
                        │   │ [Course - Lesson 3]    │ │
                        │   │ Prompt caching retains │ │
                        │   │ ...                    │ │
                        │   │                        │ │
                        │   │ [Course - Lesson 5]    │ │
                        │   │ With prompt caching... │ │
                        │   └────────────────────────┘ │
                        │   + Track sources in        │
                        │     last_sources[]          │
                        └──────────────┬───────────────┘
                                       │
                                       │ 15. Return formatted string
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              AI GENERATOR                                        │
└─────────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       │ 16. Second Claude API Call
                                       ▼
                        ┌──────────────────────────────┐
                        │   Anthropic API Call #2      │
                        │   ┌────────────────────────┐ │
                        │   │ User: original query   │ │
                        │   │ Assistant: tool_use    │ │
                        │   │ User: tool_result with │ │
                        │   │   [Course - Lesson 3]  │ │
                        │   │   Prompt caching...    │ │
                        │   └────────────────────────┘ │
                        └──────────────┬───────────────┘
                                       │
                                       │ 17. Claude synthesizes answer
                                       ▼
                        ┌──────────────────────────────┐
                        │   Final Answer Generated:    │
                        │   "Prompt caching retains    │
                        │    some of the results of    │
                        │    processing prompts..."    │
                        └──────────────┬───────────────┘
                                       │
                                       │ 18. Return response text
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              RAG ORCHESTRATOR                                    │
└─────────────────────────────────────────────────────────────────────────────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                  │
                    ▼                  ▼                  ▼
         ┌──────────────────┐  ┌─────────────┐  ┌──────────────────┐
         │ Get sources from │  │   Update    │  │  Prepare return  │
         │ tool_manager     │  │ session     │  │  tuple           │
         │ ["Course-Lesson"]│  │  history    │  │  (answer, sources)│
         └──────────────────┘  └─────────────┘  └──────────────────┘
                    │                  │                  │
                    └──────────────────┼──────────────────┘
                                       │
                                       │ 19. Return (answer, sources)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              FASTAPI BACKEND                                     │
└─────────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       │ 20. Build JSON response
                                       ▼
                        ┌──────────────────────────────┐
                        │   QueryResponse:             │
                        │   {                          │
                        │     answer: "...",           │
                        │     sources: ["Course.."],   │
                        │     session_id: "sess_123"   │
                        │   }                          │
                        └──────────────┬───────────────┘
                                       │
                                       │ 21. HTTP Response
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                   FRONTEND                                       │
└─────────────────────────────────────────────────────────────────────────────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                  │
                    ▼                  ▼                  ▼
         ┌──────────────────┐  ┌─────────────┐  ┌──────────────────┐
         │ Remove loading   │  │   Convert   │  │  Add collapsible │
         │ animation        │  │  markdown   │  │  sources section │
         │                  │  │  to HTML    │  │                  │
         └──────────────────┘  └─────────────┘  └──────────────────┘
                    │                  │                  │
                    └──────────────────┼──────────────────┘
                                       │
                                       │ 22. Display to user
                                       ▼
                        ┌──────────────────────────────┐
                        │   USER SEES ANSWER           │
                        │   ┌────────────────────────┐ │
                        │   │ 🤖 Prompt caching      │ │
                        │   │    retains some of...  │ │
                        │   │                        │ │
                        │   │ ▸ Sources (2)          │ │
                        │   └────────────────────────┘ │
                        └──────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════════════

## Key Data Structures at Each Stage

### Stage 1: Frontend Request
```javascript
{
  query: "What is prompt caching?",
  session_id: "sess_123"
}
```

### Stage 2: Claude API Call #1 (Tool Decision)
```json
{
  "model": "claude-sonnet-4-20250514",
  "messages": [{"role": "user", "content": "Answer this question..."}],
  "system": "You are an AI assistant...\n\nPrevious conversation:\n...",
  "tools": [{
    "name": "search_course_content",
    "input_schema": {...}
  }]
}
```

### Stage 3: Claude Response (Tool Use)
```json
{
  "stop_reason": "tool_use",
  "content": [{
    "type": "tool_use",
    "id": "toolu_123",
    "name": "search_course_content",
    "input": {"query": "prompt caching"}
  }]
}
```

### Stage 4: Vector Search Query
```python
query_texts=["prompt caching"]  # Embedded to 384-dim vector
n_results=5
where=None  # No filters
```

### Stage 5: ChromaDB Results
```python
{
  'documents': [["Prompt caching retains...", "With prompt caching..."]],
  'metadatas': [[
    {'course_title': 'Building Towards...', 'lesson_number': 3},
    {'course_title': 'Building Towards...', 'lesson_number': 5}
  ]],
  'distances': [[0.23, 0.31]]
}
```

### Stage 6: Formatted Tool Result
```
[Building Towards Computer Use with Anthropic - Lesson 3]
Prompt caching retains some of the results of processing prompts...

[Building Towards Computer Use with Anthropic - Lesson 5]
With prompt caching, you can cache portions of your system prompt...
```

### Stage 7: Claude API Call #2 (Answer Synthesis)
```json
{
  "messages": [
    {"role": "user", "content": "Answer this question..."},
    {"role": "assistant", "content": [{"type": "tool_use", ...}]},
    {"role": "user", "content": [{"type": "tool_result", "content": "[Course...]"}]}
  ]
}
```

### Stage 8: Final Response
```json
{
  "answer": "Prompt caching retains some of the results...",
  "sources": ["Building Towards Computer Use with Anthropic - Lesson 3", ...],
  "session_id": "sess_123"
}
```

═══════════════════════════════════════════════════════════════════════════════════

## Processing Time Breakdown (Typical)

```
┌─────────────────────────┬──────────────┐
│ Stage                   │ Time         │
├─────────────────────────┼──────────────┤
│ Frontend → API          │ ~50ms        │
│ Session/History Load    │ ~10ms        │
│ Claude API Call #1      │ ~800ms       │
│ Tool Execution:         │              │
│   - Vector Embedding    │ ~50ms        │
│   - ChromaDB Search     │ ~100ms       │
│   - Result Formatting   │ ~10ms        │
│ Claude API Call #2      │ ~1500ms      │
│ Response Assembly       │ ~20ms        │
│ API → Frontend          │ ~50ms        │
│ Frontend Rendering      │ ~30ms        │
├─────────────────────────┼──────────────┤
│ TOTAL                   │ ~2.6 seconds │
└─────────────────────────┴──────────────┘
```

═══════════════════════════════════════════════════════════════════════════════════

## Component Dependencies

```
frontend/script.js
    └─→ backend/app.py (FastAPI endpoints)
            └─→ backend/rag_system.py (Orchestrator)
                    ├─→ backend/session_manager.py (History)
                    ├─→ backend/ai_generator.py (Claude API)
                    │       └─→ Anthropic API (External)
                    └─→ backend/search_tools.py (Tool execution)
                            └─→ backend/vector_store.py (ChromaDB)
                                    └─→ ChromaDB (Persistent storage)
                                    └─→ SentenceTransformer (Embeddings)
```
