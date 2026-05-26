from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from db import execute


def create_keyboard(buttons):
    return InlineKeyboardMarkup([[InlineKeyboardButton(text, callback_data=data)] for text, data in buttons])


async def delete_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    order_id = int(query.data.replace("delete_ord", "").replace("delete_order:", ""))

    execute("DELETE FROM Orders WHERE order_id=?", (order_id,))
    execute("DELETE FROM orders_status WHERE order_id=?", (order_id,))
    execute("DELETE FROM verify_codes WHERE order_id=?", (order_id,))

    await query.edit_message_text(f'Заказ №{order_id} удален!', reply_markup=create_keyboard([("📦 Заказы", 'orders')]))
