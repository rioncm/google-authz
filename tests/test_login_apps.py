from pathlib import Path

from app.lib.login_apps import LoginAppRegistry


def test_login_app_registry_validates_approved_redirect(tmp_path: Path):
    config_path = tmp_path / "login-apps.yaml"
    config_path.write_text(
        """
login_apps:
  - app: helpers
    display_name: Little Helpers
    app_domains:
      - helpers.k8.pminc.me
    app_redirects:
      - https://helpers.k8.pminc.me/
    session_cookie_domain: .pminc.me
    required_login_permission: helpers:login
""",
        encoding="utf-8",
    )

    registry = LoginAppRegistry.from_file(config_path)
    app = registry.validate_redirect("helpers", "https://helpers.k8.pminc.me/")

    assert app.app == "helpers"
    assert app.session_cookie_domain == ".pminc.me"
    assert registry.cookie_domains() == {".pminc.me"}


def test_login_app_registry_rejects_unknown_app(tmp_path: Path):
    config_path = tmp_path / "login-apps.yaml"
    config_path.write_text("login_apps: []\n", encoding="utf-8")

    registry = LoginAppRegistry.from_file(config_path)

    try:
        registry.validate_redirect("helpers", "https://helpers.k8.pminc.me/")
    except ValueError as exc:
        assert str(exc) == "Unknown login app"
    else:
        raise AssertionError("Expected unknown app rejection")


def test_login_app_registry_rejects_unapproved_redirect(tmp_path: Path):
    config_path = tmp_path / "login-apps.yaml"
    config_path.write_text(
        """
login_apps:
  - app: helpers
    app_domains:
      - helpers.k8.pminc.me
    app_redirects:
      - https://helpers.k8.pminc.me/
""",
        encoding="utf-8",
    )

    registry = LoginAppRegistry.from_file(config_path)

    try:
        registry.validate_redirect("helpers", "https://evil.example.com/")
    except ValueError as exc:
        assert str(exc) == "redirect_uri is not approved for this app"
    else:
        raise AssertionError("Expected redirect rejection")
