"""Run a synthetic live model test without changing model configuration."""

import json
from types import SimpleNamespace
from ai_engine.forensic_assistant import analyze

artifact = SimpleNamespace(
    category="sms",
    id=1,
    evidence_id=1,
    source_ref="synthetic:1",
    timestamp_original="2026-01-01T10:00:00Z",
    sender="SYNTHETIC-A",
    recipient="SYNTHETIC-B",
    text="Synthetic test message: Please send PHP 1200 through GCash. Reference TEST-0001.",
)
result = analyze("Identify GCash references in the synthetic evidence.", [artifact])
print(json.dumps(result, indent=2))
if not result["findings"]:
    raise SystemExit("Model produced no verifiable findings")
