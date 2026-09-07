from datetime import date

from app.models.wordly import WordlyChallenge



def test_anonymous_wordly_guess(client):
    response = client.post(
        "/api/v1/wordly/guess",
        json={"guess": "music"},
    )

    assert response.status_code == 200
    data = response.json()

    assert "correct" in data
    assert "result" in data
    assert len(data["result"]) == 5

def test_logged_in_wordly_guess_is_saved(client):
    client.post(
        "/api/v1/users/",
        json={
            "username": "testuser",
            "password": "test-password",
        },
    )

    client.post(
        "/api/v1/users/login",
        json={
            "username": "testuser",
            "password": "test-password",
        },
    )

    response = client.post(
        "/api/v1/wordly/guess",
        json={"guess": "music"},
    )

    assert response.status_code == 200

    state_response = client.get("/api/v1/wordly/state")

    assert state_response.status_code == 200

    data = state_response.json()

    assert data["attempts_used"] == 1
    assert len(data["guesses"]) == 1
    assert data["guesses"][0]["guess"] == "music"

def test_logged_in_wordly_win_saves_score(client):
    client.post(
        "/api/v1/users/",
        json={
            "username": "testuser",
            "password": "test-password",
        },
    )

    client.post(
        "/api/v1/users/login",
        json={
            "username": "testuser",
            "password": "test-password",
        },
    )
    challenge = WordlyChallenge(
    challenge_date=date.today(),
    word="music",
)

    client.app.dependency_overrides
    response = client.post(
        "/api/v1/wordly/guess",
        json={"guess": "music"},
    )
    

    assert response.status_code == 200
    assert response.json()["correct"] is True

    state_response = client.get("/api/v1/wordly/state")

    assert state_response.status_code == 200

    data = state_response.json()

    assert data["completed"] is True
    assert data["won"] is True
    assert data["attempts_used"] == 1

def test_logged_in_wordly_loss_after_six_attempts(client):
    client.post(
        "/api/v1/users/",
        json={
            "username": "testuser",
            "password": "test-password",
        },
    )

    client.post(
        "/api/v1/users/login",
        json={
            "username": "testuser",
            "password": "test-password",
        },
    )

    for _ in range(6):
        response = client.post(
            "/api/v1/wordly/guess",
            json={"guess": "apple"},
        )

    assert response.status_code == 200

    data = response.json()

    assert data["correct"] is False
    assert data["game_over"] is True
    assert data["answer"] == "music"

    state_response = client.get("/api/v1/wordly/state")

    assert state_response.status_code == 200

    state = state_response.json()

    assert state["completed"] is True
    assert state["won"] is False
    assert state["attempts_used"] == 6

def test_wordly_incomplete_game_is_not_completed(client):
    client.post(
        "/api/v1/users/",
        json={
            "username": "testuser",
            "password": "test-password",
        },
    )

    client.post(
        "/api/v1/users/login",
        json={
            "username": "testuser",
            "password": "test-password",
        },
    )

    response = client.post(
        "/api/v1/wordly/guess",
        json={"guess": "apple"},
    )

    assert response.status_code == 200
    assert response.json()["game_over"] is False

    state_response = client.get("/api/v1/wordly/state")

    assert state_response.status_code == 200

    state = state_response.json()

    assert state["completed"] is False
    assert state["attempts_used"] == 1


def test_wordly_duplicate_letter_scoring(client):
    client.post(
        "/api/v1/users/",
        json={
            "username": "testuser",
            "password": "test-password",
        },
    )

    client.post(
        "/api/v1/users/login",
        json={
            "username": "testuser",
            "password": "test-password",
        },
    )

    response = client.post(
        "/api/v1/wordly/guess",
        json={"guess": "mamma"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["result"] == [
        "correct",
        "absent",
        "absent",
        "absent",
        "absent",
    ]

def test_completed_wordly_cannot_be_played_again(client):
    client.post(
        "/api/v1/users/",
        json={
            "username": "testuser",
            "password": "test-password",
        },
    )

    client.post(
        "/api/v1/users/login",
        json={
            "username": "testuser",
            "password": "test-password",
        },
    )

    first_response = client.post(
        "/api/v1/wordly/guess",
        json={"guess": "music"},
    )

    assert first_response.status_code == 200
    assert first_response.json()["correct"] is True

    second_response = client.post(
        "/api/v1/wordly/guess",
        json={"guess": "apple"},
    )

    assert second_response.status_code == 400
    assert second_response.json()["detail"] == "You have already completed today's Wordly"

def test_anonymous_wordly_state(client):
    response = client.get("/api/v1/wordly/state")

    assert response.status_code == 200

    data = response.json()

    assert data["guesses"] == []
    assert data["attempts_used"] == 0
    assert data["attempts_remaining"] == 6
    assert data["completed"] is False
    assert data["won"] is False

def test_wordly_rejects_invalid_guess_length(client):
    response = client.post(
        "/api/v1/wordly/guess",
        json={"guess": "test"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Guess must be exactly 5 letters"

# --- Regression tests for the win/loss and anonymous bugs ---

WRONG_GUESSES = ["plane", "brick", "storm", "guard", "flint"]


def login(client, username="wordler"):
    client.post(
        "/api/v1/users/",
        json={"username": username, "password": "test-password"},
    )

    assert client.post(
        "/api/v1/users/login",
        json={"username": username, "password": "test-password"},
    ).status_code == 200


def guess(client, word):
    return client.post("/api/v1/wordly/guess", json={"guess": word})


def test_winning_on_the_last_guess_counts_as_a_win(client):
    """Used to be scored as a loss: the win flag was derived from
    `score < 6`, and a sixth-guess win scores exactly 6."""
    login(client)

    for wrong in WRONG_GUESSES:
        assert guess(client, wrong).status_code == 200

    response = guess(client, "music")

    assert response.status_code == 200

    data = response.json()

    assert data["correct"] is True
    assert data["won"] is True
    assert data["game_over"] is True
    assert data["attempts_used"] == 6
    assert data["answer"] is None

    state = client.get("/api/v1/wordly/state").json()

    assert state["completed"] is True
    assert state["won"] is True


def test_losing_on_the_last_guess_is_a_loss_with_the_same_score(client):
    login(client)

    for wrong in WRONG_GUESSES:
        guess(client, wrong)

    response = guess(client, "zebra")

    assert response.status_code == 200

    data = response.json()

    assert data["won"] is False
    assert data["game_over"] is True
    assert data["attempts_used"] == 6
    assert data["answer"] == "music"

    state = client.get("/api/v1/wordly/state").json()

    assert state["won"] is False
    # Same score as the winning case above; only `won` separates them.
    assert state["completed"] is True


def test_state_still_shows_the_answer_after_a_loss(client):
    """A player who loses and reloads should still see the word."""
    login(client)

    for wrong in WRONG_GUESSES:
        guess(client, wrong)

    guess(client, "zebra")

    state = client.get("/api/v1/wordly/state").json()

    assert state["answer"] == "music"


def test_state_hides_the_answer_from_a_winner(client):
    login(client)

    guess(client, "music")

    assert client.get("/api/v1/wordly/state").json()["answer"] is None


def test_state_hides_the_answer_mid_game(client):
    login(client)

    guess(client, "plane")

    state = client.get("/api/v1/wordly/state").json()

    assert state["answer"] is None
    assert state["completed"] is False
    assert state["attempts_remaining"] == 5


def test_anonymous_guessing_never_reveals_the_answer(client):
    """Anonymous runs aren't stored, so the server can't tell a sixth
    guess from a sixtieth. Revealing on request would hand the daily
    word to anyone who asked."""
    for _ in range(12):
        response = guess(client, "zebra")

        assert response.status_code == 200

        data = response.json()

        assert data["answer"] is None
        assert data["game_over"] is False
        assert data["attempts_used"] is None
        assert data["attempts_remaining"] is None


def test_anonymous_win_ends_the_game(client):
    response = guess(client, "music")

    assert response.status_code == 200

    data = response.json()

    assert data["correct"] is True
    assert data["won"] is True
    assert data["game_over"] is True


def test_anonymous_play_stores_nothing(client, db_session):
    from app.models.game_result import GameResult
    from app.models.wordly_guess import WordlyGuess

    guess(client, "plane")
    guess(client, "music")

    assert db_session.query(WordlyGuess).count() == 0
    assert db_session.query(GameResult).count() == 0


def test_a_finished_game_cannot_be_continued(client):
    login(client)

    guess(client, "music")

    response = guess(client, "plane")

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "You have already completed today's Wordly"
    )


def test_only_one_result_row_per_player_per_day(client, db_session):
    from app.models.game_result import GameResult

    login(client)

    guess(client, "music")

    results = (
        db_session.query(GameResult)
        .filter(GameResult.game == "wordly")
        .all()
    )

    assert len(results) == 1
    assert results[0].won is True
    assert results[0].score == 1


# --- Practice mode ---

from app.models.wordly_word import PRACTICE, WordlyWord  # noqa: E402


def add_practice_word(db_session, word="crane"):
    stored = WordlyWord(word=word, pool=PRACTICE)

    db_session.add(stored)
    db_session.commit()
    db_session.refresh(stored)

    return stored


def test_practice_new_returns_a_handle_not_a_word(client, db_session):
    practice_word = add_practice_word(db_session)

    response = client.get("/api/v1/wordly/practice/new")

    assert response.status_code == 200

    data = response.json()

    assert data["word_id"] == practice_word.id
    assert data["word_length"] == 5
    assert data["max_attempts"] == 6
    assert "crane" not in response.text


def test_practice_needs_no_account_and_has_no_limit(client, db_session):
    practice_word = add_practice_word(db_session)

    for _ in range(20):
        response = client.post(
            "/api/v1/wordly/practice/guess",
            json={"word_id": practice_word.id, "guess": "plane"},
        )

        assert response.status_code == 200
        assert response.json()["correct"] is False


def test_practice_guess_scores_correctly(client, db_session):
    practice_word = add_practice_word(db_session)

    response = client.post(
        "/api/v1/wordly/practice/guess",
        json={"word_id": practice_word.id, "guess": "crane"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "correct": True,
        "result": ["correct"] * 5,
    }


def test_practice_reveal_returns_the_word(client, db_session):
    """The practice word is disposable, not a shared secret, so telling
    the player costs nothing."""
    practice_word = add_practice_word(db_session)

    response = client.post(
        "/api/v1/wordly/practice/reveal",
        json={"word_id": practice_word.id},
    )

    assert response.status_code == 200
    assert response.json()["answer"] == "crane"


def test_practice_cannot_touch_a_daily_word(client, db_session):
    """The whole point of the split: practice endpoints must not be
    usable to enumerate the daily answer pool."""
    daily_word = (
        db_session.query(WordlyWord)
        .filter(WordlyWord.word == "music")
        .one()
    )

    reveal = client.post(
        "/api/v1/wordly/practice/reveal",
        json={"word_id": daily_word.id},
    )

    assert reveal.status_code == 404

    guess = client.post(
        "/api/v1/wordly/practice/guess",
        json={"word_id": daily_word.id, "guess": "music"},
    )

    assert guess.status_code == 404


def test_practice_pool_empty_returns_a_clear_error(client):
    response = client.get("/api/v1/wordly/practice/new")

    assert response.status_code == 503
    assert response.json()["detail"] == "No practice words available yet"


def test_daily_challenge_ignores_practice_words(client, db_session):
    """Even if practice words outnumber daily ones, the daily challenge
    only ever draws from the daily pool."""
    for word in ["crane", "slate", "audio", "roast"]:
        add_practice_word(db_session, word)

    state = client.get("/api/v1/wordly/state").json()

    challenge = (
        db_session.query(WordlyChallenge)
        .filter(WordlyChallenge.id == state["challenge_id"])
        .one()
    )

    assert challenge.word == "music"


def test_practice_exclude_avoids_the_word_just_played(client, db_session):
    first = add_practice_word(db_session, "crane")
    second = add_practice_word(db_session, "slate")

    for _ in range(8):
        response = client.get(
            f"/api/v1/wordly/practice/new?exclude={first.id}"
        )

        assert response.json()["word_id"] == second.id


def test_practice_rejects_a_bad_guess_length(client, db_session):
    practice_word = add_practice_word(db_session)

    response = client.post(
        "/api/v1/wordly/practice/guess",
        json={"word_id": practice_word.id, "guess": "no"},
    )

    assert response.status_code == 400
