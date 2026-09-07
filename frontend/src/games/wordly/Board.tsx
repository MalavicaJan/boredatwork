import type { LetterResult, WordlyGuessResult } from "./wordly";

export const MAX_ATTEMPTS = 6;
export const WORD_LENGTH = 5;

/* Explicit rows. As one flat string in a wrapping flex container the
   keyboard broke wherever the container ran out of width, which put A
   at the end of the top row and Z X C at the end of the second. */
const KEY_ROWS = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"];

type BoardProps = {
  guesses: WordlyGuessResult[];
  currentGuess: string;
};

/** Shared by the daily challenge and practice mode so the two can't
 *  drift apart. */
export function WordlyBoard({ guesses, currentGuess }: BoardProps) {
  return (
    <div className="wordly-board">
      {Array.from({ length: MAX_ATTEMPTS }).map((_, rowIndex) => {
        const submitted = guesses[rowIndex];

        return Array.from({ length: WORD_LENGTH }).map((__, columnIndex) => {
          const letter = submitted
            ? submitted.guess[columnIndex]
            : rowIndex === guesses.length
              ? currentGuess[columnIndex]
              : "";

          const result: LetterResult | undefined =
            submitted?.result[columnIndex];

          return (
            <div
              className={`wordly-tile ${
                result ? `wordly-tile-${result}` : ""
              }`}
              key={`${rowIndex}-${columnIndex}`}
            >
              {letter?.toUpperCase()}
            </div>
          );
        });
      })}
    </div>
  );
}

/** Best result seen for each letter so far. A letter that was ever
 *  "correct" stays green even if a later guess puts it in the wrong
 *  place, which is what players expect. */
export function letterStates(guesses: WordlyGuessResult[]) {
  const rank: Record<LetterResult, number> = {
    absent: 0,
    present: 1,
    correct: 2,
  };

  const states: Record<string, LetterResult> = {};

  for (const played of guesses) {
    played.guess.split("").forEach((letter, index) => {
      const result = played.result[index];

      if (!result) return;

      const key = letter.toUpperCase();
      const current = states[key];

      if (!current || rank[result] > rank[current]) {
        states[key] = result;
      }
    });
  }

  return states;
}

type KeyboardProps = {
  disabled: boolean;
  states?: Record<string, LetterResult>;
  onLetter: (letter: string) => void;
  onBackspace: () => void;
  onEnter: () => void;
};

export function WordlyKeyboard({
  disabled,
  states = {},
  onLetter,
  onBackspace,
  onEnter,
}: KeyboardProps) {
  return (
    <div className="wordly-keyboard">
      {KEY_ROWS.map((row, rowIndex) => (
        <div className="wordly-keyboard-row" key={row}>
          {/* ENTER and backspace bracket the bottom row, as they do on
              every keyboard players will have used before. */}
          {rowIndex === 2 && (
            <button
              className="keyboard-wide"
              onClick={onEnter}
              disabled={disabled}
            >
              ENTER
            </button>
          )}

          {row.split("").map((letter) => {
            const state = states[letter];

            return (
              <button
                key={letter}
                className={state ? `keyboard-${state}` : ""}
                onClick={() => onLetter(letter)}
                disabled={disabled}
              >
                {letter}
              </button>
            );
          })}

          {rowIndex === 2 && (
            <button
              className="keyboard-wide"
              onClick={onBackspace}
              disabled={disabled}
            >
              ←
            </button>
          )}
        </div>
      ))}
    </div>
  );
}
