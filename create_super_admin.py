from backend.database import SessionLocal
from backend.services.super_admin import ensure_super_admin


def main() -> None:
    db = SessionLocal()
    try:
        result = ensure_super_admin(db)
        db.commit()
        print("Super admin account is ready.")
        print(f"Created: {result.created}")
        print(f"Username: {result.user.username}")
        print(f"Email: {result.user.email}")
        print(f"Role: {result.user.role.value}")
        print(f"AI credits: {result.wallet.balance_credits}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
