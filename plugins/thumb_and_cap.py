# ThanhDora | Doratem | https://github.com/ThanhDora | @DoraTeamMods
"""
Apache License 2.0
"""

# imports
from pyrogram import Client, filters
from helper.database import digital_botz
from plugins import require_approved

@Client.on_message(filters.private & filters.command('set_caption') & filters.create(require_approved))
async def add_caption(client, message):
    rkn = await message.reply_text("__**ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ**__")
    if len(message.command) == 1:
       return await rkn.edit("**__Gɪᴠᴇ Tʜᴇ Cᴀᴩᴛɪᴏɴ__\n\nExᴀᴍᴩʟᴇ:- `/set_caption {filename}\n\n💾 Sɪᴢᴇ: {filesize}\n\n⏰ Dᴜʀᴀᴛɪᴏɴ: {duration}\n\nBy: @DoraTeamMods`**")
    caption = message.text.split(" ", 1)[1]
    await digital_botz.set_caption(message.from_user.id, caption=caption)
    await rkn.edit("__**✅ Cᴀᴩᴛɪᴏɴ Sᴀᴠᴇᴅ**__")
   
@Client.on_message(filters.private & filters.command(['del_caption', 'delete_caption', 'delcaption']) & filters.create(require_approved))
async def delete_caption(client, message):
    rkn = await message.reply_text("__**ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ**__")
    caption = await digital_botz.get_caption(message.from_user.id)  
    if not caption:
       return await rkn.edit("__**😔 Yᴏᴜ Dᴏɴ'ᴛ Hᴀᴠᴇ Aɴy Cᴀᴩᴛɪᴏɴ**__")
    await digital_botz.set_caption(message.from_user.id, caption=None)
    await rkn.edit("__**❌️ Cᴀᴩᴛɪᴏɴ Dᴇʟᴇᴛᴇᴅ**__")
                                       
@Client.on_message(filters.private & filters.command(['see_caption', 'view_caption']) & filters.create(require_approved))
async def see_caption(client, message):
    rkn = await message.reply_text("__**ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ**__")
    caption = await digital_botz.get_caption(message.from_user.id)  
    if caption:
       await rkn.edit(f"**Yᴏᴜ'ʀᴇ Cᴀᴩᴛɪᴏɴ:-**\n\n`{caption}`")
    else:
       await rkn.edit("__**😔 Yᴏᴜ Dᴏɴ'ᴛ Hᴀᴠᴇ Aɴy Cᴀᴩᴛɪᴏɴ**__")

@Client.on_message(filters.private & filters.command(['view_thumb', 'viewthumb']) & filters.create(require_approved))
async def viewthumb(client, message):
    rkn = await message.reply_text("__**ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ**__")
    thumb = await digital_botz.get_thumbnail(message.from_user.id)
    if thumb:
        await client.send_photo(chat_id=message.chat.id, photo=thumb)
        await rkn.delete()
    else:
        await rkn.edit("😔 __**Yᴏᴜ Dᴏɴ'ᴛ Hᴀᴠᴇ Aɴy Tʜᴜᴍʙɴᴀɪʟ**__") 
		
@Client.on_message(filters.private & filters.command(['del_thumb', 'delete_thumb', 'delthumb']) & filters.create(require_approved))
async def removethumb(client, message):
    rkn = await message.reply_text("__**ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ**__")
    thumb = await digital_botz.get_thumbnail(message.from_user.id)
    if thumb:
        await digital_botz.set_thumbnail(message.from_user.id, file_id=None)
        await rkn.edit("❌️ __**Tʜᴜᴍʙɴᴀɪʟ Dᴇʟᴇᴛᴇᴅ**__")
        return
    await rkn.edit("😔 __**Yᴏᴜ Dᴏɴ'ᴛ Hᴀᴠᴇ Aɴy Tʜᴜᴍʙɴᴀɪʟ**__")


@Client.on_message(filters.private & filters.photo & filters.create(require_approved))
async def addthumbs(client, message):
    rkn = await message.reply_text("__**ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ**__")
    await digital_botz.set_thumbnail(message.from_user.id, file_id=message.photo.file_id)                
    await rkn.edit("✅️ __**Tʜᴜᴍʙɴᴀɪʟ Sᴀᴠᴇᴅ**__")

# ThanhDora | Doratem | @DoraTeamMods
