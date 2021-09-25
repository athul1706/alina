#(©)Codexbotz
import os
import asyncio
from pyrogram import Client, filters, __version__
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated

from bot import Bot
from config import ADMINS, FORCE_MSG, START_MSG, OWNER_ID, CUSTOM_CAPTION, DISABLE_CHANNEL_BUTTON
from helper_func import subscribed, encode, decode, get_messages
from database.support import users_info
from database.sql import add_user, query_msg


#=====================================================================================##



WAIT_MSG = """"<b>Processing ...</b>"""

REPLY_ERROR = """<code>Use this command as a replay to any telegram message with out any spaces.</code>"""


#=====================================================================================##


@Bot.on_message(filters.command('start') & filters.private & subscribed)
async def start_command(client: Client, message: Message):
    id = message.from_user.id
    user_name = '@' + message.from_user.username if message.from_user.username else None
    await add_user(id, user_name)
    text = message.text
    if len(text)>7:
        try:
            base64_string = text.split(" ", 1)[1]
        except:
            return
        string = await decode(base64_string)
        argument = string.split("-")
        if len(argument) == 3:
            try:
                start = int(int(argument[1]) / abs(client.db_channel.id))
                end = int(int(argument[2]) / abs(client.db_channel.id))
            except:
                return
            if start <= end:
                ids = range(start,end+1)
            else:
                ids = []
                i = start
                while True:
                    ids.append(i)
                    i -= 1
                    if i < end:
                        break
        elif len(argument) == 2:
            try:
                ids = [int(int(argument[1]) / abs(client.db_channel.id))]
            except:
                return
        temp_msg = await message.reply("Please wait...")
        try:
            messages = await get_messages(client, ids)
        except:
            await message.reply_text("Something went wrong..!")
            return
        await temp_msg.delete()

        for msg in messages:

            if bool(CUSTOM_CAPTION) & bool(msg.document):
                caption = CUSTOM_CAPTION.format(previouscaption = "" if not msg.caption else msg.caption.html, filename = msg.document.file_name)
            else:
                caption = "" if not msg.caption else msg.caption.html

            if DISABLE_CHANNEL_BUTTON:
                reply_markup = msg.reply_markup
            else:
                reply_markup = None

            try:
                await msg.copy(chat_id=message.from_user.id, caption = caption, parse_mode = 'html', reply_markup = reply_markup)
                await asyncio.sleep(0.5)
            except FloodWait as e:
                await asyncio.sleep(e.x)
                await msg.copy(chat_id=message.from_user.id, caption = caption, parse_mode = 'html', reply_markup = reply_markup)
            except:
                pass
        return
    else:
        reply_markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("✨ INFAME SERIES ✨", url="https://t.me/InfameSeries"),
                ]
            ]
        )
        await message.reply_text(
            text = START_MSG.format(
                first = message.from_user.first_name,
                last = message.from_user.last_name,
                username = None if not message.from_user.username else '@' + message.from_user.username,
                mention = message.from_user.mention,
                id = message.from_user.id
            ),
            reply_markup = reply_markup,
            disable_web_page_preview = True,
            quote = True
        )
        return

@Bot.on_message(filters.command('start') & filters.private)
async def not_joined(client: Client, message: Message):
    buttons = [
        [
            InlineKeyboardButton(
                "Join Channel",
                url = client.invitelink)
        ]
    ]
    try:
        buttons.append(
            [
                InlineKeyboardButton(
                    text = 'Try Again',
                    url = f"https://t.me/{client.username}?start={message.command[1]}"
                )
            ]
        )
    except IndexError:
        pass

    await message.reply(
        text = FORCE_MSG.format(
                first = message.from_user.first_name,
                last = message.from_user.last_name,
                username = None if not message.from_user.username else '@' + message.from_user.username,
                mention = message.from_user.mention,
                id = message.from_user.id
            ),
        reply_markup = InlineKeyboardMarkup(buttons),
        quote = True,
        disable_web_page_preview = True
    )

@Bot.on_message(filters.private & filters.command('users'))
async def subscribers_count(bot, m: Message):
    id = m.from_user.id
    if id not in ADMINS:
        return
    USERS_LIST = "<b>Total:</b>\n\nSubscribers - {}\nBlocked / Deleted - {}"
    msg = await m.reply_text(WAIT_MSG)
    messages = await users_info(bot)
    active = messages[0]
    blocked = messages[1]
    await m.delete()
    await msg.edit(USERS_LIST.format(active, blocked))


@Bot.on_message(filters.private & filters.command('send') & filters.user(ADMINS))
async def send_text(client: Bot, message: Message):
    id = message.from_user.id
    if id not in ADMINS:
        return
    if (" " not in message.text) and ("send" in message.text) and (message.reply_to_message is not None):
        query = await query_msg()
        for row in query:
            chat_id = int(row[0])
            try:
                await client.copy_message(
                    chat_id=chat_id,
                    from_chat_id=message.chat.id,
                    message_id=message.reply_to_message.message_id,
                    caption=message.caption,
                    reply_markup=message.reply_markup
                )
            except FloodWait as e:
                await asyncio.sleep(e.x)
            except Exception:
                pass
    else:
        msg = await message.reply_text(REPLY_ERROR)
        await asyncio.sleep(8)
        await msg.delete()
