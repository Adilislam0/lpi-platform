# Boardy × LPI Platform — Integration Plan

**Author:** Daksh Garg (Phase 4)
**Date:** June 2026
**Branch:** `daksh-phase-4`

---

## What Are We Trying to Do?

Boardy is our first real customer. They generate events when things happen on
their platform — for example, when two people are matched together. We want to:

1. **Receive** those events automatically on our platform (via a webhook)
2. **Store** them in our Supabase database as activity signals
3. **Use** them in our recommendation engine to give users better, real-data-driven suggestions

Right now our signals table only has test/simulated data. Boardy's real events
will be the first live data we use for recommendations.

---

## The Big Picture (Simple Flow)

```
Boardy's server
    │
    │  sends a POST request every time something happens
    │  (e.g. a match is created between two people)
    ▼
Our webhook endpoint
POST https://<our-domain>/api/v1/webhooks/boardy
    │
    │  we verify it's really from Boardy (using a shared secret)
    │  we parse the event
    ▼
Our Supabase database
    activity_signals table
    stream = "boardy"
    event_type = "match_created" (or whatever Boardy sends)
    │
    ▼
Our recommendation engine
    reads Boardy signals when generating recommendations for users
```

---

## Step 1 — What We Need to Give Boardy

Boardy needs two things from us to start sending us data:

### 1a. The Webhook URL

This is the address on our server where Boardy will POST their events.

```
https://<our-domain>/api/v1/webhooks/boardy
```

> **Right now this endpoint does not exist yet.** We need to build it
> (see Step 3 below). Once built and deployed, this is the URL we share.

For local testing during development:
```
http://localhost:8000/api/v1/webhooks/boardy
```

### 1b. A Shared Secret (Webhook Secret)

This is a long random string that only Boardy and we know. Boardy includes it
in every request they send us (in a header like `X-Boardy-Secret`). We check
it on our end. If the secret is wrong, we reject the request.

**This is important for security** — without it, anyone could send fake events
to our webhook.

How to generate a good secret:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Example output (do not use this one — generate your own):
```
a3f8c2e1d4b7a9f0e2c5d8b1a4e7f0c3d6b9a2e5f8c1d4b7a0e3f6c9d2b5a8
```

Store this in our `.env` file as:
```
BOARDY_WEBHOOK_SECRET=a3f8c2e1d4b7...
```

And give the same value to Boardy to put on their end.

---

## Step 2 — How the JWT Token Works

Our existing signal endpoint (`POST /api/v1/signals/`) requires a **Supabase
JWT token** in the `Authorization` header. This works fine for our own users
who log in through our frontend.

**The problem:** Boardy's server is not a user. It does not have a Supabase
account. It cannot log in to get a JWT.

**The solution:** The Boardy webhook endpoint is a **separate endpoint** that
does NOT require a JWT. Instead, it uses the **shared webhook secret** (from
Step 1b) to verify the request is really from Boardy.

Think of it this way:

| Who is calling | How they authenticate |
|---|---|
| Our frontend users | Supabase JWT in Authorization header |
| Boardy's server | Shared webhook secret in X-Boardy-Secret header |

Inside our webhook handler, once we verify the secret, we write the signal to
Supabase using our **service role key** (which bypasses row-level security),
and we assign the signal to a dedicated Boardy service user ID.

---

## Step 3 — What We Need to Build

### New endpoint: `POST /api/v1/webhooks/boardy`

This endpoint will:

1. Read the `X-Boardy-Secret` header from the incoming request
2. Compare it to our `BOARDY_WEBHOOK_SECRET` from `.env`
3. If it does not match → return `401 Unauthorized` and stop
4. If it matches → parse the event body
5. Convert the Boardy event into our Signal format
6. Save it to Supabase (`activity_signals` table, `stream = "boardy"`)
7. Return `200 OK` to Boardy so they know we received it

### New `.env` variable

```
BOARDY_WEBHOOK_SECRET=<the shared secret we agree on with Boardy>
BOARDY_SERVICE_USER_ID=boardy-service  # the user_id we assign to all Boardy signals
```

### New `config.py` fields

Add to `Settings` class:
```python
boardy_webhook_secret: str = ""
boardy_service_user_id: str = "boardy-service"
```

---

## Step 4 — What Boardy Events Look Like

We need to ask Boardy for their event schema. Based on what we already know,
a typical Boardy event might look like:

```json
{
  "event": "match_created",
  "data": {
    "person_a": "Alice",
    "person_b": "Bob",
    "score": 0.85,
    "matched_at": "2026-06-22T10:00:00Z"
  }
}
```

We will map this to our Signal format:

```json
{
  "id": "<uuid we generate>",
  "user_id": "boardy-service",
  "stream": "boardy",
  "event_type": "match_created",
  "payload": {
    "person_a": "Alice",
    "person_b": "Bob",
    "score": 0.85,
    "matched_at": "2026-06-22T10:00:00Z"
  },
  "source": "boardy_webhook",
  "timestamp": "<when we received it>"
}
```

---

## Step 5 — How Recommendations Will Use Boardy Data

Once Boardy signals are stored, our recommendation engine will automatically
pick them up. No changes needed to the engine itself — it already reads all
signals for a user.

To see Boardy signals specifically:
```
GET /api/v1/signals/?stream=boardy
```

To get recommendations that factor in Boardy data:
```
POST /api/v1/recommendations/{user_id}/run
```

The pipeline will see the Boardy signals and generate recommendations at
the `collective-intelligence` phase (which is where signal-driven
recommendations always land — connecting information from multiple sources).

---

## Step 6 — Checklist Before Going Live

- [ ] Generate a shared webhook secret (see Step 1b)
- [ ] Add `BOARDY_WEBHOOK_SECRET` to our `.env` and production environment
- [ ] Build `POST /api/v1/webhooks/boardy` endpoint (see Step 3)
- [ ] Deploy to staging server so Boardy can test
- [ ] Share the webhook URL and secret with Boardy team
- [ ] Ask Boardy for their exact event payload schema
- [ ] Update the event mapping in our webhook handler to match their schema
- [ ] Test: Boardy sends a test event → we confirm it appears in Supabase
- [ ] Test: Run `POST /recommendations/{user_id}/run` → confirm Boardy signal
  appears in a recommendation's `source_signals`

---

## Step 7 — Testing Without Boardy (While We Wait)

We do not need to wait for Boardy to be ready to test our side. We can
simulate Boardy events by calling our webhook endpoint directly:

```bash
curl -X POST https://localhost:8000/api/v1/webhooks/boardy \
  -H "X-Boardy-Secret: <our secret>" \
  -H "Content-Type: application/json" \
  -d '{
    "event": "match_created",
    "data": {
      "person_a": "Alice",
      "person_b": "Bob",
      "score": 0.85
    }
  }'
```

This lets us build and test the full pipeline before Boardy is ready to connect.

---

## Summary for Boardy Team (What to Send Them)

> Hi Boardy team,
>
> To connect your platform to LPI, please configure a webhook on your side
> with the following details:
>
> **Webhook URL:**
> `https://<our-domain>/api/v1/webhooks/boardy`
>
> **Authentication:**
> Include the following header in every request:
> `X-Boardy-Secret: <shared secret we will provide separately>`
>
> **Expected format:**
> Send a `POST` request with `Content-Type: application/json`. The body
> should contain the event name and the relevant data fields for that event.
>
> **We will acknowledge every event** with a `200 OK` response. If you
> receive a `401`, the secret is wrong. If you receive a `500`, please
> retry — something failed on our side.
>
> Please also share with us the full list of event types you will send
> (e.g. `match_created`, `match_accepted`, etc.) and a sample payload
> for each so we can map them correctly.

---

## Files to Create/Modify

| File | Action | What |
|---|---|---|
| `src/lpi/routers/webhooks.py` | Modify | Add `POST /boardy` endpoint |
| `src/lpi/config.py` | Modify | Add `boardy_webhook_secret`, `boardy_service_user_id` |
| `.env` / `.env.example` | Modify | Add `BOARDY_WEBHOOK_SECRET` |
| `supabase/migrations/` | New file | No schema change needed — `activity_signals` table already supports Boardy via `stream="boardy"` |
| `tests/test_boardy_webhook.py` | New file | Tests for the new endpoint |

---

*This document lives at `docs/boardy-integration-plan.md` in the `daksh-phase-4` branch.*
