import re

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from db import execute, fetch_one


def create_keyboard(buttons):
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(text, callback_data=data)] for text, data in buttons]
    )


def _parse_callback(data: str) -> tuple[int, str]:
    if data.startswith('for_sell_item'):
        payload = data.replace('for_sell_item', '', 1)
        item_id, item_size = payload.split('_', 1)
        return int(item_id), item_size

    match = re.match(r'size:(\d+):(.+)', data)
    if not match:
        raise ValueError(f'Bad callback data: {data}')
    return int(match.group(1)), match.group(2)


async def add_to_basket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    telegram_id = update.effective_user.id
    await query.answer()

    source_item_id, item_size = _parse_callback(query.data)

    item_row = fetch_one(
        """
        SELECT ID, Count
        FROM Items
        WHERE Name = (SELECT Name FROM Items WHERE ID=?)
          AND Size=?
        """,
        (source_item_id, item_size),
    )

    if not item_row:
        await query.edit_message_text(
            text="Товар не найден.",
            reply_markup=create_keyboard(
                [("🛍️ Товары", "items"), ("⬅️ Назад", "back_to_cabinet")]
            ),
        )
        return

    item_id, count_item = item_row

    basket_row = fetch_one(
        "SELECT quantity FROM Basket WHERE user_id=? AND item_id=? AND Size=?",
        (telegram_id, item_id, item_size),
    )

    if basket_row:
        quantity = basket_row[0]
        if quantity < count_item:
            execute(
                "UPDATE Basket SET quantity = quantity + 1 WHERE user_id=? AND item_id=? AND Size=?",
                (telegram_id, item_id, item_size),
            )
            await query.edit_message_text(
                text="Товар успешно добавлен в корзину.",
                reply_markup=create_keyboard(
                    [
                        ("➕ Добавить еще раз", f"reAdd{item_id}_{item_size}"),
                        ("🛒 Корзина", "basket"),
                        ("🛍️ Товары", "items"),
                        ("⬅️ Назад", "back_to_cabinet"),
                    ]
                ),
            )
        else:
            await query.edit_message_text(
                text="Превышено количество имеющегося товара.",
                reply_markup=create_keyboard(
                    [
                        ("🛒 Корзина", "basket"),
                        ("🛍️ Товары", "items"),
                        ("⬅️ Назад", "back_to_cabinet"),
                    ]
                ),
            )
    else:
        if count_item > 0:
            execute(
                "INSERT INTO Basket (user_id, item_id, quantity, Size) VALUES (?, ?, 1, ?)",
                (telegram_id, item_id, item_size),
            )
            await query.edit_message_text(
                text="Товар успешно добавлен в корзину.\n\n*Для дальнейшего оформления заказа перейдите в раздел «корзина»",
                reply_markup=create_keyboard(
                    [
                        ("➕ Добавить еще раз", f"reAdd{item_id}_{item_size}"),
                        ("🛒 Корзина", "basket"),
                        ("🛍️ Товары", "items"),
                        ("⬅️ Назад", "back_to_cabinet"),
                    ]
                ),
            )
        else:
            await query.edit_message_text(
                text="Товара нет на складе.",
                reply_markup=create_keyboard(
                    [
                        ("🛒 Корзина", "basket"),
                        ("🛍️ Товары", "items"),
                        ("⬅️ Назад", "back_to_cabinet"),
                    ]
                ),
            )