import { useCallback, useEffect, useRef, useState } from "react";
import GamePage from "../../components/GamePage";
import "./Sudoku.css";
import {
  CELLS,
  EMPTY,
  SIZE,
  boxOf,
  columnOf,
  formatTime,
  remainingCells,
  replaceCell,
  rowOf,
} from "./board";
import {
  DIFFICULTIES,
  checkGrid,
  getHint,
  getNewPuzzle,
  getPuzzleById,
} from "./sudoku";
import type { Difficulty, SudokuPuzzle } from "./sudoku";

// The API stores nothing about a player's run, so the run lives here.
const STORAGE_KEY = "sudoku:run";

type SavedRun = {
  puzzleId: number;
  grid: string;
  seconds: number;
};

function loadSavedRun(): SavedRun | null {
  try {
    const saved = window.localStorage.getItem(STORAGE_KEY);

    if (!saved) return null;

    const run = JSON.parse(saved) as SavedRun;

    if (typeof run.puzzleId !== "number") return null;
    if (typeof run.grid !== "string" || run.grid.length !== CELLS) return null;

    return run;
  } catch {
    return null;
  }
}

function saveRun(run: SavedRun) {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(run));
  } catch {
    // Private browsing, quota, whatever. Losing the save is survivable.
  }
}

function clearSavedRun() {
  try {
    window.localStorage.removeItem(STORAGE_KEY);
  } catch {
    // As above.
  }
}

export default function Sudoku() {
  const [difficulty, setDifficulty] = useState<Difficulty>("easy");
  const [puzzle, setPuzzle] = useState<SudokuPuzzle | null>(null);
  const [grid, setGrid] = useState("");
  const [selected, setSelected] = useState<number | null>(null);
  const [incorrect, setIncorrect] = useState<Set<number>>(new Set());
  const [solved, setSolved] = useState(false);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [seconds, setSeconds] = useState(0);
  const [message, setMessage] = useState("");

  const secondsRef = useRef(0);
  // Grid that was last auto-verified, so filling the final cell only
  // triggers one request.
  const verifiedRef = useRef("");

  const startRun = useCallback(
    (next: SudokuPuzzle, startingGrid?: string, startingSeconds = 0) => {
      setPuzzle(next);
      setDifficulty(next.difficulty);
      setGrid(startingGrid ?? next.puzzle);
      setSelected(null);
      setIncorrect(new Set());
      setSolved(false);
      setMessage("");
      setSeconds(startingSeconds);
      secondsRef.current = startingSeconds;
      verifiedRef.current = "";
    },
    [],
  );

  const loadNewPuzzle = useCallback(
    async (nextDifficulty: Difficulty, excludeId?: number) => {
      setBusy(true);
      setMessage("");

      try {
        const next = await getNewPuzzle(nextDifficulty, excludeId);

        clearSavedRun();
        startRun(next);
      } catch (error) {
        setMessage(
          error instanceof Error ? error.message : "Couldn't load a puzzle.",
        );
      } finally {
        setBusy(false);
        setLoading(false);
      }
    },
    [startRun],
  );

  // Resume the saved run if there is one, otherwise deal a fresh puzzle.
  useEffect(() => {
    const saved = loadSavedRun();

    if (!saved) {
      loadNewPuzzle("easy");
      return;
    }

    getPuzzleById(saved.puzzleId)
      .then((restored) => {
        startRun(restored, saved.grid, saved.seconds);
        setLoading(false);
      })
      .catch(() => loadNewPuzzle("easy"));
  }, [loadNewPuzzle, startRun]);

  useEffect(() => {
    if (!puzzle || solved || !grid) return;

    saveRun({ puzzleId: puzzle.id, grid, seconds });
  }, [puzzle, grid, seconds, solved]);

  useEffect(() => {
    if (!puzzle || solved) return;

    const timer = window.setInterval(() => {
      secondsRef.current += 1;
      setSeconds(secondsRef.current);
    }, 1000);

    return () => window.clearInterval(timer);
  }, [puzzle, solved]);

  // Filling the last cell is the natural moment to find out. Until then
  // the board says nothing: no colours, no warnings, no scanning done
  // on the player's behalf.
  useEffect(() => {
    if (!puzzle || solved || !grid) return;
    if (remainingCells(grid) > 0) return;
    if (verifiedRef.current === grid) return;

    verifiedRef.current = grid;

    let cancelled = false;

    checkGrid(puzzle.id, grid)
      .then((result) => {
        if (cancelled) return;

        if (result.solved) {
          setSolved(true);
          clearSavedRun();
          setMessage(`Solved in ${formatTime(secondsRef.current)}.`);
          return;
        }

        setMessage("Grid's full, but something's wrong somewhere.");
      })
      .catch(() => {
        if (!cancelled) verifiedRef.current = "";
      });

    return () => {
      cancelled = true;
    };
  }, [puzzle, grid, solved]);

  const isGiven = useCallback(
    (index: number) => Boolean(puzzle) && puzzle!.puzzle[index] !== EMPTY,
    [puzzle],
  );

  const setCell = useCallback(
    (index: number, value: string) => {
      if (!puzzle || solved || isGiven(index)) return;

      setGrid((current) => replaceCell(current, index, value));
      setMessage("");

      setIncorrect((current) => {
        if (!current.has(index)) return current;

        const next = new Set(current);
        next.delete(index);
        return next;
      });
    },
    [puzzle, solved, isGiven],
  );

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (selected === null) return;

      if (event.key >= "1" && event.key <= "9") {
        setCell(selected, event.key);
        return;
      }

      if (["Backspace", "Delete", "0"].includes(event.key)) {
        setCell(selected, EMPTY);
        return;
      }

      const moves: Record<string, number> = {
        ArrowUp: -SIZE,
        ArrowDown: SIZE,
        ArrowLeft: -1,
        ArrowRight: 1,
      };

      const move = moves[event.key];

      if (move === undefined) return;

      event.preventDefault();

      const target = selected + move;

      if (target < 0 || target >= CELLS) return;

      // Don't wrap around the edges on horizontal moves.
      if (Math.abs(move) === 1 && rowOf(target) !== rowOf(selected)) return;

      setSelected(target);
    }

    window.addEventListener("keydown", handleKeyDown);

    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [selected, setCell]);

  async function handleReveal() {
    if (!puzzle || busy || solved) return;

    setBusy(true);
    setMessage("");

    try {
      const hint = await getHint(puzzle.id, grid, selected);

      setGrid((current) => replaceCell(current, hint.index, hint.value));
      setSelected(hint.index);

      setIncorrect((current) => {
        const next = new Set(current);
        next.delete(hint.index);
        return next;
      });
    } catch (error) {
      setMessage(
        error instanceof Error ? error.message : "No hint available.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function handleShowMistakes() {
    if (!puzzle || busy || solved) return;

    setBusy(true);
    setMessage("");

    try {
      const result = await checkGrid(puzzle.id, grid);

      setIncorrect(new Set(result.incorrect_cells));

      if (result.solved) {
        setSolved(true);
        clearSavedRun();
        setMessage(`Solved in ${formatTime(secondsRef.current)}.`);
        return;
      }

      if (!result.incorrect_cells.length) {
        setMessage("Nothing wrong so far.");
        return;
      }

      setMessage(
        result.incorrect_cells.length === 1
          ? "One cell is wrong."
          : `${result.incorrect_cells.length} cells are wrong.`,
      );
    } catch (error) {
      setMessage(
        error instanceof Error ? error.message : "Couldn't check the grid.",
      );
    } finally {
      setBusy(false);
    }
  }

  const left = grid ? remainingCells(grid) : 0;

  return (
    <GamePage
      tone="tone-sudoku"
      eyebrow="PLAY ANYTIME"
      title="Sudoku"
      intro="Fill every row, column and box with 1 to 9. Play as many as you like — nothing is recorded."
    >
      <div className="sudoku-difficulties">
        {DIFFICULTIES.map((level) => (
          <button
            key={level}
            className={`sudoku-difficulty ${
              level === difficulty ? "selected" : ""
            }`}
            disabled={busy}
            onClick={() => {
              setDifficulty(level);
              loadNewPuzzle(level);
            }}
          >
            {level}
          </button>
        ))}
      </div>

      {loading && <p className="game-message">Dealing a puzzle...</p>}

      {!loading && puzzle && (
        <>
          <div className="game-status sudoku-status">
            <span>{formatTime(seconds)}</span>
            <span>{solved ? "solved" : `${left} left`}</span>
          </div>

          <div className="sudoku-board" role="grid">
            {Array.from({ length: CELLS }, (_, index) => {
              const value = grid[index] ?? EMPTY;
              const given = isGiven(index);

              const classes = [
                "sudoku-cell",
                given ? "given" : "",
                selected === index ? "selected" : "",
                incorrect.has(index) ? "incorrect" : "",
                columnOf(index) % 3 === 2 && columnOf(index) !== SIZE - 1
                  ? "box-right"
                  : "",
                rowOf(index) % 3 === 2 && rowOf(index) !== SIZE - 1
                  ? "box-bottom"
                  : "",
                selected !== null &&
                (rowOf(index) === rowOf(selected) ||
                  columnOf(index) === columnOf(selected) ||
                  boxOf(index) === boxOf(selected))
                  ? "peer"
                  : "",
              ];

              return (
                <button
                  key={index}
                  className={classes.filter(Boolean).join(" ")}
                  disabled={solved}
                  onClick={() => setSelected(index)}
                >
                  {value === EMPTY ? "" : value}
                </button>
              );
            })}
          </div>

          <div className="sudoku-pad">
            {"123456789".split("").map((digit) => (
              <button
                key={digit}
                className="sudoku-pad-key"
                disabled={selected === null || solved}
                onClick={() => selected !== null && setCell(selected, digit)}
              >
                {digit}
              </button>
            ))}

            <button
              className="sudoku-pad-key wide"
              disabled={selected === null || solved}
              onClick={() => selected !== null && setCell(selected, EMPTY)}
            >
              Clear
            </button>
          </div>

          <div className="game-actions">
            <button
              className="game-button"
              disabled={busy || solved}
              onClick={handleReveal}
            >
              Reveal a cell
            </button>

            <button
              className="game-button secondary"
              disabled={busy || solved}
              onClick={handleShowMistakes}
            >
              Show mistakes
            </button>

            <button
              className="game-button secondary"
              disabled={busy}
              onClick={() => loadNewPuzzle(difficulty, puzzle.id)}
            >
              New puzzle
            </button>
          </div>

          <p className="game-note">
            {selected === null
              ? "Reveal fills a random cell. Select one first to choose it."
              : "Reveal fills the selected cell."}
          </p>
        </>
      )}

      {message && <p className="game-message">{message}</p>}
    </GamePage>
  );
}
