from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dataclasses import dataclass
from datetime import datetime, date
import os
from dotenv import load_dotenv
from states import State, Home


load_dotenv()
TOKEN = os.getenv("TOKEN")



async def HandleStart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = Home()
    await state.OnEnter(update, context)
    context.chat_data["STATE"] = state



async def HandleMessage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "STATE" in context.chat_data:
        state: State = context.chat_data["STATE"]
        next_state: State = await state.OnMessage(update, context)
        if next_state:
            await next_state.OnEnter(update, context)
            context.chat_data["STATE"] = next_state
    else:
        state = Home()
        await state.OnEnter(update, context)
        context.chat_data["STATE"] = state



if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", HandleStart, filters.ChatType.PRIVATE))
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE, HandleMessage))
    app.run_polling()