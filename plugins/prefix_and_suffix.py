# ThanhDora | Doratem | https://github.com/ThanhDora | @DoraTeamMods
"""
Apache License 2.0
"""

# imports
from pyrogram import Client, filters, enums
from helper.database import digital_botz
from plugins import require_approved

# prefix commond ✨
@Client.on_message(filters.private & filters.command('set_prefix') & filters.create(require_approved))
async def add_prefix(client, message):
    if len(message.command) == 1:
        return await message.reply_text("**__Give The Prefix__\n\nExᴀᴍᴩʟᴇ:- `/set_prefix @DoraTeamMods`**")
    prefix = message.text.split(" ", 1)[1]
    RknDev = await message.reply_text("Please Wait ...", reply_to_message_id=message.id)
    await digital_botz.set_prefix(message.from_user.id, prefix)
    await RknDev.edit("__**✅ ᴘʀᴇꜰɪx ꜱᴀᴠᴇᴅ**__")

@Client.on_message(filters.private & filters.command('del_prefix') & filters.create(require_approved))
async def delete_prefix(client, message):
    RknDev = await message.reply_text("Please Wait ...", reply_to_message_id=message.id)
    prefix = await digital_botz.get_prefix(message.from_user.id)
    if not prefix:
        return await RknDev.edit("__**😔 ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴀɴʏ ᴘʀᴇꜰɪx**__")
    await digital_botz.set_prefix(message.from_user.id, None)
    await RknDev.edit("__**❌️ ᴘʀᴇꜰɪx ᴅᴇʟᴇᴛᴇᴅ**__")

@Client.on_message(filters.private & filters.command('see_prefix') & filters.create(require_approved))
async def see_prefix(client, message):
    RknDev = await message.reply_text("Please Wait ...", reply_to_message_id=message.id)
    prefix = await digital_botz.get_prefix(message.from_user.id)
    if prefix:
        await RknDev.edit(f"**ʏᴏᴜʀ ᴘʀᴇꜰɪx:-**\n\n`{prefix}`")
    else:
        await RknDev.edit("__**😔 ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴀɴʏ ᴘʀᴇꜰɪx**__")

# SUFFIX COMMOND ✨
@Client.on_message(filters.private & filters.command('set_suffix') & filters.create(require_approved))
async def add_suffix(client, message):
    if len(message.command) == 1:
        return await message.reply_text("**__Give The Suffix__\n\nExᴀᴍᴩʟᴇ:- `/set_suffix @DoraTeamMods`**")
    suffix = message.text.split(" ", 1)[1]
    RknDev = await message.reply_text("Please Wait ...", reply_to_message_id=message.id)
    await digital_botz.set_suffix(message.from_user.id, suffix)
    await RknDev.edit("__**✅ ꜱᴜꜰꜰɪx ꜱᴀᴠᴇᴅ**__")

@Client.on_message(filters.private & filters.command('del_suffix') & filters.create(require_approved))
async def delete_suffix(client, message):
    RknDev = await message.reply_text("Please Wait ...", reply_to_message_id=message.id)
    suffix = await digital_botz.get_suffix(message.from_user.id)
    if not suffix:
        return await RknDev.edit("__**😔 ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴀɴʏ ꜱᴜꜰꜰɪx**__")
    await digital_botz.set_suffix(message.from_user.id, None)
    await RknDev.edit("__**❌️ ꜱᴜꜰꜰɪx ᴅᴇʟᴇᴛᴇᴅ**__")

@Client.on_message(filters.private & filters.command('see_suffix') & filters.create(require_approved))
async def see_suffix(client, message):
    RknDev = await message.reply_text("Please Wait ...", reply_to_message_id=message.id)
    suffix = await digital_botz.get_suffix(message.from_user.id)
    if suffix:
        await RknDev.edit(f"**ʏᴏᴜʀ ꜱᴜꜰꜰɪx:-**\n\n`{suffix}`")
    else:
        await RknDev.edit("__**😔 ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴀɴʏ ꜱᴜꜰꜰɪx**__")

# Rkn Developer 
# Don't Remove Credit 😔
# ThanhDora | Doratem | @DoraTeamMods
