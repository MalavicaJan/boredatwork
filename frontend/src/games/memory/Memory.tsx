import { useCallback, useEffect, useRef, useState } from "react";
import GamePage from "../../components/GamePage";
import "./Memory.css";
import {
  COLUMNS,
  DIFFICULTIES,
  PAIRS,
  buildDeck,
  formatTime,
} from "./deck";
import type { Difficulty, MemoryCard } from "./deck";

// How long a mismatched pair stays visible before flipping back.
const MISMATCH_DELAY = 800;

export default function Memory() {
  const [difficulty, setDifficulty] = useState<Difficulty>("easy");
  const [cards, setCards] = useState<MemoryCard[]>([]);
  const [flipped, setFlipped] = useState<number[]>([]);
  const [matched, setMatched] = useState<Set<string>>(new Set());
  const [moves, setMoves] = useState(0);
  const [seconds, setSeconds] = useState(0);
  const [started, setStarted] = useState(false);
  const [locked, setLocked] = useState(false);

  const timeoutRef = useRef<number | undefined>(undefined);

  const startGame = useCallback((level: Difficulty) => {
    window.clearTimeout(timeoutRef.current);

    setDifficulty(level);
    setCards(buildDeck(level));
    setFlipped([]);
    setMatched(new Set());
    setMoves(0);
    setSeconds(0);
    setStarted(false);
    setLocked(false);
  }, []);

  useEffect(() => {
    startGame("easy");

    return () => window.clearTimeout(timeoutRef.current);
  }, [startGame]);

  const solved =
    cards.length > 0 && matched.size === PAIRS[difficulty];

  // The clock starts on the first flip, not on page load: staring at a
  // fresh board shouldn't cost you anything.
  useEffect(() => {
    if (!started || solved) return;

    const timer = window.setInterval(() => {
      setSeconds((current) => current + 1);
    }, 1000);

    return () => window.clearInterval(timer);
  }, [started, solved]);

  function handleFlip(position: number) {
    if (locked || solved) return;
    if (flipped.includes(position)) return;
    if (matched.has(cards[position].symbol)) return;

    if (!started) setStarted(true);

    const next = [...flipped, position];

    setFlipped(next);

    if (next.length < 2) return;

    setMoves((current) => current + 1);

    const [first, second] = next;

    if (cards[first].symbol === cards[second].symbol) {
      setMatched((current) => new Set(current).add(cards[first].symbol));
      setFlipped([]);
      return;
    }

    // Wrong pair: hold it visible long enough to memorise, then hide.
    setLocked(true);

    timeoutRef.current = window.setTimeout(() => {
      setFlipped([]);
      setLocked(false);
    }, MISMATCH_DELAY);
  }

  return (
    <GamePage
      tone="tone-memory"
      eyebrow="PLAY ANYTIME"
      title="Memory"
      intro="Find every pair. Play as many rounds as you like — nothing is recorded."
    >
      <div className="memory-difficulties">
        {DIFFICULTIES.map((level) => (
          <button
            key={level}
            className={`memory-difficulty ${
              level === difficulty ? "selected" : ""
            }`}
            onClick={() => startGame(level)}
          >
            {level}
          </button>
        ))}
      </div>

      <div className="game-status memory-status">
        <span>{formatTime(seconds)}</span>
        <span>
          {matched.size} / {PAIRS[difficulty]} pairs
        </span>
        <span>
          {moves} {moves === 1 ? "move" : "moves"}
        </span>
      </div>

      <div
        className="memory-board"
        style={{
          gridTemplateColumns: `repeat(${COLUMNS[difficulty]}, 1fr)`,
        }}
      >
        {cards.map((card, position) => {
          const isMatched = matched.has(card.symbol);
          const isFaceUp = isMatched || flipped.includes(position);

          return (
            <button
              key={card.id}
              className={`memory-card ${isFaceUp ? "face-up" : ""} ${
                isMatched ? "matched" : ""
              }`}
              onClick={() => handleFlip(position)}
              aria-label={isFaceUp ? card.symbol : "Face-down card"}
            >
              {isFaceUp ? card.symbol : ""}
            </button>
          );
        })}
      </div>

      {solved && (
        <div className="game-panel memory-result">
          <strong>
            Cleared in {formatTime(seconds)}, {moves} moves.
          </strong>

          <button
            className="game-button"
            onClick={() => startGame(difficulty)}
          >
            Play again
          </button>
        </div>
      )}
    </GamePage>
  );
}
