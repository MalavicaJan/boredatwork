import type { ReactNode } from "react";
import { Link } from "react-router-dom";

import { useAuth } from "../api/auth";
import SiteHeader from "./SiteHeader";
import "./GamePage.css";

type GamePageProps = {
  /** Tone class from tokens.css, e.g. "tone-sudoku". */
  tone: string;
  title: string;
  eyebrow?: string;
  /** Small line under the title: a date, a difficulty, a mode. */
  meta?: string;
  intro?: ReactNode;
  /** Wider column for text-heavy games. */
  wide?: boolean;
  /** Set on games whose results feed the daily streak, so signed-out
   *  players are told what an account is actually for. Leave off for
   *  games that record nothing. */
  streak?: boolean;
  children: ReactNode;
};

/** The frame shared by every game: one header, one title block, one
 *  spacing rhythm, and the account state carried through. */
export default function GamePage({
  tone,
  title,
  eyebrow,
  meta,
  intro,
  wide = false,
  streak = false,
  children,
}: GamePageProps) {
  const { username, loading } = useAuth();

  return (
    <main className={`game-page ${tone}`}>
      <SiteHeader />

      <div className={`game-page-inner ${wide ? "wide" : ""}`}>
        <div className="game-page-intro">
          {eyebrow && <p className="game-page-eyebrow">{eyebrow}</p>}

          <h1 className="game-page-title">{title}</h1>

          {meta && <p className="game-page-meta">{meta}</p>}

          {intro && <p className="game-page-lede">{intro}</p>}

          {streak && !loading && !username && (
            <p className="game-page-streak">
              <Link to="/register">Create an account</Link> to keep a daily
              streak.
            </p>
          )}
        </div>

        {children}
      </div>
    </main>
  );
}
