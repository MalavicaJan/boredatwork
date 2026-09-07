import { API_BASE_URL } from "../../api/config";

export type Difficulty = "easy" | "medium" | "hard" | "expert";

export const DIFFICULTIES: Difficulty[] = [
  "easy",
  "medium",
  "hard",
  "expert",
];

export type SudokuPuzzle = {
  id: number;
  difficulty: Difficulty;
  // 81 characters, "0" for an empty cell. Never contains the solution.
  puzzle: string;
  givens: number;
};

export type SudokuCheck = {
  complete: boolean;
  solved: boolean;
  incorrect_cells: number[];
};

export type SudokuHint = {
  index: number;
  value: string;
  remaining: number;
};

async function readError(response: Response, fallback: string) {
  try {
    const data = await response.json();
    return typeof data.detail === "string" ? data.detail : fallback;
  } catch {
    return fallback;
  }
}

export async function getNewPuzzle(
  difficulty: Difficulty,
  excludeId?: number,
): Promise<SudokuPuzzle> {
  const parameters = new URLSearchParams({ difficulty });

  if (excludeId) {
    parameters.set("exclude", String(excludeId));
  }

  const response = await fetch(`${API_BASE_URL}/sudoku/new?${parameters}`);

  if (!response.ok) {
    throw new Error(await readError(response, "Couldn't load a puzzle."));
  }

  return response.json();
}

export async function getPuzzleById(id: number): Promise<SudokuPuzzle> {
  const response = await fetch(`${API_BASE_URL}/sudoku/${id}`);

  if (!response.ok) {
    throw new Error(await readError(response, "Couldn't load that puzzle."));
  }

  return response.json();
}

export async function checkGrid(
  puzzleId: number,
  grid: string,
): Promise<SudokuCheck> {
  const response = await fetch(`${API_BASE_URL}/sudoku/check`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ puzzle_id: puzzleId, grid }),
  });

  if (!response.ok) {
    throw new Error(await readError(response, "Couldn't check the grid."));
  }

  return response.json();
}

export async function getHint(
  puzzleId: number,
  grid: string,
  index?: number | null,
): Promise<SudokuHint> {
  const response = await fetch(`${API_BASE_URL}/sudoku/hint`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      puzzle_id: puzzleId,
      grid,
      index: index ?? null,
    }),
  });

  if (!response.ok) {
    throw new Error(await readError(response, "No hint available."));
  }

  return response.json();
}
