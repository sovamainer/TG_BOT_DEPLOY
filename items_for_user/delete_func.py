from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from db import execute


def create_keyboard(buttons):
    return InlineKeyboardMarkup([[InlineKeyboardButton(text, callback_data=data)] for text, data in buttons])


async def delete_func(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    telegram_id = update.effective_user.id
    await query.answer()

    execute("DELETE FROM Basket WHERE user_id=?", (telegram_id,))

    await query.edit_message_text(text="Корзина успешно очищена!", reply_markup=create_keyboard([("⬅️ Назад", 'back_to_cabinet')]))
