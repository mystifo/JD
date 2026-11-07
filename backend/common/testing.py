"""Reusable assertions for the cross-tenant authorization matrix.

Every user-owned resource test calls `assert_cross_user_hidden`, which fails if
another user can read, update, or delete the row. The harness itself is tested
by `common/tests/test_authorization_harness.py` against a deliberately leaky
view, so a broken harness cannot pass silently.
"""

DEFAULT_METHOD = "get"


def _call(client, method, url, payload):
    handler = getattr(client, method)
    if payload is None:
        return handler(url)
    return handler(url, payload, format="json")


def assert_owner_visible(client, url, *, method=DEFAULT_METHOD, payload=None, expected=200):
    response = _call(client, method, url, payload)
    assert response.status_code == expected, (
        f"owner expected {expected} for {method.upper()} {url}, "
        f"got {response.status_code}: {_body(response)}"
    )
    return response


def assert_cross_user_hidden(client, url, *, method=DEFAULT_METHOD, payload=None, expected=404):
    """The other user must receive `expected` (404, never 403)."""
    response = _call(client, method, url, payload)
    assert response.status_code == expected, (
        f"cross-tenant leak: expected {expected} for {method.upper()} {url}, "
        f"got {response.status_code}: {_body(response)}"
    )
    return response


def assert_anonymous_denied(client, url, *, method=DEFAULT_METHOD, payload=None, expected=401):
    response = _call(client, method, url, payload)
    assert response.status_code == expected, (
        f"anonymous expected {expected} for {method.upper()} {url}, "
        f"got {response.status_code}: {_body(response)}"
    )
    return response


def _body(response):
    try:
        return response.content[:400]
    except Exception:  # pragma: no cover - defensive
        return b"<unreadable>"
