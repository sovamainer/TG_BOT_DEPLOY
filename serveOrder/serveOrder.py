from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from db import fetch_all, fetch_one


def create_keyboard(buttons):
    return InlineKeyboardMarkup([[InlineKeyboardButton(text, callback_data=data)] for text, data in buttons])


async def serveOrders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    order_info = query.data.split('_')
    username = order_info[3]
    order_id = int(order_info[2])
    telegram_id = int(order_info[1])

    email = fetch_one("SELECT Password FROM Users WHERE Telegram_ID=?", (telegram_id,))
    confirm_code = fetch_one("SELECT code FROM verify_codes WHERE order_id=?", (order_id,))
    order_status = fetch_one("SELECT order_status FROM orders_status WHERE order_id=?", (order_id,))
    delivery_address = fetch_one("SELECT delivery_adress FROM user_data_to_send WHERE user_id=?", (telegram_id,))

    order_items = fetch_all(
        """
        SELECT i.Name, i.Cost, i.ID, i.Size, o.quantity
        FROM Orders o
        JOIN Items i ON i.ID = o.item_id
        WHERE o.user_id=? AND o.order_id=?
        ORDER BY i.Name, i.Size
        """,
        (telegram_id, order_id),
    )

    items_text = ''.join([f'<b>{i + 1}. {name}</b> ({size}) ({cost} руб.) x {quantity}\n' for i, (name, cost, _id, size, quantity) in enumerate(order_items)])

    keyboard = create_keyboard([("Изменить статус заказа", f'change_status{order_id}_{telegram_id}_{username}')])

    await query.edit_message_text(
        text=(
            f"Заказ№ <code>{order_id}</code> \nID пользователя: <code>{telegram_id}</code> \n"
            f"Почта: {email[0] if email else ''}\n"
            f"*Адрес доставки(СДЭК): <b>{delivery_address[0] if delivery_address else ''}</b>\n"
            f"Никнейм пользователя: @{username}\n"
            f"Код подтверждения заказа: <code>{confirm_code[0] if confirm_code else ''}</code>\n"
            f"Статус: <b>Заказ подтвержден</b>\n"
            f"Статус заказа пользователя:\n<b>{order_status[0] if order_status else ''}</b>\n"
            f"Товары:\n{items_text}\n\n"
            f"* Адрес доставки <b>проверять по чеку</b>"
        ),
        parse_mode="HTML",
        reply_markup=keyboard,
    )
