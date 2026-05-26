import logging

from dotenv import load_dotenv
import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from db import execute, fetch_one
from items_for_user.add_to_basket import add_to_basket
from items_for_user.basket import basket
from items_for_user.delete_func import delete_func
from items_for_user.delete_order import delete_order
from items_for_user.items_db import items_db
from items_for_user.picture_of_Items import picture_of_item
from items_for_user.reAdd_to_basket import reAdd
from payment_info.payment_info import payment_info
from resources.resources import resources
from serveOrder.ready_message import assembly, delivered, ready_message, sent
from serveOrder.serveOrder import serveOrders
from toBuy_functions.buy import buy
from toBuy_functions.code_to_buy import cancel_code, recieve_code, start_to_buy
from toBuy_functions.order import orders
from toBuy_functions.verify_order import verify_order
from userData_to_send.change_mail import cancel_mail, change_mail, new_mail
from userData_to_send.data_to_send import cancel_contact, contact_data_user, data_to_send, start_to_contact


load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)

NAME, PASSWORD = range(2)
CODE, CONTACTS, MAIL = "codes", "contacts", "mail"


def create_keyboard(buttons):
    return InlineKeyboardMarkup([[InlineKeyboardButton(text, callback_data=data)] for text, data in buttons])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    user = fetch_one("SELECT ID FROM Users WHERE Telegram_ID=?", (telegram_id,))

    if user:
        text = 'Вход в личный кабинет SAMPE'
        keyboard = create_keyboard([("👤 Личный кабинет", "personal_cabinet"), ("🔗 Наши ресурсы", "resources")])
    else:
        text = 'Пожалуйста, зарегистрируйтесь'
        keyboard = create_keyboard([("👤 Регистрация", "register")])

    if update.message:
        await update.message.reply_text(text=text, reply_markup=keyboard)
    elif update.callback_query:
        await update.callback_query.edit_message_text(text=text, reply_markup=keyboard)


async def open_cabinet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    telegram_id = update.effective_user.id
    await query.answer()

    user = fetch_one("SELECT Name, Password FROM Users WHERE Telegram_ID=?", (telegram_id,))
    if not user:
        await query.edit_message_text(
            text="Пользователь не найден. Вернитесь для регистрации.",
            reply_markup=create_keyboard([("⬅️ Назад", 'back')]),
        )
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛍️ Товары", callback_data='items'), InlineKeyboardButton("🛒 Корзина", callback_data='basket')],
        [InlineKeyboardButton("📦 Заказы", callback_data='orders')],
        [InlineKeyboardButton("💰 Информация по оплате", callback_data='payment_info')],
        [InlineKeyboardButton("📋 Контактные данные", callback_data='contact_data')],
        [InlineKeyboardButton("✉ Изменить почту", callback_data='change_mail')],
        [InlineKeyboardButton("⬅️ Назад", callback_data='back')],
    ])

    await query.edit_message_text(
        text=f"<b>👤 Личный кабинет</b> @{update.effective_user.username}:\n\nИмя: {user[0]}\n✉ Почта: {user[1]}",
        parse_mode="HTML",
        reply_markup=keyboard,
    )


async def handle_register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    telegram_id = update.effective_user.id
    await query.answer()

    user = fetch_one("SELECT 1 FROM Users WHERE Telegram_ID=?", (telegram_id,))
    if user:
        await query.edit_message_text(text="Вы уже зарегистрированы. Войдите в личный кабинет.")
        return ConversationHandler.END

    await query.edit_message_text(text="Пожалуйста, введите свой никнейм:")
    return NAME


async def name_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text.strip()
    await update.message.reply_text("Пожалуйста, введите почту:")
    return PASSWORD


async def password_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = context.user_data['name']
    email = update.message.text.strip()
    execute(
        "INSERT INTO Users (Name, Password, Balance, Session_link, Telegram_ID) VALUES (?, ?, ?, ?, ?)",
        (name, email, 0, '', update.effective_user.id),
    )

    await update.message.reply_text("Регистрация успешна! Теперь вы можете войти в личный кабинет.")
    await start(update, context)
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Регистрация отменена.")
    return ConversationHandler.END


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get(CODE):
        await recieve_code(update, context)
    elif context.user_data.get(CONTACTS):
        await contact_data_user(update, context)
    elif context.user_data.get(MAIL):
        await new_mail(update, context)


async def noop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()


if __name__ == '__main__':
    application = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('cancel_code', cancel_code))
    application.add_handler(CommandHandler('cancel_contact', cancel_contact))
    application.add_handler(CommandHandler('cancel_mail', cancel_mail))

    application.add_handler(CallbackQueryHandler(open_cabinet, pattern=r'^(personal_cabinet|back_to_cabinet)$'))
    application.add_handler(CallbackQueryHandler(start, pattern=r'^back$'))

    application.add_handler(CallbackQueryHandler(items_db, pattern=r'^(items|items_page_\d+)$'))
    application.add_handler(CallbackQueryHandler(picture_of_item, pattern=r'^(for_pick_item\d+|product:\d+)$'))
    application.add_handler(CallbackQueryHandler(add_to_basket, pattern=r'^(for_sell_item\d+_[A-Za-z0-9]+|size:\d+:[A-Za-z0-9]+)$'))
    application.add_handler(CallbackQueryHandler(reAdd, pattern=r'^(reAdd\d+_[A-Za-z0-9]+|readd:\d+:[A-Za-z0-9]+)$'))

    application.add_handler(CallbackQueryHandler(basket, pattern=r'^basket$'))
    application.add_handler(CallbackQueryHandler(delete_func, pattern=r'^delete_func$'))
    application.add_handler(CallbackQueryHandler(buy, pattern=r'^buy$'))
    application.add_handler(CallbackQueryHandler(orders, pattern=r'^orders$'))
    application.add_handler(CallbackQueryHandler(verify_order, pattern=r'^(order\d+|verify_order:\d+)$'))
    application.add_handler(CallbackQueryHandler(start_to_buy, pattern=r'^(code_to_buy\d+|buy_code:\d+)$'))

    application.add_handler(CallbackQueryHandler(payment_info, pattern=r'^payment_info$'))
    application.add_handler(CallbackQueryHandler(data_to_send, pattern=r'^contact_data$'))
    application.add_handler(CallbackQueryHandler(start_to_contact, pattern=r'^start_to_contact$'))
    application.add_handler(CallbackQueryHandler(change_mail, pattern=r'^change_mail$'))
    application.add_handler(CallbackQueryHandler(resources, pattern=r'^resources$'))

    application.add_handler(CallbackQueryHandler(delete_order, pattern=r'^(delete_ord\d+|delete_order:\d+)$'))
    application.add_handler(CallbackQueryHandler(serveOrders, pattern=r'^serveOrder_'))
    application.add_handler(CallbackQueryHandler(ready_message, pattern=r'^change_status'))
    application.add_handler(CallbackQueryHandler(assembly, pattern=r'^assembly'))
    application.add_handler(CallbackQueryHandler(sent, pattern=r'^sent'))
    application.add_handler(CallbackQueryHandler(delivered, pattern=r'^delivered'))

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_register, pattern=r'^register$')],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name_input)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, password_input)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    application.add_handler(CallbackQueryHandler(noop, pattern=r'^noop$'))

    application.run_polling(drop_pending_updates=True)
