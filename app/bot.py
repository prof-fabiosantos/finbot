"""
Bot do Telegram — handlers de comandos e mensagens.
"""
import os
import asyncio
import logging
from aiohttp import web
from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from .database import init_db
from .llm import extract_expense
from . import services

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
# httpx loga TODAS as requisições em INFO, polui demais
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


# ------------------------- Comandos -------------------------

async def cmd_start(update: Update, _: ContextTypes.DEFAULT_TYPE):
    msg = (
        "👋 Olá! Sou seu assistente financeiro.\n\n"
        "Pra registrar um gasto, é só me mandar uma mensagem curta:\n"
        "• <code>uber 27</code>\n"
        "• <code>almoço 35,90</code>\n"
        "• <code>netflix 39.90</code>\n\n"
        "Comandos disponíveis:\n"
        "/total — total do mês\n"
        "/categorias — gastos por categoria\n"
        "/recentes — últimos 10 gastos\n"
        "/desfazer — apaga o último registro\n"
        "/ajuda — mostra esta mensagem"
    )
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)


async def cmd_total(update: Update, _: ContextTypes.DEFAULT_TYPE):
    total = services.total_this_month(update.effective_user.id)
    await update.message.reply_text(
        f"💰 Total do mês: <b>R${total:.2f}</b>",
        parse_mode=ParseMode.HTML,
    )


async def cmd_categorias(update: Update, _: ContextTypes.DEFAULT_TYPE):
    rows = services.total_by_category_month(update.effective_user.id)
    if not rows:
        await update.message.reply_text("Nenhum gasto registrado este mês ainda.")
        return
    lines = ["📊 <b>Gastos por categoria (mês):</b>\n"]
    for cat, total in rows:
        lines.append(f"• {cat}: R${total:.2f}")
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)


async def cmd_recentes(update: Update, _: ContextTypes.DEFAULT_TYPE):
    items = services.list_recent(update.effective_user.id, limit=10)
    if not items:
        await update.message.reply_text("Nenhum gasto registrado ainda.")
        return
    lines = ["🧾 <b>Últimos gastos:</b>\n"]
    for e in items:
        date = e.created_at.strftime("%d/%m")
        lines.append(f"• {date} — {e.item} ({e.category}): R${e.amount:.2f}")
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)


async def cmd_desfazer(update: Update, _: ContextTypes.DEFAULT_TYPE):
    last = services.delete_last(update.effective_user.id)
    if not last:
        await update.message.reply_text("Não há nada pra desfazer.")
        return
    await update.message.reply_text(
        f"🗑️ Removido: {last.item} ({last.category}) — R${last.amount:.2f}"
    )


# ------------------------- Mensagens livres -------------------------

async def handle_message(update: Update, _: ContextTypes.DEFAULT_TYPE):
    """
    Toda mensagem que não é comando passa pelo LLM.
    Se for gasto, registra. Se for consulta, sugere comandos. Senão, pede pra reformular.
    """
    user_id = update.effective_user.id
    text = update.message.text.strip()

    # Feedback visual: "digitando..." enquanto o LLM responde
    await update.message.chat.send_action("typing")

    data = extract_expense(text)
    tipo = data.get("tipo")

    if tipo == "gasto":
        try:
            item = data["item"]
            category = data["categoria"]
            amount = float(data["valor"])
        except (KeyError, ValueError, TypeError):
            await update.message.reply_text(
                "❓ Não consegui entender o valor. Tenta algo como <code>uber 27</code>.",
                parse_mode=ParseMode.HTML,
            )
            return

        exp = services.save_expense(user_id, item, category, amount, text)
        date_str = exp.created_at.strftime("%Y-%m-%d")
        reply = (
            "✅ <b>Gasto Registrado!</b>\n"
            f"📝 {exp.item} ({exp.category})\n"
            f"💰 <b>R${exp.amount:.2f}</b>\n"
            f"📅 {date_str} — #{exp.id:04d}"
        )
        await update.message.reply_text(reply, parse_mode=ParseMode.HTML)

    elif tipo == "consulta":
        await update.message.reply_text(
            "Pra consultas, usa um dos comandos:\n"
            "/total — total do mês\n"
            "/categorias — por categoria\n"
            "/recentes — últimos gastos"
        )

    elif tipo == "erro":
        logger.error(f"Erro no LLM: {data.get('motivo')}")
        await update.message.reply_text(
            "⚠️ Tive um problema pra processar. Tenta de novo em alguns segundos."
        )

    else:
        await update.message.reply_text(
            "🤔 Não entendi. Pra registrar um gasto manda algo como:\n"
            "<code>uber 27</code> ou <code>mercado 152,40</code>",
            parse_mode=ParseMode.HTML,
        )


# ------------------------- Bootstrap -------------------------

async def health(_request):
    """Endpoint de health check — o Render só pede que algo responda na porta HTTP."""
    return web.Response(text="FinBot is running")


async def start_web_server():
    """Sobe um servidor HTTP mínimo na porta exigida pelo Render (PORT env var)."""
    port = int(os.getenv("PORT", "10000"))
    app = web.Application()
    app.router.add_get("/", health)
    app.router.add_get("/health", health)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Servidor HTTP escutando na porta {port}")


async def run_bot():
    """Inicializa e roda o bot do Telegram via long polling."""
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_TOKEN não definido")

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler(["start", "ajuda", "help"], cmd_start))
    app.add_handler(CommandHandler("total", cmd_total))
    app.add_handler(CommandHandler("categorias", cmd_categorias))
    app.add_handler(CommandHandler("recentes", cmd_recentes))
    app.add_handler(CommandHandler("desfazer", cmd_desfazer))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot iniciado. Aguardando mensagens...")

    # initialize/start/updater são o ciclo manual quando rodamos junto com outra task asyncio
    await app.initialize()
    await app.start()
    await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)

    # Mantém rodando até receber sinal de parada
    stop_event = asyncio.Event()
    try:
        await stop_event.wait()
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


async def main_async():
    init_db()
    await start_web_server()
    await run_bot()


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
