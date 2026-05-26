import math
import re

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from db import fetch_all

PAGE_SIZE = 3


def create_keyboard(buttons):
    return InlineKeyboardMarkup([[InlineKeyboardButton(text, callback_data=data)] for text, data in buttons])


def _parse_page(data: str) -> int:
    if data == 'items':
        return 0
    match = re.match(r'items_page_(\d+)', data)
    return int(match.group(1)) if match else 0


async def items_db(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    page = _parse_page(query.data)
    items_all = fetch_all("SELECT MIN(ID) AS ID, Name, MIN(Cost) AS Cost FROM Items GROUP BY Name ORDER BY Name")

    if not items_all:
        await query.edit_message_text(
            text="Каталог пока пуст.",
            reply_markup=create_keyboard([("⬅️ Назад", 'back_to_cabinet')]),
        )
        return

    total_pages = max(1, math.ceil(len(items_all) / PAGE_SIZE))
    page = max(0, min(page, total_pages - 1))
    start = page * PAGE_SIZE
    page_items = items_all[start:start + PAGE_SIZE]

    items_text = '\n\n'.join([f'• {item[1]}, цена: {item[2]} ₽' for item in page_items])
    keyboard = [[InlineKeyboardButton(f"{item[1]} ({item[2]} ₽)", callback_data=f'for_pick_item{item[0]}')] for item in page_items]

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("⬅️", callback_data=f'items_page_{page - 1}'))
    nav_row.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data='noop'))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("➡️", callback_data=f'items_page_{page + 1}'))
    keyboard.append(nav_row)
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data='back_to_cabinet')])

    await query.edit_message_text(
        text=f"<b>🛍️ Каталог sampe\u200B.shop</b>\n\n{items_text}",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
