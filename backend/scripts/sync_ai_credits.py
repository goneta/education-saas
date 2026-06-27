"""Scheduled job: refresh AI provider credit balances from official APIs.

Reuses the same logic as the Super Admin "Synchroniser via API" action so a
balance-capable provider (currently OpenRouter) stays up to date without manual
clicks. Providers whose API does not expose a balance keep their manual value
and are reported as `unsupported`.

Run from system cron, e.g. daily at 03:00:

    0 3 * * *  cd /opt/teducai && APP_ENV=production \
      python -m backend.scripts.sync_ai_credits >> /var/log/teducai/ai_sync.log 2>&1

The job is idempotent and safe to run as often as desired.
"""

import sys

from backend import audit, models
from backend.database import SessionLocal
from backend.services import ai_credit_sync


def run_sync(db) -> dict:
    """Sync all active providers and return a summary. Commits on success."""
    providers = db.query(models.AIProvider).filter(
        models.AIProvider.is_active == True  # noqa: E712
    ).order_by(models.AIProvider.priority.asc()).all()
    results = []
    synced = 0
    for provider in providers:
        result = ai_credit_sync.sync_provider_credits(provider)
        ai_credit_sync.apply_sync_result(provider, result)
        if result.get("status") == "synced":
            synced += 1
        results.append(result)
    audit.record_audit(
        db,
        action="platform.ai_credits.cron_synced",
        current_user=None,
        entity_type="ai_provider",
        entity_id="all",
        details={"synced": synced, "total": len(providers)},
    )
    db.commit()
    return {"synced": synced, "total": len(providers), "results": results}


def main() -> int:
    db = SessionLocal()
    try:
        summary = run_sync(db)
        for result in summary["results"]:
            suffix = f" ({result['available_credits']} credits)" if result.get("status") == "synced" else ""
            print(f"- {result.get('name')}: {result.get('status')}{suffix}")
        print(f"AI credit sync done: {summary['synced']}/{summary['total']} provider(s) synced via API.")
        return 0
    except Exception as exc:  # pragma: no cover - operational failure path
        db.rollback()
        print(f"AI credit sync failed: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
