import { useCallback, useEffect, useRef, useState } from "react";
import GamePage from "../../components/GamePage";
import "./Blackout.css";
import {
  getBlackoutToday,
  revealBlackout,
  submitBlackoutGuess,
  type BlackoutToken,
} from "./blackout";

type GuessLogEntry = {
  guess: string;
  count: number;
};

/** Replaces hidden tokens with the words the player has uncovered. */
function applyHits(
  tokens: BlackoutToken[],
  hits: { index: number; text: string }[],
): BlackoutToken[] {
  if (!hits.length) return tokens;

  const next = [...tokens];

  for (const hit of hits) {
    next[hit.index] = { kind: "fixed", text: hit.text, length: null };
  }

  return next;
}

function countHidden(tokens: BlackoutToken[]) {
  return tokens.filter((token) => token.kind === "word").length;
}

function Tokens({
  tokens,
  highlight,
}: {
  tokens: BlackoutToken[];
  highlight: string | null;
}) {
  return (
    <>
      {tokens.map((token, index) => {
        if (token.kind === "fixed") {
          const isHit =
            highlight !== null &&
            token.text !== null &&
            token.text.toLowerCase() === highlight;

          return (
            <span
              key={index}
              className={isHit ? "blackout-word hit" : "blackout-word"}
            >
              {token.text}
            </span>
          );
        }

        return (
          <span
            key={index}
            className="blackout-redacted"
            style={{ width: `${(token.length ?? 4) * 0.62}em` }}
            aria-label="hidden word"
          />
        );
      })}
    </>
  );
}

export default function Blackout() {
  const [challengeId, setChallengeId] = useState<number | null>(null);
  const [challengeDate, setChallengeDate] = useState("");
  const [titleTokens, setTitleTokens] = useState<BlackoutToken[]>([]);
  const [bodyTokens, setBodyTokens] = useState<BlackoutToken[]>([]);
  const [titleWords, setTitleWords] = useState(0);
  const [guess, setGuess] = useState("");
  const [log, setLog] = useState<GuessLogEntry[]>([]);
  const [highlight, setHighlight] = useState<string | null>(null);
  const [solved, setSolved] = useState(false);
  const [gaveUp, setGaveUp] = useState(false);
  const [sourceUrl, setSourceUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const inFlight = useRef(false);

  useEffect(() => {
    getBlackoutToday()
      .then((state) => {
        setChallengeId(state.challenge_id);
        setChallengeDate(state.challenge_date);
        setTitleTokens(state.title_tokens);
        setBodyTokens(state.body_tokens);
        setTitleWords(state.title_word_count);
      })
      .catch((err) =>
        setError(
          err instanceof Error ? err.message : "Couldn't load today's game.",
        ),
      )
      .finally(() => setLoading(false));
  }, []);

  const finish = useCallback(async (id: number, gaveUpNow: boolean) => {
    try {
      const revealed = await revealBlackout(id);

      setTitleTokens(revealed.title_tokens);
      setBodyTokens(revealed.body_tokens);
      setSourceUrl(revealed.source_url);
      setGaveUp(gaveUpNow);
    } catch {
      setError("Couldn't load the full article.");
    }
  }, []);

  async function handleGuess() {
    if (challengeId === null || solved || gaveUp || inFlight.current) return;

    const word = guess.trim().toLowerCase();

    if (!word) return;

    if (log.some((entry) => entry.guess === word)) {
      setError(`You already tried "${word}".`);
      setGuess("");
      return;
    }

    inFlight.current = true;
    setSubmitting(true);
    setError("");

    try {
      const result = await submitBlackoutGuess(challengeId, word);

      const nextTitle = applyHits(titleTokens, result.title_hits);

      setTitleTokens(nextTitle);
      setBodyTokens((current) => applyHits(current, result.body_hits));
      setLog((current) => [{ guess: word, count: result.count }, ...current]);
      setHighlight(word);
      setGuess("");

      // The client knows which tokens make up the title, so it can tell
      // the puzzle is solved without ever being told the answer.
      if (titleWords > 0 && countHidden(nextTitle) === 0) {
        setSolved(true);
        await finish(challengeId, false);
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Couldn't submit your guess.",
      );
    } finally {
      inFlight.current = false;
      setSubmitting(false);
    }
  }

  const finished = solved || gaveUp;
  const hiddenLeft = countHidden(bodyTokens) + countHidden(titleTokens);

  return (
    <GamePage
      tone="tone-wikiguessr"
      eyebrow="TODAY'S GAME"
      title="WikiGuessr"
      meta={challengeDate}
      intro="Every word is hidden. Guess words to uncover them and work out what the article is about."
      wide
    >
      {loading && <p className="game-message">Loading...</p>}

        {/* Outside the block below: when loading fails there is no
            challenge to render, and the error is all the player gets. */}
        {!loading && error && challengeId === null && (
        <div className="game-panel">
          <strong>{error}</strong>
        </div>
        )}

        {!loading && challengeId !== null && (
          <>
            <div className="blackout-controls">
              <input
                className="blackout-input"
                value={guess}
                placeholder="Guess a word"
                autoFocus
                disabled={finished || submitting}
                onChange={(event) => setGuess(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter") handleGuess();
                }}
              />

              <button
                className="game-button"
                disabled={finished || submitting || !guess.trim()}
                onClick={handleGuess}
              >
                Guess
              </button>

              <button
                className="game-button secondary"
                disabled={finished}
                onClick={() => finish(challengeId, true)}
              >
                Give up
              </button>
            </div>

            <div className="game-status blackout-status">
              <span>{log.length} guesses</span>
              <span>{hiddenLeft} words hidden</span>
            </div>

            {error && <p className="game-message">{error}</p>}

            {finished && (
              <div
                className={`game-panel blackout-result ${solved ? "won" : ""}`}
              >
                <strong>
                  {solved
                    ? `Got it in ${log.length} guesses.`
                    : "Article revealed."}
                </strong>
              </div>
            )}

            <article className="blackout-article">
              <h2 className="blackout-title">
                <Tokens tokens={titleTokens} highlight={highlight} />
              </h2>

              <p className="blackout-body">
                <Tokens tokens={bodyTokens} highlight={highlight} />
              </p>
            </article>

            <p className="blackout-attribution">
              Text from Wikipedia, available under{" "}
              <a
                href="https://creativecommons.org/licenses/by-sa/4.0/"
                target="_blank"
                rel="noreferrer"
              >
                CC BY-SA 4.0
              </a>
              {sourceUrl && (
                <>
                  {" — "}
                  <a href={sourceUrl} target="_blank" rel="noreferrer">
                    read the full article
                  </a>
                </>
              )}
              .
            </p>

            {log.length > 0 && (
              <div className="blackout-log">
                {log.map((entry) => (
                  <span
                    key={entry.guess}
                    className={`blackout-log-entry ${
                      entry.count > 0 ? "found" : ""
                    }`}
                  >
                    {entry.guess}
                    <em>{entry.count}</em>
                  </span>
                ))}
              </div>
            )}
        </>
      )}
    </GamePage>
  );
}
