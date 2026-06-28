"""Access tracking service for PDF views."""
import uuid
from datetime import datetime
from typing import Optional


class AccessLogEntry:
    def __init__(self, account_id: str, ip_address: str, user_agent: str, source: str):
        self.log_id = uuid.uuid4().hex[:8]
        self.account_id = account_id
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.source = source
        self.timestamp = datetime.utcnow()


class AccessTracker:
    """In-memory access tracker (same as Java version).
    Optionally persists to DB for production use.
    """

    def __init__(self):
        self._logs: list[AccessLogEntry] = []
        self._counts: dict[str, int] = {}

    def log_access(self, account_id: str, ip_address: str, user_agent: str, source: str) -> AccessLogEntry:
        entry = AccessLogEntry(account_id, ip_address, user_agent, source)
        self._logs.append(entry)
        self._counts[account_id] = self._counts.get(account_id, 0) + 1
        return entry

    def get_logs(self, account_id: Optional[str] = None) -> list[dict]:
        filtered = self._logs
        if account_id:
            filtered = [l for l in filtered if l.account_id == account_id]
        filtered.sort(key=lambda x: x.timestamp, reverse=True)

        result = []
        for entry in filtered[:200]:
            result.append({
                "id": entry.log_id,
                "accountId": entry.account_id,
                "ipAddress": entry.ip_address,
                "source": entry.source,
                "timestamp": entry.timestamp.isoformat(),
                "userAgent": (entry.user_agent[:80] + "...") if entry.user_agent and len(entry.user_agent) > 80 else (entry.user_agent or ""),
            })
        return result

    def get_stats(self) -> dict:
        return {
            "totalAccesses": len(self._logs),
            "uniqueAccounts": len(self._counts),
            "topAccounts": [
                {"accountId": k, "count": v}
                for k, v in sorted(self._counts.items(), key=lambda x: -x[1])[:10]
            ],
        }

    def get_count(self, account_id: str) -> int:
        return self._counts.get(account_id, 0)


# Global singleton (same as Java's @Service)
tracker = AccessTracker()
