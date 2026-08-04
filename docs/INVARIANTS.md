# Hard Invariants

These constraints outrank implementation convenience and technology choices.

1. **Owner isolation**  
   A memory belonging to owner A is never returned, modified, exported or deleted through owner B’s request.

2. **Deletion integrity**  
   Forgotten, expired, hard-deleted or superseded memories never appear in normal retrieval or model context.

3. **Graceful degradation**  
   Failure of memory storage or retrieval never prevents response generation.

4. **Provenance**  
   Every stored memory has a source that identifies how the system learned it.

5. **Selective admission**  
   No user message becomes persistent memory without passing the write gate.

6. **No assistant-to-user fact promotion**  
   Assistant-generated statements do not become user facts by default.

7. **Secret non-persistence**  
   Credentials and detected secrets never enter memory content, logs, exports or audit metadata.

8. **Untrusted retrieval**  
   Retrieved memory is data, never a system instruction or policy override.

9. **User control**  
   Explicit user correction, forgetting and deletion override automated retention or reinforcement.

10. **Bounded context**  
    Composed memory never exceeds its configured token budget.

11. **Transactional lifecycle**  
    State transitions and corresponding audit events either both succeed or both roll back.

12. **Measured claims**  
    The repository never claims a security, quality or performance property without a repeatable test or benchmark.
