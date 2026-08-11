import os
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]
# Render sets this automatically for every web service, e.g. https://myapp.onrender.com
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")
PORT = int(os.environ.get("PORT", "10000"))

API_URL = "https://api.frankfurter.app/latest"


def fetch_conversion(amount: float, from_cur: str, to_cur: str):
    """Hit Frankfurter (free, no API key needed) for a live rate."""
    params = {"amount": amount, "from": from_cur.upper(), "to": to_cur.upper()}
    resp = requests.get(API_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    rates = data.get("rates", {})
    if to_cur.upper() not in rates:
        return None
    return rates[to_cur.upper()], data.get("date")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hi! I'm a currency converter bot.\n\n"
        "Usage:\n"
        "/convert <amount> <from> <to>\n"
        "Example: /convert 100 USD EUR\n\n"
        "You can also just type it plain, e.g.:\n"
        "100 USD to EUR\n\n"
        "Send /list to see supported currency codes."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)


async def list_currencies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        resp = requests.get("https://api.frankfurter.app/currencies", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        lines = [f"{code} - {name}" for code, name in sorted(data.items())]
        text = "Supported currencies:\n" + "\n".join(lines)
        # Telegram messages cap at 4096 chars; chunk if needed
        for i in range(0, len(text), 4000):
            await update.message.reply_text(text[i:i + 4000])
    except Exception as e:
        logger.exception("Failed to fetch currency list")
        await update.message.reply_text("Sorry, couldn't fetch the currency list right now.")


async def convert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) != 3:
        await update.message.reply_text(
            "Usage: /convert <amount> <from> <to>\nExample: /convert 100 USD EUR"
        )
        return
    await do_convert(update, args[0], args[1], args[2])


async def plain_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Parses messages like '100 USD to EUR' or '100 usd eur'."""
    text = update.message.text.strip().lower().replace(" to ", " ")
    parts = text.split()
    if len(parts) != 3:
        return  # not a conversion request, ignore silently
    amount, from_cur, to_cur = parts
    await do_convert(update, amount, from_cur, to_cur)


async def do_convert(update: Update, amount_raw: str, from_cur: str, to_cur: str):
    try:
        amount = float(amount_raw)
    except ValueError:
        await update.message.reply_text("⚠️ Amount must be a number. Example: /convert 100 USD EUR")
        return

    from_cur = from_cur.upper()
    to_cur = to_cur.upper()

    try:
        result = fetch_conversion(amount, from_cur, to_cur)
    except requests.RequestException:
        logger.exception("API request failed")
        await update.message.reply_text("⚠️ Couldn't reach the exchange rate service. Try again shortly.")
        return

    if result is None:
        await update.message.reply_text(
            f"⚠️ Couldn't convert {from_cur} → {to_cur}. Check the currency codes (e.g. USD, EUR, GBP, NGN).\n"
            "Send /list to see all supported codes."
        )
        return

    converted, date = result
    await update.message.reply_text(
        f"💱 {amount:,.2f} {from_cur} = {converted:,.2f} {to_cur}\n"
        f"(rate date: {date})"
    )


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Unknown command. Send /help to see how to use me.")


def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("list", list_currencies))
    application.add_handler(CommandHandler("convert", convert))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, plain_text))
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    if RENDER_EXTERNAL_URL:
        # Webhook mode - required on Render (free web service needs a bound port)
        webhook_path = BOT_TOKEN  # use token as an unguessable path segment
        webhook_url = f"{RENDER_EXTERNAL_URL}/{webhook_path}"
        logger.info("Starting webhook at %s", webhook_url)
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=webhook_path,
            webhook_url=webhook_url,
        )
    else:
        # Local fallback for testing on your machine
        logger.info("RENDER_EXTERNAL_URL not set - running in polling mode (local dev)")
        application.run_polling()


if __name__ == "__main__":
    main()
