# Deploying boredatwork on a free Oracle Cloud VM

Everything runs on one machine: Postgres, the API, and Caddy serving the
built frontend. One origin, so there is no CORS and the session cookie keeps
working as CSRF protection.

Budget an evening. Most of it is Oracle's signup, not your app.

---

## What you end up with

```
        boredatwork.xyz
              |
         (DNS A record)
              |
      ┌───────▼────────┐
      │  Caddy :443    │  TLS, Let's Encrypt, auto-renewing
      │                │
      │  /api/*  ──────┼──► app:8000   FastAPI (uvicorn)
      │  /*      ──────┼──► /srv/frontend   built Vite files
      └────────────────┘         │
                                 ▼
                            db:5432  Postgres
```

Only Caddy publishes ports. Postgres and the API are reachable only from
inside the Docker network — Postgres is never exposed to the internet.

---

## 1. Create the Oracle account

<https://www.oracle.com/cloud/free/>

- A card is required for identity verification. Always Free resources do not
  charge it; you may see a temporary authorisation hold of about $1.
- Pick your **home region** carefully. It cannot be changed, and ARM capacity
  varies by region. Somewhere close to you, and ideally not the busiest one.

## 2. Create the VM

Compute → Instances → Create instance.

- **Image:** Ubuntu 24.04 (Minimal is fine)
- **Shape:** Ampere `VM.Standard.A1.Flex`, **2 OCPU / 12 GB**

  The Always Free allowance is 4 OCPU / 24 GB total. Taking half leaves room
  for a second instance later, and 12 GB is far more than this app needs.
- **SSH keys:** paste your public key (`cat ~/.ssh/id_ed25519.pub`). If you
  don't have one: `ssh-keygen -t ed25519`.
- Save the **public IP** shown after creation.

### "Out of capacity"

Very common on ARM. The instance simply fails to launch. Options: try a
different availability domain, try again later (capacity frees up in waves),
or use one of the retry scripts on GitHub that poll the API for you. This is
the single most annoying part of Oracle's free tier — it is not you doing
something wrong.

### Open ports 80 and 443

Two separate firewalls, and you must do **both**:

**Oracle's** — Networking → Virtual Cloud Networks → your VCN → Security
Lists → Default. Add two ingress rules:

| Source    | Protocol | Destination port |
|-----------|----------|------------------|
| 0.0.0.0/0 | TCP      | 80               |
| 0.0.0.0/0 | TCP      | 443              |

**Ubuntu's** — Oracle's images ship with iptables rules that drop everything
but SSH. On the VM:

```bash
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save
```

Forgetting the second one is the classic Oracle time-sink: the port looks open
in the console and nothing connects.

## 3. Point the domain at it

At your registrar (Cloudflare Registrar sells at cost), add:

| Type | Name | Value            |
|------|------|------------------|
| A    | @    | your.vm.public.ip |
| A    | www  | your.vm.public.ip |

**If you use Cloudflare DNS, set both records to "DNS only" (grey cloud) for
the first deploy.** With the orange proxy on, Let's Encrypt cannot reach your
server to validate the domain and Caddy will fail to get a certificate. Turn
the proxy on afterwards if you want it.

Check it resolves before continuing:

```bash
dig +short boredatwork.xyz
```

## 4. Set up the server

```bash
ssh ubuntu@your.vm.public.ip

sudo apt update && sudo apt upgrade -y

# Docker, from Docker's own repository
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker ubuntu
newgrp docker    # or log out and back in

# Security updates applied automatically. You own this box now.
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure --priority=low unattended-upgrades
```

## 5. Deploy

```bash
git clone https://github.com/<you>/boredatwork.git
cd boredatwork/deploy

cp .env.example .env
nano .env
```

Set `DOMAIN` and generate a real password:

```bash
openssl rand -base64 32
```

Then:

```bash
docker compose up -d --build
docker compose logs -f caddy
```

Watch for Caddy obtaining a certificate. It takes a few seconds. If it loops
with an error, the cause is almost always DNS not yet pointing here, port 80
blocked by one of the two firewalls, or the Cloudflare proxy being on.

Visit `https://boredatwork.xyz`. TLS is real and renews itself.

## 6. Apply the migrations

`create_tables` runs on every start, but it only creates **missing tables**.
It never alters an existing one, so column changes need the SQL applied by
hand — once, in order:

```bash
cd ~/boredatwork/deploy
source .env

for f in ../backend/migrations/*.sql; do
  echo "== $f"
  docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$f"
done
```

On a brand-new database most will no-op or error harmlessly, because
`create_tables` already built the tables in their current shape. The one that
matters is `006_game_results_won.sql`. Read the output rather than skimming it.

**This is the weakest part of the setup.** Ordering is by filename, there are
two files numbered `002`, and nothing records what has been applied. Adopting
Alembic is the fix, and it gets more painful the longer it waits.

## 7. Seed the content

Games are empty until you do this.

```bash
docker compose exec app python -m app.seed_wordly_words
docker compose exec app python -m app.seed_wordly_practice_words

# Slow: an expert puzzle takes a couple of seconds to generate.
docker compose exec app python -m app.seed_sudoku_puzzles

# Fetches from Wikipedia. Set a real contact address — Wikimedia's policy
# requires a descriptive User-Agent and they block generic ones.
docker compose exec \
  -e BLACKOUT_USER_AGENT="boredatwork/1.0 (https://boredatwork.xyz; you@email)" \
  app python -m app.seed_blackout_articles
```

Check it worked:

```bash
docker compose exec db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  -c "SELECT 'sudoku', count(*) FROM sudoku_puzzles
      UNION ALL SELECT 'articles', count(*) FROM blackout_articles
      UNION ALL SELECT 'words', count(*) FROM wordly_words;"
```

## 8. Backups

Nothing is backed up until you do this, and Oracle will not do it for you.

```bash
crontab -e
```

```
0 3 * * * /home/ubuntu/boredatwork/deploy/backup.sh
```

`backup.sh` writes a gzipped dump to `~/backups` and keeps 14 days.

**Restore it once, now, while nothing is at stake.** A backup you have never
restored is a hypothesis:

```bash
gunzip -c ~/backups/boredatwork-YYYY-MM-DD.sql.gz | \
  docker compose exec -T db psql -U "$POSTGRES_USER" -d postgres \
  -c "CREATE DATABASE restoretest;" && \
gunzip -c ~/backups/boredatwork-YYYY-MM-DD.sql.gz | \
  docker compose exec -T db psql -U "$POSTGRES_USER" -d restoretest
```

Dumps live on the same disk as the database, so they survive a bad migration
but not a lost instance. Copying them off the box occasionally — `scp`, or
Oracle's 20 GB free object storage — is what makes them a real backup.

## 9. Keep Oracle from reclaiming the instance

Always Free compute that stays idle across a 7-day window (roughly, low CPU
**and** low network) becomes eligible to be stopped. A quiet hobby site
qualifies. It is recoverable — you restart it from the console — but the site
is down until you notice.

A small periodic task is enough to avoid it:

```
*/15 * * * * curl -fsS https://boredatwork.xyz/api/v1/health > /dev/null
```

That also gives you a crude uptime check. An external monitor (UptimeRobot's
free tier) is better, because it tells you when the site is down rather than
just keeping it warm.

Accounts left entirely unused for 30 days can also be flagged as abandoned, so
log into the Oracle console occasionally.

---

## Updating

```bash
cd ~/boredatwork/deploy
./deploy.sh
```

Pull, rebuild, restart, health check. New migrations still go by hand — step 6.

## Day-to-day

```bash
docker compose ps                  # what is running
docker compose logs -f app         # API logs
docker compose logs -f caddy       # TLS and request logs
docker compose restart app         # restart just the API
docker compose down                # stop everything (data volumes survive)

docker compose exec db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"
```

## When something is wrong

**Caddy won't get a certificate.** DNS isn't pointing at the VM yet, port 80 is
blocked in one of the two firewalls, or the Cloudflare proxy is on. Check in
that order.

**502 from Caddy.** The API isn't up. `docker compose logs app` — usually a
database connection problem or a crash at import.

**API can't reach the database.** `docker compose ps` to check `db` is
healthy. The hostname is `db`, not `localhost` — inside compose, each service
is its own host.

**Site loads but games are empty.** Step 7 wasn't run, or was run against a
different database.

**Frontend changes don't show.** The `frontend` service is one-shot: it builds
and exits. `docker compose up -d --build frontend` to rebuild.

---

## Still outstanding before this is genuinely public

From the pre-deployment review, deliberately not fixed yet:

- `GET /api/v1/users/` lists every user, unauthenticated. Delete the route.
- No rate limiting on login or register.
- Login response time reveals whether a username exists.
- `/users/daily-progress` returns all history with no date filter.

The first two are the ones I would not leave on a public domain.
