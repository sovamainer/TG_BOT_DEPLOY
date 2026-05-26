from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from db import execute, fetch_one


def create_keyboard(buttons):
    return InlineKeyboardMarkup([[InlineKeyboardButton(text, callback_data=data)] for text, data in buttons])


def _parse_status_callback(data: str):
    payload = data.split('change_status', 1)[1]
    order_id, telegram_id, username = payload.split('_', 2)
    return order_id, telegram_id, username


def _update_status(order_id: int, status: str):
    execute("UPDATE orders_status SET order_status=? WHERE order_id=?", (status, order_id))
    row = fetch_one("SELECT order_status FROM orders_status WHERE order_id=?", (order_id,))
    return row[0] if row else status


async def ready_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    order_id, telegram_id, username = _parse_status_callback(query.data)
    order_status = fetch_one("SELECT order_status FROM orders_status WHERE order_id=?", (order_id,))

    await query.edit_message_text(
        text=f"Изменить статус заказа:\n\n<b>Заказ№ <code>{order_id}</code></b>\nТекущий статус: <b>{order_status[0] if order_status else ''}</b>",
        parse_mode="HTML",
        reply_markup=create_keyboard([
            ("📥 Сборка", f'assembly{order_id}_{telegram_id}_{username}'),
            ("➡ Отправлен на адрес доставки", f'sent{order_id}_{telegram_id}_{username}'),
            ("✅ Доставлено", f'delivered{order_id}_{telegram_id}_{username}'),
        ]),
    )


async def assembly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    order_id, telegram_id, username = query.data.replace('assembly', '', 1).split('_', 2)
    order_status = _update_status(int(order_id), "📥 Сборка")

    back_keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data=f"serveOrder_{telegram_id}_{order_id}_{username}")]]

    await context.bot.send_message(chat_id=telegram_id, text=f"Статус заказа№ <code>{order_id}</code> изменен:\n\nТекущий статус: <b>{order_status}</b>", reply_markup=create_keyboard([("📦 Заказы", 'orders')]), parse_mode="HTML")
    await query.edit_message_text(text=f"Статус заказа№ <code>{order_id}</code> изменен:\n\nТекущий статус: <b>{order_status}</b>", reply_markup=InlineKeyboardMarkup(back_keyboard), parse_mode="HTML")


async def sent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    order_id, telegram_id, username = query.data.replace('sent', '', 1).split('_', 2)
    order_status = _update_status(int(order_id), "➡ Отправлен на адрес доставки")

    back_keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data=f"serveOrder_{telegram_id}_{order_id}_{username}")]]

    await context.bot.send_message(chat_id=telegram_id, text=f"Статус заказа№ <code>{order_id}</code> изменен:\n\nТекущий статус: <b>{order_status}</b>", reply_markup=create_keyboard([("📦 Заказы", 'orders')]), parse_mode="HTML")
    await query.edit_message_text(text=f"Статус заказа№ <code>{order_id}</code> изменен:\n\nТекущий статус: <b>{order_status}</b>", reply_markup=InlineKeyboardMarkup(back_keyboard), parse_mode="HTML")


async def delivered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    order_id, telegram_id, username = query.data.replace('delivered', '', 1).split('_', 2)
    order_status = _update_status(int(order_id), "✅ Доставлено")

    back_keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data=f"serveOrder_{telegram_id}_{order_id}_{username}")]]

    await context.bot.send_message(chat_id=telegram_id, text=f"Статус заказа№ <code>{order_id}</code> изменен:\n\nТекущий статус: <b>{order_status}</b>", reply_markup=create_keyboard([("📦 Заказы", 'orders')]), parse_mode="HTML")
    await query.edit_message_text(text=f"Статус заказа№ <code>{order_id}</code> изменен:\n\nТекущий статус: <b>{order_status}</b>", reply_markup=InlineKeyboardMarkup(back_keyboard), parse_mode="HTML")
