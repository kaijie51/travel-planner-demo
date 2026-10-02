# Wayfare: AI group itinerary planner (SC2304 prototype)

A Streamlit demo of the group travel planner described in the project report. Claude (`claude-sonnet-5-5`) drafts the itineraries. The app does everything else in plain Python: fairness scoring, score breakdowns, de-identification and the weather lookup.

> "Wayfare" is a placeholder name. To rename the app, change `APP_NAME` in `config.py`.

## Features

| Report feature | Where it appears in the app |
|---|---|
| Trip constraints (dates, hours, budget, transport, hotel, crowd tolerance, diet) | **1 · Trip** tab |
| Per-person preference profiles + adjustable group weights | **2 · Travellers** tab |
| Locked-in anchors (fixed date/time) and flexible must-visits | **3 · Must-visits & links** tab |
| TikTok / Instagram / web link import | **3 · Must-visits & links** tab → *Import* |
| Several itinerary options, compared side by side | **Plan** tab (3 strategies generated in parallel) |
| Fairness (weighted Nash social welfare, Jain's index, least-satisfied member) | **Plan** tab → *Group balance* |
| Explainability: score breakdown per stop, "why this instead of that", counterfactuals | **Plan** tab |
| Human in the loop: lock / swap / remove stops, switch transport, regenerate, confirm | **Plan** tab |
| Weather forecast + wet-weather backups | Trip and Plan tabs (Open-Meteo, no key needed) |
| Real-time re-planning (rain, delays, cravings) with accept/discard | **Live re-plan** tab |
| Tag-based discovery of lesser-known places | **Explore** tab |
| Privacy layer, PDPA consent, data sources & limitations, AI call log | **Privacy & data** tab + sidebar |

Not in the prototype: accounts, real multi-user groups, live prices/crowds, bookings, restaurant menus, Wanderlog import, and learning from reviews.

## API key

The app reads `ANTHROPIC_API_KEY` from Streamlit secrets, falling back to an environment variable.

**GitHub repository secrets are not visible to Streamlit Cloud.** Those secrets only exist for GitHub Actions. You have to paste the key into Streamlit's own Secrets box (step 4 below).

## Run locally

```bash
cd travel-planner-demo
py -m pip install -r requirements.txt
copy .streamlit\secrets.toml.example .streamlit\secrets.toml   # then paste your key into it
py -m streamlit run app.py
```

## Deploy a public link (Streamlit Community Cloud, free)

1. Push this folder to a GitHub repository. `.gitignore` already keeps `secrets.toml` out of the repo.
2. Go to https://share.streamlit.io and sign in with GitHub.
3. Click **Create app**, pick the repo and branch, and set the main file to `app.py`. Under *Advanced settings*, choose Python 3.12 or newer.
4. In **Advanced settings → Secrets**, paste:
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-..."
   APP_PASSWORD = "pick-an-access-code"   # optional but recommended
   ```
   Anyone with the link can spend your API credits, so set an `APP_PASSWORD` and share it only with your markers.
5. Click **Deploy**. You'll get a link like `https://<your-app>.streamlit.app`.

## Demo tips

- The Singapore group trip is preloaded, and **Load Singapore demo** in the sidebar resets it. The presenter script is in the sidebar expander.
- Turn on **AI generation** in the sidebar just before you present, or click the consent button when it appears. Showing that notice is part of the PDPA story.
- With reasoning effort set to "low", generating 3 options in parallel usually takes about 30–90 s. Use 2 options or fewer days if it needs to be faster.
- Generate one plan before you go on stage. The plan stays in the browser session, so you can present from it even if the Wi-Fi drops.

## Code map

| File | Purpose |
|---|---|
| `app.py` | Streamlit UI |
| `ai.py` | All Claude calls (structured outputs, parallel option generation, refusal fallback) |
| `schemas.py` | Pydantic schemas Claude must answer in |
| `privacy.py` | De-identification layer: allowlist, aliases, scrubbing, group-level needs |
| `scoring.py` | Deterministic fairness metrics, costs, pace checks, score breakdowns |
| `weather.py` | Open-Meteo geocoding + forecast |
| `demo.py` | Singapore preset + presenter script |
| `config.py` | Name, model, interests, strategies |
