from app.rate_limit import RateLimiter, client_ip


def register(client, username="player", password="test-password"):
    return client.post(
        "/api/v1/users/",
        json={"username": username, "password": password},
    )


def login(client, username="player", password="test-password"):
    return client.post(
        "/api/v1/users/login",
        json={"username": username, "password": password},
    )


# --- The limiter itself ---

def test_allows_up_to_the_limit_then_refuses():
    limiter = RateLimiter(max_attempts=3, window_seconds=60)

    assert limiter.check("k") is None
    assert limiter.check("k") is None
    assert limiter.check("k") is None

    retry_after = limiter.check("k")

    assert retry_after is not None
    assert retry_after > 0


def test_keys_are_counted_separately():
    limiter = RateLimiter(max_attempts=1, window_seconds=60)

    assert limiter.check("a") is None
    assert limiter.check("b") is None
    assert limiter.check("a") is not None


def test_reset_clears_a_key():
    limiter = RateLimiter(max_attempts=1, window_seconds=60)

    limiter.check("k")
    limiter.reset("k")

    assert limiter.check("k") is None


def test_client_ip_prefers_the_forwarded_header():
    """Behind Caddy every request appears to come from the proxy, so
    limiting on request.client would lock out everyone at once."""

    class Request:
        headers = {"x-forwarded-for": "203.0.113.7, 10.0.0.1"}
        client = type("C", (), {"host": "172.18.0.5"})()

    assert client_ip(Request()) == "203.0.113.7"


def test_client_ip_falls_back_when_no_proxy():
    class Request:
        headers = {}
        client = type("C", (), {"host": "192.0.2.9"})()

    assert client_ip(Request()) == "192.0.2.9"


# --- Applied to the endpoints ---

def test_the_public_user_list_is_gone(client):
    """It returned every username in the database to anyone."""
    assert client.get("/api/v1/users/").status_code == 405


def test_repeated_bad_logins_are_eventually_refused(client):
    register(client)

    seen_429 = False

    for _ in range(12):
        response = login(client, password="wrong-password")

        if response.status_code == 429:
            seen_429 = True
            assert "Retry-After" in response.headers
            break

        assert response.status_code == 401

    assert seen_429, "brute force was never rate limited"


def test_a_successful_login_clears_the_count(client):
    register(client)

    for _ in range(3):
        assert login(client, password="wrong-password").status_code == 401

    assert login(client).status_code == 200

    # The earlier failures must not count against them now.
    for _ in range(3):
        assert login(client, password="wrong-password").status_code == 401


def test_registration_is_rate_limited(client):
    # One more than the limit, so the test doesn't have to know the
    # exact number — only that a ceiling exists.
    codes = [register(client, username=f"user{n}").status_code for n in range(14)]

    assert 429 in codes
    assert codes.count(201) >= 5, "the limit must not be absurdly tight"


def test_login_does_not_reveal_whether_a_username_exists(client):
    register(client, username="realuser")

    missing = login(client, username="nosuchuser", password="x")
    wrong = login(client, username="realuser", password="x")

    assert missing.status_code == wrong.status_code == 401
    assert missing.json()["detail"] == wrong.json()["detail"]
