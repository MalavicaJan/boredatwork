/** Small wrapper over localStorage.
 *
 *  Every call is guarded: private browsing, a full quota, or a user
 *  who has blocked storage all throw, and none of that should take a
 *  game down. Losing a saved run is survivable; a crash is not.
 */

export function loadJson<T>(key: string): T | null {
  try {
    const raw = window.localStorage.getItem(key);

    return raw ? (JSON.parse(raw) as T) : null;
  } catch {
    return null;
  }
}

export function saveJson(key: string, value: unknown): void {
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // Quota, private browsing, blocked storage. Nothing to do.
  }
}

export function clearKey(key: string): void {
  try {
    window.localStorage.removeItem(key);
  } catch {
    // As above.
  }
}
