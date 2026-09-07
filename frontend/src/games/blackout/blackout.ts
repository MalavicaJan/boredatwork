import { API_BASE_URL } from "../../api/config";

export type BlackoutToken = {
  kind: "word" | "fixed";
  text: string | null;
  length: number | null;
};

export type BlackoutState = {
  challenge_id: number;
  challenge_date: string;
  title_tokens: BlackoutToken[];
  body_tokens: BlackoutToken[];
  title_word_count: number;
};

export type BlackoutHit = {
  index: number;
  text: string;
};

export type BlackoutGuessResponse = {
  guess: string;
  title_hits: BlackoutHit[];
  body_hits: BlackoutHit[];
  count: number;
};

export type BlackoutReveal = {
  title: string;
  title_tokens: BlackoutToken[];
  body_tokens: BlackoutToken[];
  source_url: string;
};

async function readError(response: Response, fallback: string) {
  try {
    const data = await response.json();
    return typeof data.detail === "string" ? data.detail : fallback;
  } catch {
    return fallback;
  }
}

export async function getBlackoutToday(): Promise<BlackoutState> {
  const response = await fetch(`${API_BASE_URL}/blackout/today`);

  if (!response.ok) {
    throw new Error(await readError(response, "Couldn't load today's game."));
  }

  return response.json();
}

export async function submitBlackoutGuess(
  challengeId: number,
  guess: string,
): Promise<BlackoutGuessResponse> {
  const response = await fetch(`${API_BASE_URL}/blackout/guess`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ challenge_id: challengeId, guess }),
  });

  if (!response.ok) {
    throw new Error(await readError(response, "Couldn't submit your guess."));
  }

  return response.json();
}

export async function revealBlackout(
  challengeId: number,
): Promise<BlackoutReveal> {
  const response = await fetch(`${API_BASE_URL}/blackout/reveal`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ challenge_id: challengeId }),
  });

  if (!response.ok) {
    throw new Error(await readError(response, "Couldn't reveal the article."));
  }

  return response.json();
}
