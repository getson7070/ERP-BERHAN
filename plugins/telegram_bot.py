def register(app, register_plugin):
    try:
        from telegram import Update
        from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
    except Exception:
        return
    limits = {}
    links = {}

    async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
        uid = update.effective_user.id
        limits[uid] = limits.get(uid, 0) + 1
        if limits[uid] > 5:
            return
        await update.message.reply_text("pong")

    async def link(update: Update, context: ContextTypes.DEFAULT_TYPE):
        token = context.args[0] if context.args else ""
        if not token:
            await update.message.reply_text("token required")
            return
        links[update.effective_user.id] = token
        await update.message.reply_text("linked")

    async def run_bot():
        token = app.config.get("TELEGRAM_TOKEN")
        if not token:
            return
        application = ApplicationBuilder().token(token).build()
        application.add_handler(CommandHandler("ping", ping))
        application.add_handler(CommandHandler("link", link))
        application.run_polling()

    register_plugin("telegram_bot", jobs=[run_bot])
