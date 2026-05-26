from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from db import fetch_all, fetch_one


def create_keyboard(buttons):
    return InlineKeyboardMarkup([[InlineKeyboardButton(text, callback_data=data)] for text, data in buttons])


def _parse_order_id(data: str) -> int:
    if data.startswith('order'):
        return int(data.replace('order', '', 1))
    return int(data.split(':', 1)[1])


async def verify_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    telegram_id = update.effective_user.id
    await query.answer()

    user = fetch_one("SELECT 1 FROM user_data_to_send WHERE user_id=?", (telegram_id,))
    if not user:
        await query.edit_message_text(
            """<b>Контактные данные</b> не обнаружены
Для просмотра заказа требуется ввод <b>контактных данных</b>""",
            reply_markup=create_keyboard([("📋 Контактные данные", 'contact_data'), ("📦 Заказы", 'orders')]),
            parse_mode="HTML",
        )
        return

    order_id = _parse_order_id(query.data)

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

    if not order_items:
        await query.edit_message_text(f"Заказ №{order_id} не найден.", reply_markup=create_keyboard([("📦 Заказы", 'orders')]))
        return

    items_text = ''
    total_sum = 0
    for i, (name, cost, _item_id, size, quantity) in enumerate(order_items, start=1):
        total_sum += cost * quantity
        items_text += f'<b>{i}. {name}</b> ({size}) ({cost} руб.) x {quantity}\n'

    order = fetch_one("SELECT order_status FROM orders_status WHERE order_id=?", (order_id,))
    if order:
        items_text += f'\nСтатус заказа: <b>{order[0]}</b>\n'

    items_text += f'\n<b>Итого:</b> {total_sum} рублей.'

    code_usage = fetch_one("SELECT code_usage FROM verify_codes WHERE order_id=?", (order_id,))
    if code_usage and code_usage[0]:
        keyboard = create_keyboard([
            ('🎉Покупка подтверждена!🎉', 'code_success'),
            ('❌ Удалить заказ', f'delete_ord{order_id}'),
            ('⬅️ Назад', 'orders'),
        ])
    else:
        keyboard = create_keyboard([
            ('✅ Подтвердить покупку', f'code_to_buy{order_id}'),
            ('❌ Удалить заказ', f'delete_ord{order_id}'),
            ('💰 Информация по оплате', 'payment_info'),
            ('⬅️ Назад', 'orders'),
        ])

    await query.edit_message_text(text=f"📦 Заказ <b>№{order_id}</b>:\n\n{items_text}", reply_markup=keyboard, parse_mode="HTML")
