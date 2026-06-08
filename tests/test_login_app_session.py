from fastapi import Request
from fastapi.responses import Response

from app.lib.config import Settings
from app.lib.oauth import OAuthStateManager
from app.lib.session import SessionManager


def _request_with_cookie(name: str, value: str) -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/auth/callback",
        "headers": [(b"cookie", f"{name}={value}".encode())],
    }
    return Request(scope)


def test_oauth_state_preserves_login_app_metadata():
    settings = Settings(session_signing_secret="secret")
    manager = OAuthStateManager(settings)
    state = manager.generate(
        app="helpers",
        redirect_uri="https://helpers.k8.pminc.me/",
        session_cookie_domain=".pminc.me",
    )
    response = Response()

    manager.save_to_response(response, state)
    cookie = response.headers["set-cookie"].split(";", 1)[0].split("=", 1)[1]
    request = _request_with_cookie(settings.oauth_state_cookie_name, cookie)
    loaded = manager.load_from_request(request)

    assert loaded is not None
    assert loaded.app == "helpers"
    assert loaded.redirect_uri == "https://helpers.k8.pminc.me/"
    assert loaded.session_cookie_domain == ".pminc.me"


def test_session_cookie_can_be_scoped_to_parent_domain():
    settings = Settings(session_signing_secret="secret")
    manager = SessionManager(settings)
    response = Response()

    manager.set_cookie(response, "token", domain=".pminc.me")

    assert "Domain=.pminc.me" in response.headers["set-cookie"]
