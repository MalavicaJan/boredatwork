import { API_BASE_URL } from "../../api/config";

export type SequenceState = {
  challenge_id: number;
  challenge_date: string;
  round: number;
  total_rounds: number;
  // Only ever the digits for the current round, never the full sequence.
  digits: string | null;
  completed: boolean;
  score: number | null;
};

export type SequenceAnswerResponse = {
  correct: boolean;
  round: number;
  game_over: boolean;
  score: number | null;
  next_round: number | null;
  next_digits: string | null;
};

export class SequenceConflictError extends Error {}

export async function getSequenceState(): Promise<SequenceState> {
  const response = await fetch(`${API_BASE_URL}/sequence/state`, {
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error("Couldn't load today's Sequence.");
  }

  return response.json();
}

export async function submitSequenceAnswer(
  round: number,
  answer: string,
): Promise<SequenceAnswerResponse> {
  const response = await fetch(`${API_BASE_URL}/sequence/answer`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify({ round, answer }),
  });

  const data = await response.json();

  if (response.status === 409) {
    // The client and the server disagree about the round. The server wins.
    throw new SequenceConflictError(data.detail);
  }

  if (!response.ok) {
    throw new Error(data.detail ?? "Couldn't submit your answer.");
  }

  return data;
}
