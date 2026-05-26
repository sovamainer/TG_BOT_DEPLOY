from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from db import execute, fetch_one

DATA_TO_SEND_PROGRESS = 'contacts'


def create_keyboard(buttons):
    return InlineKeyboardMarkup([[InlineKeyboardButton(text, callback_data=data)] for text, data in buttons])


async def data_to_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    telegram_id = update.effective_user.id
    await query.answer()

    user = fetch_one("SELECT * FROM user_data_to_send WHERE user_id=?", (telegram_id,))

    if user:
        text_for_user_data = ['Регион', 'Город', 'Улица', 'Дом', 'Квартира', 'ФИО', 'Телефон', 'Почтовый индекс', 'Ссылка на вас', 'Адрес доставки(СДЭК)']
        text = ''.join([f'<b>{label}</b>: {value}\n' for label, value in zip(text_for_user_data, user[1:])])
        await query.edit_message_text(
            f"<b>📋 Ваши контактные данные:</b>\n\n{text}",
            reply_markup=create_keyboard([('Изменить контактные данные', 'start_to_contact'), ('⬅️ Назад', 'back_to_cabinet')]),
            disable_web_page_preview=True,
            parse_mode="HTML",
        )
    else:
        await query.edit_message_text(
            '''
<b>📋 Заполнение контактной информации для отправки заказа!</b>

Каждый пункт важен и <b>требует внимательного заполнения</b>, иначе могут возникнуть <b>проблемы</b> в процессе отправки товара!

<b>Для удобства заполнения просто скопируйте форму заказа, удалив данные, которые являются примером, и отправьте нам обратно:</b>

Республика / край / область / итп - Московская область
Город / поселок / итп - Москва
Улица – Столешников переулок
Дом - 8
Квартира - 27
ФИО - Соколова Анна Александрова
Телефон - +71234567890
Индекс – 111111 ( для почты России) 
Ссылка на вас - для обратной связи
Адрес доставки - указывайте адрес ближайшего к вам СДЭК

- Если вам будет удобен какой-то конкретный пункт выдачи заказов в вашем населенном пункте, сообщите @smpadmn.''',
            reply_markup=create_keyboard([('Ввести контактные данные', 'start_to_contact'), ('⬅️ Назад', 'back_to_cabinet')]),
            parse_mode="HTML",
        )


async def start_to_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    telegram_id = update.effective_user.id
    await query.answer()

    if fetch_one("SELECT 1 FROM user_data_to_send WHERE user_id=?", (telegram_id,)):
        execute("DELETE FROM user_data_to_send WHERE user_id=?", (telegram_id,))

    context.user_data[DATA_TO_SEND_PROGRESS] = True
    await query.edit_message_text("⬇ Форма записи контактных данных ⬇")

    await context.bot.send_message(chat_id=telegram_id, text="""Регион
Город
Улица
Дом
Квартира
ФИО
Телефон
Почтовый индекс
Ссылка на вас
Адрес доставки(СДЭК)""")

    await context.bot.send_message(
        chat_id=telegram_id,
        text="""Введите контактные данные в сообщение по данному ниже примеру:
    
Регион
Город
Улица - необязательно(символ "-")
Дом(номер) - необязательно(символ "-")
Квартира(номер) - необязательно(символ "-")
ФИО
Телефон
Почтовый индекс
Ссылка на вас
Адрес доставки(СДЭК)

<b>Для удобства скопируйте форму ввода в <i>сообщении выше</i> и замените на свои данные.\n\nКаждое поле должно быть на отдельной строке.</b>

Или введите /cancel_contact для отмены ввода контактных данных

<b><i>Пример заполнения на фото ниже</i></b>""",
        parse_mode="HTML",
    )

    with open("pictures/photo_5273779897854195336_y.jpg", "rb") as photo:
        await context.bot.send_photo(chat_id=telegram_id, photo=photo, caption="Пример заполнения")


async def contact_data_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get(DATA_TO_SEND_PROGRESS):
        telegram_id = update.effective_user.id
        text = [line.rstrip() for line in update.message.text.split("\n")]

        if len(text) == 10:
            execute(
                """INSERT INTO user_data_to_send (user_id, region, city, street, home, apartment, fullName, phone, city_index, tg, delivery_adress) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (telegram_id, *text),
            )
            context.user_data[DATA_TO_SEND_PROGRESS] = False
            await update.message.reply_text("Ваши данные успешно заполнены!", reply_markup=create_keyboard([("⬅️ Назад", 'back_to_cabinet')]))
        else:
            await update.message.reply_text('Некорректный ввод / Недостаточно данных\n\nПопробуйте снова или введите /cancel_contact для отмены ввода контактных данных')


async def cancel_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get(DATA_TO_SEND_PROGRESS):
        context.user_data[DATA_TO_SEND_PROGRESS] = False
        await update.message.reply_text("Процедура ввода контактных данных отменена", reply_markup=create_keyboard([("⬅️ Назад", 'back_to_cabinet')]))
