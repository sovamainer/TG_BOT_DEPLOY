from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from db import fetch_all


def create_keyboard(buttons):
    return InlineKeyboardMarkup([[InlineKeyboardButton(text, callback_data=data)] for text, data in buttons])


async def orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    telegram_id = update.effective_user.id
    await query.answer()

    order_rows = fetch_all("SELECT DISTINCT order_id FROM Orders WHERE user_id=? ORDER BY order_id DESC", (telegram_id,))

    keyboard = [[InlineKeyboardButton(f"Заказ №{order_id}", callback_data=f"order{order_id}")] for (order_id,) in order_rows]
    keyboard.append([InlineKeyboardButton("📋 Контактные данные", callback_data='contact_data')])
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_cabinet")])

    await query.edit_message_text(
        """<b>📦 Ваши заказы:</b>

Перед оплатой <b>обязательно заполните и перепроверьте контактные данные!</b>

*<b>не удаляйте</b> свои заказы если вы <b>не получили товар на руки</b>, чтобы не было путаницы в дальнейшем!""",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML',
    )
