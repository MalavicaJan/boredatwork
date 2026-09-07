import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import SiteHeader from "../components/SiteHeader";
import "./Progress.css";
import {
  getCurrentUser,
  getDailyProgress,
  getUserStreak,
} from "../api/users";

type DailyProgress = {
  challenge_id: number;
  game: string;
  completed: boolean;
};

function Progress() {
  const [currentStreak, setCurrentStreak] = useState(0);
  const [longestStreak, setLongestStreak] = useState(0);
  const [dailyProgress, setDailyProgress] = useState<DailyProgress[]>([]);
  const [authenticated, setAuthenticated] = useState<boolean | null>(null);


useEffect(() => {
  async function loadProgress() {
    const user = await getCurrentUser();

    if (!user) {
      setAuthenticated(false);
      return;
    }

    try {
      const [streak, progress] = await Promise.all([
        getUserStreak(),
        getDailyProgress(),
      ]);

      setCurrentStreak(streak.current_streak);
      setLongestStreak(streak.longest_streak);
      setDailyProgress(progress);
      setAuthenticated(true);
    } catch {
      setAuthenticated(false);
    }
  }

  loadProgress();
}, []);
  if (authenticated === null) {
  return (
    <main className="progress-page">
      <SiteHeader />

      <section className="progress-container">
        <p className="progress-message">Loading...</p>
      </section>
    </main>
  );
}

if (!authenticated) {
  return (
    <main className="progress-page">
      <SiteHeader />

      <section className="progress-container">
        <p className="progress-eyebrow">YOUR PROGRESS</p>
        <h1>Log in first.</h1>
        <Link className="progress-back" to="/login">
          Log in →
        </Link>
      </section>
    </main>
  );
}
  return (
    <main className="progress-page">
      <SiteHeader />

      <section className="progress-container">
        <p className="progress-eyebrow">YOUR PROGRESS</p>

        <h1>Progress</h1>

        <div className="progress-card">
          <strong>Current streak</strong>
          <span>
            {currentStreak} {currentStreak === 1 ? "day" : "days"}
          </span>
        </div>

        <div className="progress-card">
          <strong>Longest streak</strong>
          <span>
            {longestStreak} {longestStreak === 1 ? "day" : "days"}
          </span>
        </div>

        <div className="progress-card progress-games">
        <strong>Daily challenges</strong>

        <div className="progress-game-list">
            {dailyProgress.length === 0 ? (
            <span>None completed yet.</span>
            ) : (
            dailyProgress.map((item) => (
                <span key={`${item.challenge_id}-${item.game}`}>
                {item.game}
                </span>
            ))
            )}
        </div>
        </div>
        <a className="progress-back" href="/">
          ← Games
        </a>
      </section>
    </main>
  );
}

export default Progress;

