# Failure Modes

| Failure | Effect | Required control |
|---|---|---|
| Memory pollution | Retrieval becomes noisy | selective write gate |
| Incorrect extraction | False belief is stored | confidence, provenance, correction |
| Retrieval miss | Useful memory is ignored | keyword retrieval, later hybrid retrieval |
| Irrelevant retrieval | Context quality declines | ranking and golden-set evaluation |
| Feedback poisoning | False preference becomes durable | evidence threshold and explicit-source priority |
| Cross-owner leakage | Privacy breach | mandatory owner scope and adversarial tests |
| Secret persistence | Credential exposure | Aira Guard and redaction |
| Forgotten-memory leakage | User control is violated | lifecycle filtering and exact-match tests |
| Context overflow | Prompt is crowded or rejected | actual tokenizer budget |
| Database outage | Chat fails | no-memory fallback |
| Duplicate write | Repeated memories and audit events | idempotency key |
| Interrupted write | inconsistent state | transaction rollback |
| Stale preference | outdated personalization | superseding, validity and decay |
| Malformed import | corrupted store | validation and atomic import |
| Ranking regression | relevant memories disappear | versioned golden set and CI gate |
| Checkpoint incompatibility | model cannot load | versioned checkpoint schema |
| Resource exhaustion | M2 system becomes unusable | tiny configs, smoke modes and bounded batches |
