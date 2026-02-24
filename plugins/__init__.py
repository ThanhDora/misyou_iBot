# ThanhDora | DoraTeam | https://github.com/ThanhDora | @DoraTeamMods
"""
Apache License 2.0
"""

__name__ = "Digital-Rename-Bot"
__version__ = "3.1.0"
__license__ = " Apache License, Version 2.0"
__copyright__ = "ThanhDora | <a href=https://github.com/ThanhDora>GitHub</a>"
__programer__ = "<a href=https://github.com/ThanhDora>ThanhDora</a>"
__library__ = "<a href=https://github.com/pyrogram>Pyʀᴏɢʀᴀᴍ</a>"
__language__ = "<a href=https://www.python.org/>Pyᴛʜᴏɴ 3</a>"
__database__ = "<a href=https://cloud.mongodb.com/>Mᴏɴɢᴏ DB</a>"
__developer__ = "<a href=https://t.me/DoraTeamMods>@DoraTeamMods</a>"
__maindeveloper__ = "<a href=https://github.com/ThanhDora>ThanhDora / DoraTeam</a>"

# main copyright herders (©️)
# I have been working on this repo since 2022


# main working files 
# - bot.py
# - web_support.py
# - plugins/
# - start_&_cb.py
# - Force_Sub.py
# - admin_panel.py
# - file_rename.py
# - metadata.py
# - prefix_&_suffix.py
# - thumb_&_cap.py
# - config.py
# - utils.py
# - database.py

# bot run files
# - bot.py
# - Procfile
# - Dockerfile
# - requirements.txt
# - runtime.txt

from plugins.force_sub import not_subscribed, forces_sub, handle_banned_user_status
from pyrogram import Client, filters
from config import Config
from helper.database import digital_botz
from helper.utils import send_pending_approval_notification

async def require_approved(_, client, update):
    if not getattr(Config, "APPROVAL_REQUIRED", False):
        return True
    user_id = getattr(update, "from_user", None) and update.from_user.id
    if not user_id:
        return False
    return await digital_botz.is_approved(user_id)

@Client.on_message(filters.private)
async def _(bot, message):
    await digital_botz.add_user(bot, message)
    if Config.APPROVAL_REQUIRED and not await digital_botz.is_approved(message.from_user.id):
        if message.text and message.text.strip().lower().startswith("/start"):
            await send_pending_approval_notification(bot, message.from_user)
        return await message.reply_text(
            "⏳ **Bạn chưa được duyệt.**\n\nAdmin cần duyệt tài khoản trước khi bạn dùng bot.\nVui lòng đợi hoặc liên hệ admin."
        )
    await handle_banned_user_status(bot, message)

@Client.on_message(filters.private & filters.sticker & filters.create(require_approved))
async def sticker_file_id_handler(bot, message):
    fid = message.sticker.file_id
    await message.reply_text(f"**LOADING_STICKER**\n\n`{fid}`\n\nMột sticker: copy vào .env\nNhiều sticker: gửi lần lượt từng sticker, copy từng id rồi ghép bằng dấu phẩy trong .env:\n`LOADING_STICKER=id1,id2,id3`")


@Client.on_message(filters.private & filters.create(not_subscribed) & filters.create(require_approved))
async def forces_sub_handler(bot, message):
    await forces_sub(bot, message)
