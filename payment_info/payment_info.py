from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes


def create_keyboard(buttons):
    return InlineKeyboardMarkup([[InlineKeyboardButton(text, callback_data=data)] for text, data in buttons])


async def payment_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        text='''
    💰 Инструкция по оплате!

Для того чтобы оплатить заказ вам нужно перевести указанную сумму по реквизитам:
2200700928791788 - Михаил Ф.

После оплаты <b>вам нужно отправить номер заказа администратору @smpadmn</b> вместе с <b>приложенным чеком об оплате</b>. После проверки поступления суммы <b>вам будет отправлен индивидуальный код</b>, который вы должны будете написать в чат с ботом после нажатия кнопки 
"✅ Подтвердить покупку".

После этого вы получите сообщение с информацией на какой стадии ваш заказ. В дальнейшем, в течении <b>двух суток</b> вам будет выслан трек номер СДЕК, по которому вы сможете отслеживать свой заказ.

<b>Если возникли какие либо вопросы, обращайтесь к нашему администратору: @smpadmn</b>

❗️❗️❗
УДАЛЯЙТЕ ЗАКАЗ ТОЛЬКО В ТОМ СЛУЧАЕ, ЕСЛИ ОН ЕЩЕ НЕ ОПЛАЧЕН, ЛИБО ЗАКАЗ ОПЛАЧЕН И ПЕРЕДАН В РУКИ
❗️❗️❗️

Спасибо что поддерживаете нас и покупаете нашу продукцию!)''',
        reply_markup=create_keyboard([("📦 Заказы", 'orders'), ('⬅️ Назад', 'back_to_cabinet')]),
        parse_mode="HTML",
    )
