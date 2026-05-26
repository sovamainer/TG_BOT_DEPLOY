import re

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from db import execute, fetch_one


def create_keyboard(buttons):
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(text, callback_data=data)] for text, data in buttons]
    )


def _parse_callback(data: str):
    payload = data.replace('reAdd', '', 1)
    item_id, item_size = payload.split('_', 1)
    return int(item_id), item_size


async def reAdd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    telegram_id = update.effective_user.id

    await query.answer()

    item_id, item_size = _parse_callback(query.data)

    basket_row = fetch_one(
        """
        SELECT quantity
        FROM Basket
        WHERE user_id=? AND item_id=? AND Size=?
        """,
        (telegram_id, item_id, item_size),
    )

    if not basket_row:
        await query.edit_message_text(
            text="Товар не найден в корзине.",
            reply_markup=create_keyboard([
                ("🛒 Корзина", "basket"),
                ("🛍️ Товары", "items"),
                ("⬅️ Назад", "back_to_cabinet"),
            ]),
        )
        return

    quantity = basket_row[0]

    count_row = fetch_one(
        "SELECT Count FROM Items WHERE ID=?",
        (item_id,),
    )

    if not count_row:
        await query.edit_message_text(
            text="Товар отсутствует на складе.",
            reply_markup=create_keyboard([
                ("🛍️ Товары", "items"),
                ("⬅️ Назад", "back_to_cabinet"),
            ]),
        )
        return

    count_item = count_row[0]

    if quantity >= count_item:
        await query.edit_message_text(
            text="Превышено количество имеющегося товара.",
            reply_markup=create_keyboard([
                ("🛒 Корзина", "basket"),
                ("🛍️ Товары", "items"),
                ("⬅️ Назад", "back_to_cabinet"),
            ]),
        )
        return

    execute(
        """
        UPDATE Basket
        SET quantity = quantity + 1
        WHERE user_id=? AND item_id=? AND Size=?
        """,
        (telegram_id, item_id, item_size),
    )

    new_quantity = fetch_one(
        """
        SELECT quantity
        FROM Basket
        WHERE user_id=? AND item_id=? AND Size=?
        """,
        (telegram_id, item_id, item_size),
    )[0]

    await query.edit_message_text(
        text=f"Количество товара увеличено.\n\n"
             f"Теперь в корзине: {new_quantity} шт.",
        reply_markup=create_keyboard([
            ("➕ Добавить еще раз", f"reAdd{item_id}_{item_size}"),
            ("🛒 Корзина", "basket"),
            ("🛍️ Товары", "items"),
            ("⬅️ Назад", "back_to_cabinet"),
        ]),
    )