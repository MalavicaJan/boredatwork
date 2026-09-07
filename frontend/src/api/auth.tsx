import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import type { ReactNode } from "react";

import { getCurrentUser } from "./users";

type AuthValue = {
  username: string | null;
  loading: boolean;
  setUsername: (username: string | null) => void;
  refresh: () => Promise<void>;
};

const AuthContext = createContext<AuthValue>({
  username: null,
  loading: true,
  setUsername: () => {},
  refresh: async () => {},
});

/** Fetches the current user once for the whole app instead of on every
 *  page mount, so navigating between games doesn't re-ask. */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [username, setUsername] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const user = await getCurrentUser();
      setUsername(user?.username ?? null);
    } catch {
      // Not signed in is the normal case, not an error.
      setUsername(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const value = useMemo(
    () => ({ username, loading, setUsername, refresh }),
    [username, loading, refresh],
  );

  return (
    <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
