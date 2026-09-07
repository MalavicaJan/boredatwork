import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

import SiteHeader from "../components/SiteHeader";
import { useAuth } from "../api/auth";
import "./Login.css";
import { loginUser } from "../api/users";

function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const navigate = useNavigate();
  const { refresh } = useAuth();

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");

    setSubmitting(true);

    try {
      await loginUser(username, password);

      // Tell the shared auth state rather than reloading the whole app.
      await refresh();
      navigate("/");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Login failed.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="login-page">
      <SiteHeader />

      <section className="login-container">
        <h1>Log in</h1>

        <form className="login-form" onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
          />

          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />

          <button type="submit" disabled={submitting}>
            {submitting ? "Logging in..." : "Log in"}
          </button>
        </form>

        {error && <p className="login-error">{error}</p>}

        <p className="login-note">
          Want to keep your challenge progress and streak? Log in. Just here
          to play? No login needed.
        </p>
        <p className="register-link">
        Don't have an account?{" "}
        <Link to="/register">Create one.</Link>
        </p>
      </section>
    </main>
  );
}

export default Login;