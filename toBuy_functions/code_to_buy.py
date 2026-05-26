import os
from time import localtime, strftime

import pdfkit
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from db import execute, fetch_all, fetch_one

CONFIRMATION_PROGRESS = 'codes'


def create_keyboard(buttons):
    return InlineKeyboardMarkup([[InlineKeyboardButton(text, callback_data=data)] for text, data in buttons])


def _wkhtmltopdf_config():
    wkhtmltopdf_path = os.getenv('WKHTMLTOPDF_PATH', r'wkhtmltopdf/bin/wkhtmltopdf.exe')
    if os.path.exists(wkhtmltopdf_path):
        return pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
    return None


async def start_to_buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    order_id = int(query.data.replace("code_to_buy", "").replace("buy_code:", ""))
    code = fetch_one("SELECT order_id, code, code_usage FROM verify_codes WHERE order_id=?", (order_id,))
    if not code:
        await query.edit_message_text("Код подтверждения не найден.")
        return

    context.user_data['order_id'] = code[0]
    context.user_data[CONFIRMATION_PROGRESS] = True
    context.user_data['code'] = code[1]

    await query.edit_message_text("Введите код или отмените подтверждение с помощью /cancel_code")


async def recieve_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get(CONFIRMATION_PROGRESS):
        return

    user_input = update.message.text.strip()
    telegram_id = update.effective_user.id
    username = update.effective_user.username or 'unknown'
    print(user_input)

    if user_input != context.user_data.get('code'):
        await update.message.reply_text('Неверный код, попробуйте еще раз или введите /cancel_code, чтобы отменить ввод')
        return

    context.user_data[CONFIRMATION_PROGRESS] = False
    order_id = context.user_data.get('order_id')

    execute("UPDATE verify_codes SET code_usage=1 WHERE order_id=?", (order_id,))
    execute("INSERT OR IGNORE INTO orders_status (order_id, order_status) VALUES (?, ?)", (order_id, "🔄 В обработке"))

    items = fetch_all("SELECT item_id, quantity FROM Orders WHERE order_id=?", (order_id,))
    for item_id, quantity in items:
        execute(
            """
            UPDATE Items
            SET Count = CASE
                WHEN Count - ? < 0 THEN 0
                ELSE Count - ?
            END
            WHERE ID=?
            """,
            (quantity, quantity, item_id),
        )

    order_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Перейти к заказу", callback_data=f"serveOrder_{telegram_id}_{order_id}_{username}")]])
    await context.bot.send_message(chat_id=993256762, text=f'Заказ №{order_id} оплачен!', reply_markup=order_keyboard)

    user_name = fetch_one("SELECT fullName FROM user_data_to_send WHERE user_id=?", (telegram_id,))
    user_mail = fetch_one("SELECT Password FROM Users WHERE Telegram_id=?", (telegram_id,))
    phone = fetch_one("SELECT phone FROM user_data_to_send WHERE user_id=?", (telegram_id,))
    delivery = fetch_one("SELECT city, region, delivery_adress, city_index FROM user_data_to_send WHERE user_id=?", (telegram_id,))
    items_info = fetch_all("SELECT item_id, quantity, Size FROM Orders WHERE order_id=?", (order_id,))
    all_items = fetch_all("SELECT ID, Name, Cost FROM Items WHERE ID IN (SELECT item_id FROM Orders WHERE order_id=?)", (order_id,))

    file_text = '<b>ЧЕК ОПЛАТЫ</b>\n\n'
    cur_time = localtime()
    file_text += f'<b>Дата</b>: {strftime("%d.%m %Y", cur_time)} {strftime("%H:%M:%S", cur_time)}\n'
    file_text += f'<b>Номер заказа:</b> {order_id}\n\n'
    file_text += f'<b>Покупатель:</b> {user_name[0] if user_name else ""}\n'
    file_text += f'<b>Почта:</b> {user_mail[0] if user_mail else ""}\n'
    file_text += f'<b>Телефон:</b> {phone[0] if phone else ""}\n\n'
    if delivery:
        file_text += f'<b>Место доставки:</b> {delivery[0]}, {delivery[1]}, {delivery[2]}. <b>Индекс:</b> {delivery[3]}\n\n'
    file_text += f'<b>Товары:</b>\n'

    summary = {item_id: (name, cost) for item_id, name, cost in all_items}
    total = 0
    for item_id, quantity, size in items_info:
        name, cost = summary.get(item_id, ('Неизвестно', 0))
        file_text += f'<b>- {name}</b>\n'
        file_text += f'   Размер: {size}\n'
        file_text += f'   Количество: {quantity}\n'
        file_text += f'   Цена: {cost} руб.\n'
        file_text += f'   Общая стоимость: {quantity * cost} руб.\n\n'
        total += quantity * cost

    file_text += f'\n<b>Итого к оплате:</b> {total} руб.\n\n'
    file_text += '<b>Благодарим за покупку!</b>\n'
    file_text += '<b>Добро пожаловать в мир SAMPE.</b>\n'
    file_text += '<b>WE ARE YOUR FRIENDS.</b>\n\n'
    file_text += '<b>По всем вопросам обращаться в Telegram: @smpadmn</b>'

    txt_name = f'@{username}_check_{order_id}.txt'
    html_name = f'@{username}_check_{order_id}.html'
    pdf_name = f'@{username}_check_{order_id}.pdf'

    with open(txt_name, 'w', encoding='utf-8') as file:
        file.write(file_text)

    with open(txt_name, 'r', encoding='utf-8') as file:
        content = file.read()
        html_content = f"""
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{pdf_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; font-size: 20px; width: 80%; margin: auto; }}
                .content {{ white-space: pre-wrap; }}
            </style>
        </head>
        <body>
            <div class="content">{content}</div>
        </body>
        </html>
        """

    with open(html_name, 'w', encoding='utf-8') as file:
        file.write(html_content)

    config = _wkhtmltopdf_config()
    if config is not None:
        pdfkit.from_file(html_name, pdf_name, configuration=config, options={'page-size': 'A5'})
        with open(pdf_name, 'rb') as file:
            await context.bot.send_document(chat_id=993256762, document=file, filename=pdf_name)
        with open(pdf_name, 'rb') as file:
            await context.bot.send_document(chat_id=telegram_id, document=file, filename=pdf_name)

    await context.bot.send_message(
        chat_id=telegram_id,
        text="""<b>Ваш чек об оплате!</b>

<b>Администратор:</b> @smpadmn

Для полной поддержки нас присоединяйтесь во все наши соц сети:
Наш новостной/исторический аккаунт <b>SAMPE\u200B.NS</b>: https://www.instagram.com/sampe.ns?igsh=c3h3aTVxeTVtdGx3
Наша страница в инстаграмме: https://www.instagram.com/sampe.shop?igsh=MTJxMzMybW1tbHVpNg==
Наш телеграмм: https://t.me/SAMPESHOP""",
        parse_mode="HTML",
    )

    await update.message.reply_text("Товар подтвержден. Чек приложен к сообщению", reply_markup=create_keyboard([("📦 Заказы", 'orders')]))

    for path in (pdf_name, html_name, txt_name):
        if os.path.exists(path):
            os.remove(path)


async def cancel_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get(CONFIRMATION_PROGRESS):
        context.user_data[CONFIRMATION_PROGRESS] = False
        await update.message.reply_text('Процедура ввода кода подтверждения отменена', reply_markup=create_keyboard([("📦 Заказы", 'orders')]))
