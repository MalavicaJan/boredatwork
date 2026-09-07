import { API_BASE_URL } from "./config"

export type SequenceState = {
  completed: boolean;
  score: number | null;
};

export async function getSequenceState(): Promise<SequenceState> {
  const response = await fetch(
    `${API_BASE_URL}/sequence/state`,
    {
      credentials: "include",
    },
  );

  if (!response.ok) {
    throw new Error("Failed to load Sequence state");
  }

  return response.json();
}

export async function loginUser(username: string, password: string) {
  const response = await fetch(`${API_BASE_URL}/users/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify({
      username,
      password,
    }),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Login failed");
  }

  return data;
}
export async function registerUser(username: string, password: string) {
  const response = await fetch(`${API_BASE_URL}/users/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      username,
      password,
    }),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Registration failed");
  }

  return data;
}
export async function getCurrentUser() {
  const response = await fetch(`${API_BASE_URL}/users/me`, {
    credentials: "include",
  });

  if (!response.ok) {
    return null;
  }

  return response.json();
}
export async function logoutUser() {
  const response = await fetch(`${API_BASE_URL}/users/logout`, {
    method: "POST",
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error("Logout failed");
  }
}
export async function getUserStreak() {
  const response = await fetch(`${API_BASE_URL}/users/streak`, {
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error("Failed to load streak");
  }

  return response.json();
}
export async function getDailyProgress() {
  const response = await fetch(`${API_BASE_URL}/users/daily-progress`, {
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error("Failed to load daily progress");
  }

  return response.json();
}