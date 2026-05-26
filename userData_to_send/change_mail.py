from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from db import execute, fetch_one

NEW_MAIL = "mail"


def create_keyboard(buttons):
    return InlineKeyboardMarkup([[InlineKeyboardButton(text, callback_data=data)] for text, data in buttons])


async def change_mail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data[NEW_MAIL] = True
    await query.edit_message_text("Введите новую почту. Для отмены ввода - /cancel_mail")


async def new_mail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get(NEW_MAIL):
        telegram_id = update.effective_user.id
        execute("UPDATE Users SET Password=? WHERE Telegram_ID=?", (update.message.text.strip(), telegram_id))
        context.user_data[NEW_MAIL] = False
        mail = fetch_one("SELECT Password FROM Users WHERE Telegram_ID=?", (telegram_id,))
        await update.message.reply_text(f"Почта изменена на {mail[0] if mail else ''}", reply_markup=create_keyboard([("⬅️ Назад", 'back_to_cabinet')]))


async def cancel_mail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get(NEW_MAIL):
        context.user_data[NEW_MAIL] = False
        await update.message.reply_text("Процедура ввода новой почты отменена", reply_markup=create_keyboard([("⬅️ Назад", 'back_to_cabinet')]))
