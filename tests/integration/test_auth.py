import pytest

from vybora.core.errors import PermissionDeniedError, ValidationError
from vybora.services.container import build_services


@pytest.fixture()
def svc(db):
    return build_services(db)


def test_first_run_setup_and_login(svc):
    assert not svc.auth.is_initialized()
    ctx = svc.auth.setup_admin("admin", "মালিক", "strong-pass-123")
    assert svc.auth.is_initialized()
    assert ctx.has("users.manage") and ctx.has("sales.create")
    ctx2 = svc.auth.login("admin", "strong-pass-123")
    assert ctx2.user_id == ctx.user_id


def test_no_hardcoded_credentials(svc):
    # Before setup there are no users at all.
    assert svc.db.scalar("SELECT COUNT(*) FROM users") == 0


def test_wrong_password(svc):
    svc.auth.setup_admin("admin", "মালিক", "strong-pass-123")
    with pytest.raises(ValidationError):
        svc.auth.login("admin", "wrong-password")


def test_lockout_after_failures(svc):
    svc.auth.setup_admin("admin", "মালিক", "strong-pass-123")
    for _ in range(5):
        with pytest.raises(ValidationError):
            svc.auth.login("admin", "bad")
    # Even correct password is locked now.
    with pytest.raises(ValidationError):
        svc.auth.login("admin", "strong-pass-123")


def test_short_password_rejected(svc):
    with pytest.raises(ValidationError):
        svc.auth.setup_admin("admin", "মালিক", "short")


def test_duplicate_admin_rejected(svc):
    svc.auth.setup_admin("admin", "মালিক", "strong-pass-123")
    with pytest.raises(ValidationError):
        svc.auth.setup_admin("admin2", "আরেকজন", "strong-pass-456")


def test_password_change(svc):
    ctx = svc.auth.setup_admin("admin", "মালিক", "strong-pass-123")
    svc.auth.change_password(ctx, "strong-pass-123", "new-strong-pass-456")
    with pytest.raises(ValidationError):
        svc.auth.login("admin", "strong-pass-123")
    assert svc.auth.login("admin", "new-strong-pass-456").user_id == ctx.user_id


def test_password_change_wrong_current(svc):
    ctx = svc.auth.setup_admin("admin", "মালিক", "strong-pass-123")
    with pytest.raises(ValidationError):
        svc.auth.change_password(ctx, "wrong", "new-strong-pass-456")


def test_rbac_cashier_cannot_manage_users(svc):
    admin = svc.auth.setup_admin("admin", "মালিক", "strong-pass-123")
    svc.users.create_user(admin, "cashier1", "ক্যাশিয়ার", "cashier-pass-123", "cashier")
    cashier = svc.auth.login("cashier1", "cashier-pass-123")
    assert cashier.has("sales.create")
    assert not cashier.has("users.manage")
    with pytest.raises(PermissionDeniedError):
        svc.users.create_user(cashier, "x", "x", "password-123", "cashier")
    with pytest.raises(PermissionDeniedError):
        svc.settings.set(cashier, "tax_mode", "exclusive")


def test_deactivated_user_cannot_login(svc):
    admin = svc.auth.setup_admin("admin", "মালিক", "strong-pass-123")
    uid = svc.users.create_user(admin, "worker", "কর্মী", "worker-pass-123", "cashier")
    svc.users.set_active(admin, uid, False)
    with pytest.raises(ValidationError):
        svc.auth.login("worker", "worker-pass-123")


def test_audit_records_login(svc):
    svc.auth.setup_admin("admin", "মালিক", "strong-pass-123")
    svc.auth.login("admin", "strong-pass-123")
    actions = [r["action"] for r in svc.audit.recent()]
    assert "login.success" in actions
    assert "admin.setup" in actions


def test_audit_redacts_password(svc):
    admin = svc.auth.setup_admin("admin", "মালিক", "strong-pass-123")
    svc.users.create_user(admin, "u2", "ইউজার", "secret-pass-999", "cashier")
    for r in svc.audit.recent():
        if r["details_json"]:
            assert "secret-pass-999" not in r["details_json"]
