# Telegram Currency Converter Bot

Converts between currencies using live exchange rates (via [Frankfurter.app](https://www.frankfurter.app/) — free, no API key required).

## Commands
- `/start`, `/help` — instructions
- `/convert 100 USD EUR` — convert 100 USD to EUR
- `100 USD to EUR` — plain-text conversion also works
- `/list` — list all supported currency codes

## 1. Create your bot token
1. Open Telegram, message **@BotFather**.
2. Send `/newbot`, follow the prompts.
3. Copy the token it gives you (looks like `123456789:ABCdefGhIJKlmNoPQRstuVWxyz`).

## 2. Push this code to GitHub
```bash
git init
git add .
git commit -m "Initial commit: currency converter bot"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

## 3. Deploy on Render
1. Go to [render.com](https://render.com) → **New** → **Web Service**.
2. Connect your GitHub repo.
3. Render should auto-detect `render.yaml` (Blueprint). If not, set manually:
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`
   - **Plan**: Free
4. Add an environment variable:
   - `BOT_TOKEN` = the token from BotFather
5. Deploy. Render gives your service a public URL (e.g. `https://currency-converter-bot.onrender.com`) and sets `RENDER_EXTERNAL_URL` automatically — the bot uses this to register its Telegram webhook on startup. No manual webhook setup needed.

## 4. Test it
Open your bot in Telegram and send `/start`.

## Notes
- **Free tier sleep**: Render free web services spin down after ~15 min of no traffic and take a few seconds to wake on the next request/webhook call. That's fine for a personal bot — first message after idle may just be a bit slow.
- **No database needed** — this bot is fully stateless; every conversion is a fresh API call.
- To run locally instead of deploying: set `BOT_TOKEN` as an env var and run `python bot.py` (it auto-falls back to polling mode when `RENDER_EXTERNAL_URL` isn't set).
