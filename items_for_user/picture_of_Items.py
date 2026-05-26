import os
import re

from dotenv import load_dotenv

import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ContextTypes

from db import fetch_all, fetch_one


load_dotenv()

REPO_OWNER = "sovamainer"
REPO_NAME = "TG_BOT_DEPLOY"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

ITEM_MEDIA = {
    1: {
        "title": "T-shirt SAMPLEOFALL",
        "product": "pictures/photo_5202035136349201100_y.jpg",
        "extra": "pictures/photo_5305266492079729520_y.jpg",
    },
    2: {
        "title": "T-shirt PastFuture",
        "product": "pictures/photo_5202035136349201101_y.jpg",
        "extra": "pictures/photo_5305266492079729520_y.jpg",
    },
    3: {
        "title": "T-shirt AllWillBeFine",
        "product": "pictures/photo_5202035136349201102_y.jpg",
        "extra": "pictures/photo_5305266492079729520_y.jpg",
    },
}


def _keyboard(buttons):
    return InlineKeyboardMarkup([[InlineKeyboardButton(text, callback_data=data)] for text, data in buttons])


def _extract_item_id(data: str) -> int:
    match = re.search(r'(?:for_pick_item|product:)(\d+)', data)
    if not match:
        raise ValueError(f'Bad callback data: {data}')
    return int(match.group(1))


def _resolve_download_url(path: str) -> str | None:
    url = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{path}'
    headers = {'Accept': 'application/vnd.github+json'}
    if GITHUB_TOKEN:
        headers['Authorization'] = f'Bearer {GITHUB_TOKEN}'

    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code == 200:
        payload = response.json()
        return payload.get('download_url')
    return None


async def picture_of_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    telegram_id = update.effective_user.id
    await query.answer()

    pic_item = _extract_item_id(query.data)
    row = fetch_one("SELECT Name FROM Items WHERE ID=?", (pic_item,))
    if not row:
        await query.edit_message_text(text="Товар не найден.", reply_markup=_keyboard([("⬅️ Назад", 'items')]))
        return

    name = row[0]
    sizes = fetch_all("SELECT ID, Size, Count, Cost FROM Items WHERE Name=? ORDER BY ID", (name,))

    keyboard = []
    for _item_id, size, count, _cost in sizes:
        if count > 0:
            keyboard.append([InlineKeyboardButton(f'Купить {size} ({count})', callback_data=f'for_sell_item{pic_item}_{size}')])

    if not keyboard:
        keyboard.append([InlineKeyboardButton('Нет в наличии', callback_data='noop')])

    keyboard.append([InlineKeyboardButton('⬅️ Назад', callback_data='items')])

    item_info = ITEM_MEDIA.get(pic_item, {"title": name, "product": None, "extra": None})

    await query.edit_message_text(text=f"<b>SAMPE DROP - {item_info['title']}</b>", parse_mode='HTML')

    photo_1 = _resolve_download_url(item_info['product']) if item_info['product'] else None
    photo_2 = _resolve_download_url(item_info['extra']) if item_info['extra'] else None

    media = []
    if photo_1:
        media.append(
            InputMediaPhoto(
                media=photo_1,
                caption=(
                    f"<b>SAMPE DROP - {item_info['title']}</b>\n\n"
                    f"Состав – 80% хлопок, 20% - полиэстер\n"
                    f"Плотность – 240 грамм\n"
                    f"Лого – шелкография"
                ),
                parse_mode='HTML',
            )
        )
    if photo_2:
        media.append(InputMediaPhoto(media=photo_2))

    if media:
        if len(media) == 1:
            await context.bot.send_photo(chat_id=telegram_id, photo=media[0].media, caption=media[0].caption, parse_mode='HTML')
        else:
            await context.bot.send_media_group(chat_id=telegram_id, media=media)

    await context.bot.send_message(
        chat_id=telegram_id,
        text=f"<b>SAMPE DROP - {item_info['title']}</b>",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
