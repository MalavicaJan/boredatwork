import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import "./Home.css";
import { getCurrentUser, logoutUser } from "../api/users";

function Home() {
  const [username, setUsername] = useState<string | null>(null);

  useEffect(() => {
    getCurrentUser()
      .then((user) => setUsername(user?.username ?? null))
      .catch(() => setUsername(null));
  }, []);

  return (
    <main className="home">
      <header className="header">
        <div className="logo">boredatwork.xyz</div>

        {username ? (
          <div className="user-menu">
            <span className="logged-in-user">{username}</span>

            <Link className="progress-link" to="/progress">
              Progress
            </Link>

            <button
              className="login-button"
              onClick={async () => {
                await logoutUser();
                setUsername(null);
              }}
            >
              Log out
            </button>
          </div>
        ) : (
          <Link className="login-button" to="/login">
            Log in
          </Link>
        )}
      </header>

      <section className="hero">
        <p className="eyebrow">YOUR PRODUCTIVITY BREAK</p>

        <h1>
          Bored?
          <br />
          Good.
        </h1>

        <p className="subtitle">
          Short games for when work needs a tiny break.
        </p>
      </section>

      <section className="game-section">
        <div className="section-heading">
          <h2>Daily challenge</h2>
          <p>One go each. Everyone gets the same puzzle, new at midnight UTC.</p>
        </div>

        <div className="game-grid">
          <GameCard
            title="Wordly"
            description="Guess the word in six tries."
            to="/wordly"
            tone="tone-wordly"
          />

          <GameCard
            title="Sequence"
            description="Remember the sequence."
            to="/sequence"
            tone="tone-sequence"
          />

          <GameCard
            title="WikiGuessr"
            description="Uncover the hidden article."
            to="/blackout"
            tone="tone-wikiguessr"
          />
        </div>
      </section>

      <section className="game-section">
        <div className="section-heading">
          <h2>Play anytime</h2>
          <p>No limits, no account needed. Stop whenever the meeting starts.</p>
        </div>

        <div className="game-grid">
          <GameCard
            title="Sudoku"
            description="Fill the grid. Four difficulties."
            to="/sudoku"
            tone="tone-sudoku"
          />

          <GameCard
            title="Memory"
            description="Find every pair."
            to="/memory"
            tone="tone-memory"
          />

          <GameCard
            title="Wordly Practice"
            description="Same game, as many words as you want."
            to="/wordly-practice"
            tone="tone-practice"
          />
        </div>
      </section>
    </main>
  );
}

type GameCardProps = {
  title: string;
  description: string;
  to?: string;
  /** Tone class from tokens.css. The card wears the colour of the page
   *  it leads to, so it reads as a preview rather than a label. */
  tone?: string;
};

function GameCard({ title, description, to, tone }: GameCardProps) {
  const content = (
    <>
      <div className="game-card-title">{title}</div>

      <div className="game-card-description">{description}</div>

      <div className="game-card-action">{to ? "PLAY →" : "SOON"}</div>
    </>
  );

  if (!to) {
    return <article className="game-card">{content}</article>;
  }

  return (
    <Link className={`game-card active ${tone ?? ""}`} to={to}>
      {content}
    </Link>
  );
}

export default Home;
