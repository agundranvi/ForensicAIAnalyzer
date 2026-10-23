import re
from collections import Counter

PATTERNS = {
    "amount": r"(?i)(?:PHP|USD|\u20b1|\$)\s*[\d,]+(?:\.\d{1,2})?",
    "payment_service": r"(?i)\b(?:gcash|maya|bitcoin|ethereum|payment|transfer)\b",
    "account_reference": r"(?i)\b(?:account|acct|reference|ref|transaction)\s*[:#-]?\s*([A-Za-z0-9-]{6,40})",
    "crypto_candidate": r"\b(?:0x[a-fA-F0-9]{40}|bc1[a-zA-HJ-NP-Z0-9]{25,62}|[13][a-km-zA-HJ-NP-Z1-9]{25,34})\b",
}


def financial(artifacts):
    return [
        dict(
            artifact_id=a.id,
            kind=kind,
            value=m.group(0),
            status="Unverified indicator; does not establish a transaction",
        )
        for a in artifacts
        for kind, pattern in PATTERNS.items()
        for m in re.finditer(pattern, a.text)
    ]


def statistics(artifacts):
    counts = Counter(a.category for a in artifacts)
    messages = [
        a
        for a in artifacts
        if any(k in a.category for k in ("sms", "mms", "message", "chat"))
    ]
    calls = [a for a in artifacts if "call" in a.category]
    metrics = {
        "messages": len(messages),
        "incoming_messages": sum(
            a.direction.lower() in ("incoming", "inbound", "received") for a in messages
        ),
        "outgoing_messages": sum(
            a.direction.lower() in ("outgoing", "outbound", "sent") for a in messages
        ),
        "calls": len(calls),
        "incoming_calls": sum(
            a.direction.lower() in ("incoming", "inbound", "received") for a in calls
        ),
        "outgoing_calls": sum(
            a.direction.lower() in ("outgoing", "outbound", "sent") for a in calls
        ),
        "missed_calls": sum(
            a.direction.lower() == "missed" or "missed" in a.category for a in calls
        ),
        "contacts": sum("contact" in a.category for a in artifacts),
    }
    return {
        "metrics": metrics,
        "categories": dict(counts),
        "directions": dict(Counter(a.direction or "unknown" for a in artifacts)),
        "contacts": dict(
            Counter(
                x for a in artifacts for x in (a.sender, a.recipient) if x
            ).most_common()
        ),
        "days": dict(
            sorted(
                Counter(
                    a.timestamp_utc[:10] for a in artifacts if a.timestamp_utc
                ).items()
            )
        ),
    }


def clusters(edges):
    """Connected recorded endpoints; no identity or ownership inference."""
    parents = {}

    def root(value):
        parents.setdefault(value, value)
        while parents[value] != value:
            parents[value] = parents[parents[value]]
            value = parents[value]
        return value

    for source, target in edges:
        parents[root(source)] = root(target)
    groups = {}
    for endpoint in parents:
        groups.setdefault(root(endpoint), {"endpoints": [], "artifact_ids": []})[
            "endpoints"
        ].append(endpoint)
    for (source, target), ids in edges.items():
        groups[root(source)]["artifact_ids"].extend(ids)
    return list(groups.values())
