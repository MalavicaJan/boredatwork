import { Link } from "react-router-dom";

import { useAuth } from "../api/auth";
import { logoutUser } from "../api/users";
import "./SiteHeader.css";

/** The one header every page wears: brand on the left, a way home and
 *  the account state on the right. Extracted from GamePage so the
 *  account pages can't drift away from it. */
export default function SiteHeader({ showBack = true }: { showBack?: boolean }) {
  const { username, loading, setUsername } = useAuth();

  return (
    <header className="site-header">
      <Link className="site-logo" to="/">
        boredatwork.xyz
      </Link>

      <nav className="site-nav">
        {showBack && (
          <Link className="site-link" to="/">
            ← All games
          </Link>
        )}

        {!loading &&
          (username ? (
            <>
              <Link className="site-account" to="/progress">
                {username}
              </Link>

              <button
                className="site-link"
                onClick={async () => {
                  await logoutUser();
                  setUsername(null);
                }}
              >
                Log out
              </button>
            </>
          ) : (
            <Link className="site-link" to="/login">
              Log in
            </Link>
          ))}
      </nav>
    </header>
  );
}
