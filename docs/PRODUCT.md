# boredatwork.xyz — Product Definition

## 1. Product Vision

boredatwork.xyz is a collection of short cognitive games designed for people who need a quick mental break during the workday.

The product should be fast, simple, polished, and fun.

The core experience is:

> Open the website → choose a game → play immediately.

---

## 2. Target User

The primary user is someone at work who has a few minutes available and wants a short mental challenge.

Typical session length:

- 30 seconds
- 1 minute
- 3 minutes
- 5 minutes

The product should not require a large time commitment.

---

## 3. Product Personality

boredatwork.xyz should feel:

- Minimal
- Playful
- Slightly sarcastic
- Fast
- Modern
- Professional
- Not childish
- Not distracting

Example brand voice:

> You should probably be working.

> Congratulations. You wasted 3 minutes productively.

---

## 4. MVP

The first public version will contain:

### Core

- Homepage
- User registration
- Username
- Password
- Login
- Logout
- Persistent user account
- Unique usernames
- Permanent usernames
- Secure password storage

### Games

Initial games:

1. Wordly
2. Sequence
3. Memory

Additional games will be added after the core architecture is proven.

### Progress

- Game scores
- Daily challenges
- Current streak
- Longest streak
- Leaderboards

---

## 5. Authentication

Users create an account using:

- Unique username
- Password

No social login will be required for the MVP.

Passwords must never be stored directly.

The backend stores a secure password hash.

Usernames are unique and cannot be changed after account creation.

---

## 6. Daily Streak

A user earns a streak day by completing at least one daily challenge.

Starting a game does not count.

Opening the website does not count.

Completing a qualifying daily challenge counts.

The backend is responsible for calculating and storing streak information.

---

## 7. Leaderboards

The product will eventually support:

### Daily leaderboard

Shows the highest scores for the current day.

### Game leaderboard

Shows the highest scores for a specific game.

### All-time leaderboard

Shows the highest accumulated scores.

### Streak leaderboard

Shows users with the longest active streaks.

---

## 8. MVP Non-Goals

The initial product will NOT include:

- Mobile applications
- Multiplayer games
- Chat
- Social feeds
- Subscriptions
- Advertising
- Complex user profiles
- AI features unless required by a specific game
- Microservices
- Kubernetes
- Complex infrastructure

These may be considered later.

---

## 9. Product Principle

The application should remain simple.

Every new feature should answer at least one of these questions:

1. Does it make the games more fun?
2. Does it improve the user experience?
3. Does it improve retention?
4. Does it provide meaningful technical value?

If it does none of these, it probably does not belong in the product.

---

## 10. Core User Journey

New user:

1. Visit boredatwork.xyz
2. Choose a username
3. Create a password
4. Account is created
5. User enters the application
6. User chooses a game
7. User plays
8. Score is recorded
9. Streak is updated
10. User can view the leaderboard

Returning user:

1. Visit boredatwork.xyz
2. Login
3. See current streak and scores
4. Play today's games
5. Score is recorded
6. Streak is updated
7. Leaderboard is updated

---

## 11. Product Success Criteria

The MVP is successful when a new user can:

- Create an account
- Log in
- Select a game
- Play a complete game
- Receive a score
- Have the score stored
- Build a daily streak
- See their position on a leaderboard

The entire experience should feel fast and reliable.