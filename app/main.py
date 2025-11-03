from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ChatMemberHandler, filters, ContextTypes
from states import State, Home, Registration
from dotenv import load_dotenv
import os, mariadb, sys



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привіт!\n" \
        "В цьому боті ти можеш переглянути свої пропуски і історію чергувань\n" \
        "Якщо ти студент групи ІПЗ-3/1 і ще не зареєстрований - зроби це командою /register\n" \
        "Якщо ти вже зареєстрований напиши - /home"
    )



async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = Registration()
    context.chat_data["STATE"] = state
    next_state = await state.on_enter(update, context)
    while next_state is not None:
        state = next_state
        context.chat_data["STATE"] = state
        next_state: State = await state.on_enter(update, context)



async def home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = Home()
    context.chat_data["STATE"] = state
    next_state = await state.on_enter(update, context)
    while next_state is not None:
        state = next_state
        context.chat_data["STATE"] = state
        next_state = await state.on_enter(update, context)



async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "STATE" in context.chat_data:
        state: State = context.chat_data["STATE"]
        next_state: State = await state.on_message(update, context)
        while next_state is not None:
            state = next_state
            context.chat_data["STATE"] = state
            next_state: State = await state.on_enter(update, context)
    else:
        await update.message.reply_text("Щось пішло не так. Спробуй перейти на головну /home")



async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "STATE" in context.chat_data:
        state: State = context.chat_data["STATE"]
        next_state: State = await state.on_callback(update, context)
        while next_state is not None:
            state = next_state
            context.chat_data["STATE"] = state
            next_state: State = await state.on_enter(update, context)
    else:
        await context.bot.send_message(update.effective_chat.id, "Щось пішло не так. Спробуй перейти на головну /home")




if __name__ == "__main__":
    load_dotenv(os.getenv("ENV_FILE", ".env"))

    app = Application.builder().token(os.getenv("TOKEN")).build()

    app.add_handler(CommandHandler("home", home, filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler("register", register, filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler("start", start, filters.ChatType.PRIVATE))
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.run_polling()