// Pure deck logic, kept apart from the component so it can be tested
// once there's a runner for the frontend.

export type Difficulty = "easy" | "medium" | "hard";

export const DIFFICULTIES: Difficulty[] = ["easy", "medium", "hard"];

export const PAIRS: Record<Difficulty, number> = {
  easy: 8,
  medium: 12,
  hard: 18,
};

// Columns the board is laid out in, per difficulty.
export const COLUMNS: Record<Difficulty, number> = {
  easy: 4,
  medium: 6,
  hard: 6,
};

const SYMBOLS = [
  "🌵", "🍄", "🐙", "🔑", "⚓", "🎈", "🧊", "🌙",
  "🔔", "🍋", "🪁", "🧭", "🎲", "🪴", "☂️", "🥁",
  "🛟", "🪐", "🧩", "🍉",
];

export type MemoryCard = {
  /** Position in the shuffled deck. */
  id: number;
  symbol: string;
};

export function shuffle<T>(items: T[]): T[] {
  const shuffled = [...items];

  // Fisher-Yates.
  for (let index = shuffled.length - 1; index > 0; index--) {
    const swap = Math.floor(Math.random() * (index + 1));

    [shuffled[index], shuffled[swap]] = [shuffled[swap], shuffled[index]];
  }

  return shuffled;
}

export function buildDeck(difficulty: Difficulty): MemoryCard[] {
  const pairs = PAIRS[difficulty];

  if (pairs > SYMBOLS.length) {
    throw new Error(`Not enough symbols for ${pairs} pairs`);
  }

  const chosen = shuffle(SYMBOLS).slice(0, pairs);

  return shuffle([...chosen, ...chosen]).map((symbol, id) => ({
    id,
    symbol,
  }));
}

export function formatTime(totalSeconds: number) {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;

  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}
