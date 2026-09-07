import pytest

from app.models.blackout import BlackoutArticle, BlackoutChallenge
from app.services.blackout import redact, tokenize


LEAD = (
    "Napoleon Bonaparte was a French military commander who rose to "
    "prominence during the Revolution. He led successful campaigns and "
    "was crowned emperor in 1804. His campaigns are studied at military "
    "schools worldwide."
)


@pytest.fixture
def article(db_session):
    stored = BlackoutArticle(
        title="Napoleon",
        lead=LEAD,
        source_url="https://en.wikipedia.org/wiki/Napoleon",
    )

    db_session.add(stored)
    db_session.commit()
    db_session.refresh(stored)

    return stored


def test_today_never_sends_the_article_text(client, article):
    response = client.get("/api/v1/blackout/today")

    assert response.status_code == 200

    body = response.text

    assert "Napoleon" not in body
    assert "Bonaparte" not in body
    assert "emperor" not in body
    # The source URL contains the title, so it stays back too.
    assert "wikipedia.org" not in body


def test_hidden_tokens_carry_only_a_length(client, article):
    data = client.get("/api/v1/blackout/today").json()

    hidden = [
        token
        for token in data["body_tokens"]
        if token["kind"] == "word"
    ]

    assert hidden
    assert all(token["text"] is None for token in hidden)
    assert all(token["length"] > 0 for token in hidden)


def test_every_word_is_hidden_including_common_ones(client, article):
    """Revealing "the" and "of" gives away sentence structure, which is
    most of the difficulty."""
    data = client.get("/api/v1/blackout/today").json()

    visible = [
        token["text"]
        for token in data["body_tokens"]
        if token["kind"] == "fixed"
    ]

    assert "was" not in visible
    assert "the" not in visible
    assert "The" not in visible

    # Numbers and punctuation stay: they shape the page without giving
    # away vocabulary.
    assert "1804" in visible
    assert "." in visible


def test_title_word_count_does_not_reveal_the_title(client, article):
    data = client.get("/api/v1/blackout/today").json()

    assert data["title_word_count"] == 1
    assert all(
        token["text"] is None
        for token in data["title_tokens"]
        if token["kind"] == "word"
    )


def test_a_correct_guess_returns_every_position(client, article):
    challenge_id = client.get("/api/v1/blackout/today").json()["challenge_id"]

    response = client.post(
        "/api/v1/blackout/guess",
        json={"challenge_id": challenge_id, "guess": "campaigns"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 2
    assert len(data["body_hits"]) == 2
    assert all(hit["text"] == "campaigns" for hit in data["body_hits"])


def test_guessing_is_case_insensitive_but_keeps_the_original(
    client,
    article,
):
    challenge_id = client.get("/api/v1/blackout/today").json()["challenge_id"]

    response = client.post(
        "/api/v1/blackout/guess",
        json={"challenge_id": challenge_id, "guess": "NAPOLEON"},
    )

    data = response.json()

    assert data["title_hits"] == [{"index": 0, "text": "Napoleon"}]
    assert data["body_hits"][0]["text"] == "Napoleon"


def test_a_wrong_guess_reveals_nothing(client, article):
    challenge_id = client.get("/api/v1/blackout/today").json()["challenge_id"]

    response = client.post(
        "/api/v1/blackout/guess",
        json={"challenge_id": challenge_id, "guess": "bicycle"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "guess": "bicycle",
        "title_hits": [],
        "body_hits": [],
        "count": 0,
    }


def test_common_words_are_guessable(client, article):
    """Since they start hidden, guessing them has to uncover them."""
    challenge_id = client.get("/api/v1/blackout/today").json()["challenge_id"]

    response = client.post(
        "/api/v1/blackout/guess",
        json={"challenge_id": challenge_id, "guess": "was"},
    )

    assert response.json()["count"] == 2


def test_non_word_guesses_are_rejected(client, article):
    challenge_id = client.get("/api/v1/blackout/today").json()["challenge_id"]

    for bad in ["", "   ", "12345", "two words"]:
        response = client.post(
            "/api/v1/blackout/guess",
            json={"challenge_id": challenge_id, "guess": bad},
        )

        assert response.status_code == 400


def test_only_todays_challenge_is_playable(client, article, db_session):
    """Accepting any challenge id would let anyone read back every past
    article by walking the ids."""
    challenge_id = client.get("/api/v1/blackout/today").json()["challenge_id"]

    response = client.post(
        "/api/v1/blackout/guess",
        json={"challenge_id": challenge_id + 999, "guess": "napoleon"},
    )

    assert response.status_code == 404

    reveal = client.post(
        "/api/v1/blackout/reveal",
        json={"challenge_id": challenge_id + 999},
    )

    assert reveal.status_code == 404


def test_reveal_returns_the_whole_article_and_the_source(client, article):
    challenge_id = client.get("/api/v1/blackout/today").json()["challenge_id"]

    response = client.post(
        "/api/v1/blackout/reveal",
        json={"challenge_id": challenge_id},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["title"] == "Napoleon"
    assert data["source_url"] == "https://en.wikipedia.org/wiki/Napoleon"
    assert all(token["kind"] == "fixed" for token in data["body_tokens"])

    rebuilt = "".join(token["text"] for token in data["body_tokens"])

    assert rebuilt == LEAD


def test_revealed_tokens_line_up_with_the_redacted_ones(client, article):
    """The client swaps tokens in place, so the two lists must have the
    same positions."""
    redacted = client.get("/api/v1/blackout/today").json()

    challenge_id = redacted["challenge_id"]

    revealed = client.post(
        "/api/v1/blackout/reveal",
        json={"challenge_id": challenge_id},
    ).json()

    assert len(revealed["body_tokens"]) == len(redacted["body_tokens"])
    assert len(revealed["title_tokens"]) == len(redacted["title_tokens"])


def test_empty_pool_returns_a_clear_error(client):
    response = client.get("/api/v1/blackout/today")

    assert response.status_code == 503
    assert response.json()["detail"] == "No articles available yet"


def test_the_same_article_is_served_all_day(client, article, db_session):
    first = client.get("/api/v1/blackout/today").json()
    second = client.get("/api/v1/blackout/today").json()

    assert first["challenge_id"] == second["challenge_id"]
    assert db_session.query(BlackoutChallenge).count() == 1


def test_tokenizing_is_lossless():
    text = "It's a 19th-century bridge, built in 1887 (roughly)."

    assert "".join(tokenize(text)) == text
    assert len(redact(text)) == len(tokenize(text))
