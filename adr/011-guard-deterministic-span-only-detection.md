# ADR: Deterministic, span-only secret detection with precision over recall

- Status: Accepted
- Date: 2026-08-06
- Last reviewed: 2026-08-06

## Context

Aira Guard is the pre-persistence gate (Step 03). It must block credentials and detected
secrets before they can enter memory, logs, exports or audit metadata (invariant 7), and
must never emit a raw secret. It runs offline with no third-party PII service and no LLM
(project constraints). Two design questions needed a recorded decision: how detectors
expose matches, and how to balance false positives against false negatives.

## Decision

1. **Span-only detectors.** Each detector returns a category and the *offsets* of a
   match, never the matched substring. The raw text is used only to compute redaction
   spans; nothing derived from a secret value leaves the detector layer. Redaction
   replaces spans with fixed tokens (e.g. `[REDACTED:api_key]`), and that redacted
   preview is the only content-bearing field on results, events and logs.
2. **Precision over recall.** Patterns target well-known, high-signal secret forms
   (PEM private keys, AWS/GitHub/Google/Slack/Stripe/OpenAI key shapes, JWTs, bearer
   tokens, credential URLs, cookie headers) and keyword-anchored assignments
   (`password: …`, `api_key = …`). Payment cards require a Luhn-valid 13–19 digit run.
   The aim is a low false-positive rate on ordinary prose; recall is explicitly not
   exhaustive and the covered set is documented and tested.
3. **Block restricted, flag the rest.** A detected secret blocks persistence and marks
   the content RESTRICTED. Do-not-remember and instruction/policy-override language are
   *reported* (for capture and untrusted-context handling) but do not themselves block.
4. **Bounded input.** Inputs larger than a configured byte limit are blocked without
   being scanned (a denial-of-service control).

## Alternatives considered

- Broad, greedy patterns (e.g. "any 32+ char token") for higher recall. Rejected:
  unacceptable false positives on IDs, hashes and UUIDs in normal text.
- Returning masked samples (e.g. last four characters) on findings. Rejected: any
  retained fragment weakens invariant 7; offsets plus a token are enough to redact.
- An LLM or hosted PII classifier. Rejected by project constraints (offline,
  deterministic, no cloud APIs).

## Consequences

- Deletion/secret-leak properties are structurally cheap to test: no output path can
  carry a raw value. Known-secret regression tests assert zero leakage across preview,
  reason, repr, serialized event and logs.
- Some real secrets in unusual formats will pass; capture and later review are the
  backstops, and the detector set can grow with tests. This is documented, not hidden.

## Traceability

- Upholds invariants: 5 (selective admission), 7 (secret non-persistence in content,
  logs, events), 8 (instruction-like content flagged as untrusted, not promoted), 12
  (deterministic, tested behaviour).
- Realized in stage 03; consumed by capture (Step 05) which runs the guard before any
  evaluation or persistence, and by Aira Trail (Step 04) whose events reuse the
  audit-safe `GuardEvent` shape.

## Migration path

Add detectors with accompanying tests as new secret formats appear. If a hosted or
learned classifier is ever justified, keep the `Guard` protocol and the span-only
contract so redaction and non-leakage guarantees are preserved.
