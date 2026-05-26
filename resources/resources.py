from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes


async def resources(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [[InlineKeyboardButton("🗨️ SAMPE.NS", url="https://t.me/SAMPESHOP")],
                [InlineKeyboardButton("Instagram",
                                      url="https://www.instagram.com/sampe.shop?igsh=MTJxMzMybW1tbHVpNg==")],
                [InlineKeyboardButton("Новостной аккаунт",
                                      url="https://www.instagram.com/sampe.ns?igsh=c3h3aTVxeTVtdGx3")],
                [InlineKeyboardButton("⬅️ Назад", callback_data='back')]]

    await query.edit_message_text("🔗 Наши ресурсы\n", reply_markup=InlineKeyboardMarkup(keyboard))
