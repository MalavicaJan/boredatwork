import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";

import GamePage from "../../components/GamePage";
import "./Wordly.css";
import { MAX_ATTEMPTS, WORD_LENGTH, WordlyBoard, WordlyKeyboard } from "./Board";
import {
  getWordlyState,
  submitWordlyGuess,
  type WordlyGuessResult,
} from "./wordly";

/** The daily challenge rolls over at UTC midnight, not local midnight.
 *  Counting down to the local one was wrong by an hour or two for
 *  anyone outside UTC. */
function timeUntilNextChallenge() {
  const now = new Date();

  const nextUtcMidnight = Date.UTC(
    now.getUTCFullYear(),
    now.getUTCMonth(),
    now.getUTCDate() + 1,
  );

  return nextUtcMidnight - now.getTime();
}

function formatCountdown(milliseconds: number) {
  const totalSeconds = Math.floor(milliseconds / 1000);

  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;

  return [hours, minutes, seconds]
    .map((part) => String(part).padStart(2, "0"))
    .join(":");
}

function Wordly() {
  const [guesses, setGuesses] = useState<WordlyGuessResult[]>([]);
  const [currentGuess, setCurrentGuess] = useState("");
  const [challengeDate, setChallengeDate] = useState("");
  const [timeRemaining, setTimeRemaining] = useState("");
  const [completed, setCompleted] = useState(false);
  const [won, setWon] = useState(false);
  const [answer, setAnswer] = useState<string | null>(null);
  const [signedIn, setSignedIn] = useState(false);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  // Guards against a second request while one is in flight. State
  // updates are async, so the ref is what actually blocks a double
  // Enter press.
  const inFlight = useRef(false);

  useEffect(() => {
    async function loadGame() {
      try {
        const state = await getWordlyState();

        setGuesses(state.guesses);
        setChallengeDate(state.challenge_date);
        setCompleted(state.completed);
        setWon(state.won);
        setAnswer(state.answer);
        // Only a logged-in player has server-side state to report.
        setSignedIn(state.attempts_used > 0 || state.completed);
      } catch {
        setError("Couldn't load today's Wordly.");
      } finally {
        setLoading(false);
      }
    }

    loadGame();
  }, []);

  useEffect(() => {
    function updateCountdown() {
      const remaining = timeUntilNextChallenge();

      if (remaining <= 0) {
        window.location.reload();
        return;
      }

      setTimeRemaining(formatCountdown(remaining));
    }

    updateCountdown();

    const interval = window.setInterval(updateCountdown, 1000);

    return () => window.clearInterval(interval);
  }, []);

  const handleSubmit = useCallback(async () => {
    if (completed || inFlight.current) return;

    if (currentGuess.length !== WORD_LENGTH) {
      setError(`Your guess needs ${WORD_LENGTH} letters.`);
      return;
    }

    inFlight.current = true;
    setSubmitting(true);
    setError("");

    try {
      const result = await submitWordlyGuess(currentGuess);

      const submitted: WordlyGuessResult = {
        guess: currentGuess,
        result: result.result,
      };

      const played = [...guesses, submitted];

      setGuesses(played);
      setCurrentGuess("");

      if (result.attempts_used !== null) {
        setSignedIn(true);
      }

      if (result.correct) {
        setCompleted(true);
        setWon(true);
        return;
      }

      // The server ends the game for signed-in players. For anonymous
      // ones it keeps no count, so the board enforces the six rows.
      const outOfGuesses =
        result.game_over || played.length >= MAX_ATTEMPTS;

      if (outOfGuesses) {
        setCompleted(true);
        setWon(false);
        setAnswer(result.answer);
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Couldn't submit your guess.",
      );
    } finally {
      inFlight.current = false;
      setSubmitting(false);
    }
  }, [completed, currentGuess, guesses]);

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (loading || completed || submitting) return;

      const key = event.key.toUpperCase();

      if (key === "ENTER") {
        handleSubmit();
        return;
      }

      if (key === "BACKSPACE") {
        setCurrentGuess((guess) => guess.slice(0, -1));
        return;
      }

      if (/^[A-Z]$/.test(key) && currentGuess.length < WORD_LENGTH) {
        setCurrentGuess((guess) => guess + key.toLowerCase());
      }
    }

    window.addEventListener("keydown", handleKeyDown);

    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [currentGuess, completed, loading, submitting, handleSubmit]);

  function handleLetter(letter: string) {
    if (completed || submitting || currentGuess.length >= WORD_LENGTH) return;

    setError("");
    setCurrentGuess((guess) => guess + letter.toLowerCase());
  }

  function handleBackspace() {
    if (completed || submitting) return;

    setCurrentGuess((guess) => guess.slice(0, -1));
  }

  const locked = completed || submitting;

  return (
    <GamePage
      tone="tone-wordly"
      eyebrow="TODAY'S GAME"
      title="Wordly"
      meta={challengeDate}
      intro="Guess the five-letter word in six tries."
    >
      <p className="wordly-countdown">
        {completed && <strong>Today's Wordly is complete.</strong>}
        <span>Next challenge in {timeRemaining}</span>
      </p>

        {loading ? (
          <p className="game-message">Loading...</p>
      ) : (
        <>
            <WordlyBoard guesses={guesses} currentGuess={currentGuess} />

            {completed && (
              <div className="game-panel wordly-result">
                <strong>
                  {won
                    ? `Nice. ${guesses.length} ${
                        guesses.length === 1 ? "try" : "tries"
                      }.`
                    : "Better luck tomorrow."}
                </strong>

                {!won && answer && (
                  <span>The answer was {answer.toUpperCase()}.</span>
                )}

                {!won && !answer && !signedIn && (
                  <span>
                    <Link to="/login">Sign in</Link> to see the answer and
                    keep a streak.
                  </span>
                )}
              </div>
            )}

            {error && <p className="game-message">{error}</p>}

            <WordlyKeyboard
              disabled={locked}
              onLetter={handleLetter}
              onBackspace={handleBackspace}
              onEnter={handleSubmit}
            />
        </>
      )}
    </GamePage>
  );
}

export default Wordly;
