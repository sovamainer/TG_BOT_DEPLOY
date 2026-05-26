from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from db import fetch_all


def create_keyboard(buttons):
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(text, callback_data=data)] for text, data in buttons]
    )


async def basket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    telegram_id = update.effective_user.id

    await query.answer()

    items = fetch_all(
        """
        SELECT i.Name, i.Cost, i.ID, i.Size, b.quantity
        FROM Basket b
        JOIN Items i ON i.ID = b.item_id
        WHERE b.user_id=?
        ORDER BY i.Name, i.Size
        """,
        (telegram_id,),
    )

    if not items:
        await query.edit_message_text(
            text="Корзина пуста.",
            reply_markup=create_keyboard([
                ("⬅️ Назад", "back_to_cabinet")
            ]),
        )
        return

    total_sum = sum(cost * quantity for _, cost, _, _, quantity in items)

    items_text = ""

    for i, (name, cost, item_id, size, quantity) in enumerate(items, start=1):
        items_text += (
            f"<b>{i}</b>. <b>{name}</b>\n"
            f"Размер: {size}\n"
            f"Количество: {quantity}\n"
            f"Цена: {cost} руб.\n\n"
        )

    keyboard = create_keyboard([
        (f"💳 Купить ({total_sum} руб.)", "buy"),
        ("🗑️ Очистить корзину", "delete_func"),
        ("⬅️ Назад", "back_to_cabinet"),
    ])

    await query.edit_message_text(
        text=f"🛒 Корзина:\n\n{items_text}",
        parse_mode="HTML",
        reply_markup=keyboard,
    )