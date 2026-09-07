import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

import SiteHeader from "../components/SiteHeader";
import "./Register.css";
import { registerUser } from "../api/users";

function Register() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  
  async function handleSubmit(event: FormEvent) {
  event.preventDefault();
  setError("");

  try {
    await registerUser(username, password);
    window.location.href = "/login";
  } catch (err) {
    setError(
      err instanceof Error ? err.message : "Registration failed.",
    );
  }
}

  return (
    <main className="register-page">
      <SiteHeader />

      <section className="register-container">
        <h1>Create account</h1>

        <form className="register-form" onSubmit={handleSubmit}>
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

          <button type="submit">Create account</button>
        </form>

        {error && <p className="register-error">{error}</p>}
        <p className="login-link">
        Already have an account?{" "}
        <Link to="/login">Log in.</Link>
        </p>
      </section>
    </main>
  );
}

export default Register;