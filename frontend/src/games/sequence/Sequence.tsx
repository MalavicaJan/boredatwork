import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";

import GamePage from "../../components/GamePage";
import "./Sequence.css";
import {
  SequenceConflictError,
  getSequenceState,
  submitSequenceAnswer,
} from "./sequence";

// Longer runs get a little more time on screen.
function displayDuration(digits: string) {
  return 1000 + 250 * digits.length;
}

export default function Sequence() {
  const [loading, setLoading] = useState(true);
  const [round, setRound] = useState(1);
  const [totalRounds, setTotalRounds] = useState(6);
  const [digits, setDigits] = useState("");
  const [showing, setShowing] = useState(false);
  const [answer, setAnswer] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [finished, setFinished] = useState(false);
  const [score, setScore] = useState<number | null>(null);
  const [playedEarlier, setPlayedEarlier] = useState(false);
  const [message, setMessage] = useState("");

  const timerRef = useRef<number | undefined>(undefined);

  const startRound = useCallback((nextDigits: string) => {
    setDigits(nextDigits);
    setAnswer("");
    setShowing(true);

    window.clearTimeout(timerRef.current);

    timerRef.current = window.setTimeout(() => {
      setShowing(false);
    }, displayDuration(nextDigits));
  }, []);

  const loadState = useCallback(async () => {
    try {
      const state = await getSequenceState();

      setRound(state.round);
      setTotalRounds(state.total_rounds);

      if (state.completed) {
        setFinished(true);
        setPlayedEarlier(true);
        setScore(state.score);
        return;
      }

      if (state.digits) {
        startRound(state.digits);
      }
    } catch {
      setMessage("Couldn't load today's Sequence. Try reloading.");
    } finally {
      setLoading(false);
    }
  }, [startRound]);

  useEffect(() => {
    loadState();

    return () => window.clearTimeout(timerRef.current);
  }, [loadState]);

  async function handleSubmit() {
    if (submitting || finished || showing) return;

    if (answer.length !== digits.length) {
      setMessage(`Enter all ${digits.length} digits.`);
      return;
    }

    setMessage("");
    setSubmitting(true);

    try {
      const result = await submitSequenceAnswer(round, answer);

      if (result.game_over) {
        setFinished(true);
        setScore(result.score);
        return;
      }

      if (result.next_round && result.next_digits) {
        setRound(result.next_round);
        startRound(result.next_digits);
      }
    } catch (error) {
      if (error instanceof SequenceConflictError) {
        // Server state moved on (another tab, a stale page). Resync.
        setMessage("Picking up where you left off.");
        await loadState();
        return;
      }

      setMessage(
        error instanceof Error
          ? error.message
          : "Couldn't submit your answer.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <GamePage
      tone="tone-sequence"
      eyebrow="TODAY'S GAME"
      title="Sequence"
      meta={finished ? undefined : `Round ${round} of ${totalRounds}`}
      intro={
        <>
          Remember the digits and type them back in the same order. Each
          round is longer, and one mistake ends the run.
        </>
      }
    >
      {loading && <p className="game-message">Loading...</p>}

      {!loading && !finished && (
        <>
          <p className="sequence-round">
            {showing ? "Memorise" : "Type it back"}
          </p>

          <div className="sequence-stage">
            {showing ? (
              <div className="sequence-display">{digits}</div>
            ) : (
              <div className="sequence-form">
                <input
                  className="sequence-input"
                  type="text"
                  inputMode="numeric"
                  autoComplete="off"
                  value={answer}
                  maxLength={digits.length}
                  autoFocus
                  disabled={submitting}
                  aria-label={`Enter ${digits.length} digits`}
                  onChange={(event) =>
                    setAnswer(
                      event.target.value
                        .replace(/\D/g, "")
                        .slice(0, digits.length),
                    )
                  }
                  onKeyDown={(event) => {
                    if (event.key === "Enter") handleSubmit();
                  }}
                />

                <button
                  className="game-button"
                  onClick={handleSubmit}
                  disabled={submitting || answer.length !== digits.length}
                >
                  {submitting ? "Checking..." : "Submit"}
                </button>
              </div>
            )}
          </div>

          {/* Progress you can read at a glance, rather than as a number. */}
          <div className="sequence-progress">
            {Array.from({ length: totalRounds }, (_, index) => (
              <span
                key={index}
                className={`sequence-pip ${
                  index + 1 < round
                    ? "cleared"
                    : index + 1 === round
                      ? "current"
                      : ""
                }`}
              />
            ))}
          </div>
        </>
      )}

      {finished && (
        <div className="game-panel">
          <h2>{playedEarlier ? "Already played today" : "Run over"}</h2>

          <p className="sequence-score">
            {score} of {totalRounds}
          </p>

          <p>Come back tomorrow for a new one.</p>

          <div className="game-actions">
            <Link className="game-button" to="/">
              Pick another game
            </Link>
          </div>
        </div>
      )}

      {message && <p className="game-message">{message}</p>}
    </GamePage>
  );
}
