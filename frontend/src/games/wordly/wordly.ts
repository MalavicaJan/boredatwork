import { API_BASE_URL } from "../../api/config";

export type LetterResult = "correct" | "present" | "absent";

export type WordlyGuessResult = {
  guess: string;
  result: LetterResult[];
};

export type WordlyState = {
  challenge_id: number;
  challenge_date: string;
  guesses: WordlyGuessResult[];
  attempts_used: number;
  attempts_remaining: number;
  completed: boolean;
  won: boolean;
  // Present only once a logged-in player has finished and lost.
  answer: string | null;
};

export type WordlyGuessResponse = {
  correct: boolean;
  result: LetterResult[];
  game_over: boolean;
  won: boolean;
  // Null for anonymous players: the server keeps no count for them.
  attempts_used: number | null;
  attempts_remaining: number | null;
  answer: string | null;
};



export async function getWordlyState(): Promise<WordlyState> {
  const response = await fetch(`${API_BASE_URL}/wordly/state`, {
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error("Failed to load Wordly");
  }

  return response.json();
}

export async function submitWordlyGuess(
  guess: string,
): Promise<WordlyGuessResponse> {
  const response = await fetch(`${API_BASE_URL}/wordly/guess`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify({
      guess,
    }),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Failed to submit guess");
  }

  return data;
}

// --- Practice mode ---

export type PracticeWord = {
  word_id: number;
  word_length: number;
  max_attempts: number;
};

export type PracticeGuessResponse = {
  correct: boolean;
  result: LetterResult[];
};

async function readError(response: Response, fallback: string) {
  try {
    const data = await response.json();
    return typeof data.detail === "string" ? data.detail : fallback;
  } catch {
    return fallback;
  }
}

export async function getPracticeWord(
  excludeId?: number,
): Promise<PracticeWord> {
  const parameters = excludeId ? `?exclude=${excludeId}` : "";

  const response = await fetch(
    `${API_BASE_URL}/wordly/practice/new${parameters}`,
  );

  if (!response.ok) {
    throw new Error(await readError(response, "Couldn't load a word."));
  }

  return response.json();
}

export async function submitPracticeGuess(
  wordId: number,
  guess: string,
): Promise<PracticeGuessResponse> {
  const response = await fetch(`${API_BASE_URL}/wordly/practice/guess`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ word_id: wordId, guess }),
  });

  if (!response.ok) {
    throw new Error(await readError(response, "Couldn't submit your guess."));
  }

  return response.json();
}

export async function revealPracticeWord(wordId: number): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/wordly/practice/reveal`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ word_id: wordId }),
  });

  if (!response.ok) {
    throw new Error(await readError(response, "Couldn't reveal the word."));
  }

  const data = await response.json();

  return data.answer;
}
