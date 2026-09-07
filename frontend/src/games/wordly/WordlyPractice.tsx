import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";

import GamePage from "../../components/GamePage";
import "./Wordly.css";
import { MAX_ATTEMPTS, WORD_LENGTH, WordlyBoard, WordlyKeyboard } from "./Board";
import {
  getPracticeWord,
  revealPracticeWord,
  submitPracticeGuess,
  type WordlyGuessResult,
} from "./wordly";

export default function WordlyPractice() {
  const [wordId, setWordId] = useState<number | null>(null);
  const [guesses, setGuesses] = useState<WordlyGuessResult[]>([]);
  const [currentGuess, setCurrentGuess] = useState("");
  const [completed, setCompleted] = useState(false);
  const [won, setWon] = useState(false);
  const [answer, setAnswer] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const inFlight = useRef(false);

  const loadWord = useCallback(async (excludeId?: number) => {
    setLoading(true);
    setError("");

    try {
      const word = await getPracticeWord(excludeId);

      setWordId(word.word_id);
      setGuesses([]);
      setCurrentGuess("");
      setCompleted(false);
      setWon(false);
      setAnswer(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't load a word.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadWord();
  }, [loadWord]);

  const handleSubmit = useCallback(async () => {
    if (completed || inFlight.current || wordId === null) return;

    if (currentGuess.length !== WORD_LENGTH) {
      setError(`Your guess needs ${WORD_LENGTH} letters.`);
      return;
    }

    inFlight.current = true;
    setSubmitting(true);
    setError("");

    try {
      const result = await submitPracticeGuess(wordId, currentGuess);

      const played = [...guesses, { guess: currentGuess, result: result.result }];

      setGuesses(played);
      setCurrentGuess("");

      if (result.correct) {
        setCompleted(true);
        setWon(true);
        return;
      }

      if (played.length >= MAX_ATTEMPTS) {
        setCompleted(true);
        setWon(false);

        // Nothing is at stake in practice, so the word is handed over
        // rather than held back.
        try {
          setAnswer(await revealPracticeWord(wordId));
        } catch {
          setError("Couldn't reveal the word.");
        }
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Couldn't submit your guess.",
      );
    } finally {
      inFlight.current = false;
      setSubmitting(false);
    }
  }, [completed, currentGuess, guesses, wordId]);

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

  const locked = completed || submitting;

  return (
    <GamePage
      tone="tone-practice"
      eyebrow="PRACTICE"
      title="Wordly"
      intro="Guess the five-letter word in six tries. As many words as you like — nothing is recorded."
    >
      <p className="wordly-countdown">
        <Link to="/wordly">Playing for real? Try today's challenge →</Link>
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
                    ? `Got it in ${guesses.length} ${
                        guesses.length === 1 ? "try" : "tries"
                      }.`
                    : "Out of guesses."}
                </strong>

                {!won && answer && (
                  <span>The word was {answer.toUpperCase()}.</span>
                )}

                <button
                  className="game-button"
                  onClick={() => loadWord(wordId ?? undefined)}
                >
                  Next word
                </button>
              </div>
            )}

            {error && <p className="game-message">{error}</p>}

            <WordlyKeyboard
              disabled={locked}
              onLetter={(letter) => {
                if (locked || currentGuess.length >= WORD_LENGTH) return;
                setError("");
                setCurrentGuess((guess) => guess + letter.toLowerCase());
              }}
              onBackspace={() => {
                if (locked) return;
                setCurrentGuess((guess) => guess.slice(0, -1));
              }}
              onEnter={handleSubmit}
            />
        </>
      )}
    </GamePage>
  );
}
