import random

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from db import execute, execute_many, fetch_all, fetch_one


def create_keyboard(buttons):
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(text, callback_data=data)] for text, data in buttons]
    )


def generate_confirmation_code():
    return ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789', k=12))


def generate_order_id() -> str:
    while True:
        order_id = ''.join(random.choices('0123456789', k=7))
        if not fetch_one("SELECT 1 FROM Orders WHERE order_id=?", (order_id,)):
            return order_id


async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    telegram_id = update.effective_user.id

    await query.answer()

    basket_items = fetch_all(
        """
        SELECT item_id, quantity, Size
        FROM Basket
        WHERE user_id=?
        """,
        (telegram_id,),
    )

    if not basket_items:
        await query.edit_message_text(
            text="Корзина пуста.",
            reply_markup=create_keyboard([
                ("🛒 Корзина", "basket"),
                ("⬅️ Назад", "back_to_cabinet"),
            ]),
        )
        return

    user_orders_count_row = fetch_one(
        "SELECT COUNT(DISTINCT order_id) FROM Orders WHERE user_id=?",
        (telegram_id,),
    )
    user_orders_count = user_orders_count_row[0] if user_orders_count_row else 0

    keyboard = create_keyboard([("📦 Заказы", "orders"), ("⬅️ Назад", "back_to_cabinet")])

    if user_orders_count >= 5:
        await query.edit_message_text(text="Превышен лимит заказов.", reply_markup=keyboard)
        return

    confirm_code = generate_confirmation_code()
    order_id = generate_order_id()

    order_rows = [(telegram_id, item_id, quantity, order_id, size) for item_id, quantity, size in basket_items]
    execute_many(
        "INSERT INTO Orders (user_id, item_id, quantity, order_id, Size) VALUES (?, ?, ?, ?, ?)",
        order_rows,
    )
    execute("INSERT INTO verify_codes (order_id, code, code_usage) VALUES (?, ?, ?)", (order_id, confirm_code, 0))
    execute("DELETE FROM Basket WHERE user_id=?", (telegram_id,))

    email_row = fetch_one("SELECT Password FROM Users WHERE Telegram_ID=?", (telegram_id,))
    email = email_row[0] if email_row else ''

    await query.edit_message_text(text="Обработка заказа...")
    await context.bot.send_message(
        chat_id=telegram_id,
        text="""Ваш заказ сформирован!

В данный момент вам требуется оплатить заказ для дальнейшего оформления.

Для оплаты вам требуется перевести нужную сумму по данным реквизитам:
2200700928791788 - Михаил Ф.

После оплаты <b>вам нужно отправить номер заказа администратору @smpadmn</b> вместе с <b>приложенным чеком об оплате</b>. После проверки поступления суммы <b>вам будет отправлен индивидуальный код</b>, который вы должны будете написать в этот чат.

После этого вы получите сообщение с информацией на какой стадии ваш заказ. В дальнейшем, в течении <b>двух суток</b> вам будет выслан трек номер СДЕК, по которому вы сможете отслеживать свой заказ.

<b>Если возникли какие либо вопросы, обращайтесь к нашему администратору: @smpadmn</b>""",
        parse_mode="HTML",
    )
    await context.bot.send_message(
        chat_id=telegram_id,
        text=f"Товары сформированы в Заказ №{order_id}\n\n*Для дальнейшего оформления заказа перейдите в раздел «заказы» на главной странице",
        reply_markup=keyboard,
    )
    await context.bot.send_message(
        chat_id=993256762,
        text=f"Заказ№ <code>{order_id}</code> \nID пользователя: <code>{telegram_id}</code> \nПочта: {email}\nНикнейм пользователя: @{update.effective_user.username}\nКод подтверждения заказа: <code>{confirm_code}</code>",
        parse_mode="HTML",
    )