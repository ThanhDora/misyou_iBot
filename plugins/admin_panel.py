# ThanhDora | DoraTeam | https://github.com/ThanhDora | @DoraTeamMods
"""
Apache License 2.0
"""

# extra imports
from config import Config
from helper.database import digital_botz
from helper.utils import get_seconds, humanbytes
import os, sys, time, asyncio, logging, datetime, pytz, traceback

# pyrogram imports
from pyrogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram import Client, filters
from pyrogram.errors import FloodWait, InputUserDeactivated, UserIsBlocked, PeerIdInvalid


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


async def resolve_user(client, arg):
    arg = (arg or "").strip().lstrip("@")
    if not arg:
        return None, None
    try:
        uid = int(arg)
        user = await client.get_users(uid)
        return user.id, user
    except ValueError:
        try:
            user = await client.get_users(arg)
            return user.id, user
        except Exception:
            return None, None
    except Exception:
        return None, None


@Client.on_message(filters.command(["stats", "status"]) & filters.user(Config.ADMIN))
async def get_stats(bot, message):
    total_users = await digital_botz.total_users_count()
    if bot.premium:
        total_premium_users = await digital_botz.total_premium_users_count()
    else:
        total_premium_users = "Disabled ✅"
    uptime = time.strftime("%Hh%Mm%Ss", time.gmtime(time.time() - bot.uptime))    
    start_t = time.time()
    rkn = await message.reply('**ᴘʀᴏᴄᴇssɪɴɢ.....**')    
    end_t = time.time()
    time_taken_s = (end_t - start_t) * 1000
    await rkn.edit(text=f"{Config.E_STAT} <b>Bot Status</b>\n\n{Config.E_CALENDAR} Uptime: <code>{uptime}</code>\n{Config.E_STAT} Ping: <code>{time_taken_s:.3f} ms</code>\n{Config.E_USER} Total users: <code>{total_users}</code>\n{Config.E_MENU} Premium users: <code>{total_premium_users}</code>", parse_mode="html")

# bot logs process 
@Client.on_message(filters.command('logs') & filters.user(Config.ADMIN))
async def log_file(b, m):
    try:
        await m.reply_document('BotLog.txt')
    except Exception as e:
        await m.reply(str(e))

@Client.on_message(filters.command(["addpremium", "add_premium"]) & filters.user(Config.ADMIN))
async def add_premium(client, message):
    if not client.premium:
        return await message.reply_text("premium mode disabled ✅")
     
    if client.uploadlimit:
        if len(message.command) < 4:
            return await message.reply_text("Usage : /addpremium @username hoặc user_id Plan_Type time\n\nPlan: <code>VIP</code> | <code>Pro</code> | <code>UltraPro</code>\nTime: 1 day | 1 month | 1 year", quote=True)

        user_id, user = await resolve_user(client, message.command[1])
        if user_id is None:
            return await message.reply_text("Không tìm thấy user. Dùng @username hoặc user_id.", quote=True)
        plan_type = message.command[2]

        if plan_type not in ["VIP", "Pro", "UltraPro"]:
            return await message.reply_text("Invalid Plan. Use: VIP | Pro | UltraPro", quote=True)

        time_string = " ".join(message.command[3:])

        time_zone = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
        current_time = time_zone.strftime("%d-%m-%Y\n⏱️ ᴊᴏɪɴɪɴɢ ᴛɪᴍᴇ : %I:%M:%S %p")

        if plan_type == "VIP":
            limit = 53687091200
            type = "VIP"
        elif plan_type == "Pro":
            limit = 107374182400
            type = "Pro"
        elif plan_type == "UltraPro":
            limit = 1073741824000
            type = "UltraPro"

        seconds = await get_seconds(time_string)
        if seconds <= 0:
            return await message.reply_text("Invalid time format. Please use `/addpremium user_id 1 year 1 month 1 day 1 min 10 s`", quote=True)

        expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
        user_data = {"id": user_id, "expiry_time": expiry_time}
        try:
            await digital_botz.add_premium(user_id, user_data, limit, type)

            user_data = await digital_botz.get_user_data(user_id) or {}
            limit = user_data.get('uploadlimit', 0)
            type = user_data.get('usertype', "Free")
            data = await digital_botz.get_user(user_id) or {}
            expiry = data.get("expiry_time")
            if expiry is None:
                return await message.reply_text("Đã tạo user nhưng không đọc được hạn premium. Thử lại lệnh.", quote=True)
            expiry_str_in_ist = expiry.astimezone(pytz.timezone("Asia/Kolkata")).strftime("%d-%m-%Y\n⏱️ ᴇxᴘɪʀʏ ᴛɪᴍᴇ : %I:%M:%S %p")

            await message.reply_text(f"ᴘʀᴇᴍɪᴜᴍ ᴀᴅᴅᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ✅\n\n👤 ᴜꜱᴇʀ : {user.mention}\n⚡ ᴜꜱᴇʀ ɪᴅ : <code>{user_id}</code>\nᴘʟᴀɴ :- `{type}`\nᴅᴀɪʟʏ ᴜᴘʟᴏᴀᴅ ʟɪᴍɪᴛ :- `{humanbytes(limit)}`\n⏰ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇꜱꜱ : <code>{time_string}</code>\n\n⏳ ᴊᴏɪɴɪɴɢ ᴅᴀᴛᴇ : {current_time}\n\n⌛️ ᴇxᴘɪʀʏ ᴅᴀᴛᴇ : {expiry_str_in_ist}", quote=True, disable_web_page_preview=True)

            try:
                await client.send_message(
                        chat_id=user_id,
                        text=f"👋 ʜᴇʏ {user.mention},\nᴛʜᴀɴᴋ ʏᴏᴜ ꜰᴏʀ ᴘᴜʀᴄʜᴀꜱɪɴɢ ᴘʀᴇᴍɪᴜᴍ.\nᴇɴᴊᴏʏ !! ✨🎉\n\n⏰ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇꜱꜱ : <code>{time_string}</code>\nᴘʟᴀɴ :- `{type}`\nᴅᴀɪʟʏ ᴜᴘʟᴏᴀᴅ ʟɪᴍɪᴛ :- `{humanbytes(limit)}`\n⏳ ᴊᴏɪɴɪɴɢ ᴅᴀᴛᴇ : {current_time}\n\n⌛️ ᴇxᴘɪʀʏ ᴅᴀᴛᴇ : {expiry_str_in_ist}", disable_web_page_preview=True
                    )
            except Exception:
                await message.reply_text("Premium đã thêm, nhưng bot không gửi được tin nhắn cho user đó (chưa từng mở bot hoặc đã chặn bot).", quote=True)
        except Exception:
            traceback.print_exc()
            return await message.reply_text("Không thêm được premium. Kiểm tra lại user và thử lại.", quote=True)

    else:
        if len(message.command) < 3:
            return await message.reply_text("Usage : /addpremium @username hoặc user_id time\nVD: 1 day | 1 month | 1 year", quote=True)

        user_id, user = await resolve_user(client, message.command[1])
        if user_id is None:
            return await message.reply_text("Không tìm thấy user. Dùng @username hoặc user_id.", quote=True)
        time_string = " ".join(message.command[2:])

        time_zone = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
        current_time = time_zone.strftime("%d-%m-%Y\n⏱️ ᴊᴏɪɴɪɴɢ ᴛɪᴍᴇ : %I:%M:%S %p")        
        seconds = await get_seconds(time_string)
        if seconds <= 0:
            return await message.reply_text("Invalid time format. Please use `/addpremium user_id 1 year 1 month 1 day 1 min 10 s`", quote=True)

        expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
        user_data = {"id": user_id, "expiry_time": expiry_time}
        try:
            await digital_botz.add_premium(user_id, user_data)
            data = await digital_botz.get_user(user_id) or {}
            expiry = data.get("expiry_time")
            if expiry is None:
                return await message.reply_text("Đã tạo user nhưng không đọc được hạn premium. Thử lại lệnh.", quote=True)
            expiry_str_in_ist = expiry.astimezone(pytz.timezone("Asia/Kolkata")).strftime("%d-%m-%Y\n⏱️ ᴇxᴘɪʀʏ ᴛɪᴍᴇ : %I:%M:%S %p")

            await message.reply_text(f"ᴘʀᴇᴍɪᴜᴍ ᴀᴅᴅᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ✅\n\n👤 ᴜꜱᴇʀ : {user.mention}\n⚡ ᴜꜱᴇʀ ɪᴅ : <code>{user_id}</code>\n⏰ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇꜱꜱ : <code>{time_string}</code>\n\n⏳ ᴊᴏɪɴɪɴɢ ᴅᴀᴛᴇ : {current_time}\n\n⌛️ ᴇxᴘɪʀʏ ᴅᴀᴛᴇ : {expiry_str_in_ist}", quote=True, disable_web_page_preview=True)

            try:
                await client.send_message(
                        chat_id=user_id,
                        text=f"👋 ʜᴇʏ {user.mention},\nᴛʜᴀɴᴋ ʏᴏᴜ ꜰᴏʀ ᴘᴜʀᴄʜᴀꜱɪɴɢ ᴘʀᴇᴍɪᴜᴍ.\nᴇɴᴊᴏʏ !! ✨🎉\n\n⏰ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇꜱꜱ : <code>{time_string}</code>\n⏳ ᴊᴏɪɴɪɴɢ ᴅᴀᴛᴇ : {current_time}\n\n⌛️ ᴇxᴘɪʀʏ ᴅᴀᴛᴇ : {expiry_str_in_ist}", disable_web_page_preview=True
                    )
            except Exception:
                await message.reply_text("Premium đã thêm, nhưng bot không gửi được tin nhắn cho user đó (chưa từng mở bot hoặc đã chặn bot).", quote=True)
        except Exception:
            traceback.print_exc()
            return await message.reply_text("Không thêm được premium. Kiểm tra lại user và thử lại.", quote=True)
     

@Client.on_message(filters.command(["removepremium", "remove_premium"]) & filters.user(Config.ADMIN))
async def remove_premium(bot, message):
    if not bot.premium:
        return await message.reply_text("premium mode disabled ✅")
     
    if len(message.command) == 2:
        user_id, user = await resolve_user(bot, message.command[1])
        if user_id is None:
            return await message.reply_text("Không tìm thấy user. Dùng @username hoặc user_id.", quote=True)
        if await digital_botz.has_premium_access(user_id):
            await digital_botz.remove_premium(user_id)
            await message.reply_text(f"ʜᴇʏ {user.mention}, ᴘʀᴇᴍɪᴜᴍ ᴘʟᴀɴ sᴜᴄᴄᴇssғᴜʟʟʏ ʀᴇᴍᴏᴠᴇᴅ.", quote=True)
            await bot.send_message(chat_id=user_id, text=f"<b>ʜᴇʏ {user.mention},\n\n✨ ʏᴏᴜʀ ᴀᴄᴄᴏᴜɴᴛ ʜᴀs ʙᴇᴇɴ ʀᴇᴍᴏᴠᴇᴅ ᴛᴏ ᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ᴘʟᴀɴ\n\nᴄʜᴇᴄᴋ ʏᴏᴜʀ ᴘʟᴀɴ ʜᴇʀᴇ /myplan</b>")
        else:
            await message.reply_text("User không có premium hoặc không tìm thấy.", quote=True)
    else:
        await message.reply_text("Usage: /removepremium @username hoặc user_id", quote=True)


@Client.on_message(filters.command(["approve", "duyet"]) & filters.user(Config.ADMIN))
async def approve_user(client, message):
    if not getattr(Config, "APPROVAL_REQUIRED", False):
        return await message.reply_text("Tính năng duyệt user chưa bật. Thêm APPROVAL_REQUIRED=true vào .env", quote=True)
    if len(message.command) < 2:
        return await message.reply_text("Usage: /approve @username hoặc user_id", quote=True)
    user_id, user = await resolve_user(client, message.command[1])
    if user_id is None:
        return await message.reply_text("Không tìm thấy user.", quote=True)
    await digital_botz.set_approved(user_id, True)
    await message.reply_text(f"✅ Đã duyệt {user.mention} (`{user_id}`). User có thể dùng bot.", quote=True)
    try:
        await client.send_message(user_id, "✅ **Bạn đã được admin duyệt.** Bạn có thể dùng bot ngay.")
    except Exception:
        pass


@Client.on_message(filters.command(["unapprove", "hoduyet"]) & filters.user(Config.ADMIN))
async def unapprove_user(client, message):
    if not getattr(Config, "APPROVAL_REQUIRED", False):
        return await message.reply_text("Tính năng duyệt user chưa bật.", quote=True)
    if len(message.command) < 2:
        return await message.reply_text("Usage: /unapprove @username hoặc user_id", quote=True)
    user_id, user = await resolve_user(client, message.command[1])
    if user_id is None:
        return await message.reply_text("Không tìm thấy user.", quote=True)
    await digital_botz.set_approved(user_id, False)
    await message.reply_text(f"❌ Đã hủy duyệt {user.mention} (`{user_id}`).", quote=True)


@Client.on_message(filters.command(["pending", "choduyet"]) & filters.user(Config.ADMIN))
async def pending_users(client, message):
    if not getattr(Config, "APPROVAL_REQUIRED", False):
        return await message.reply_text("Tính năng duyệt user chưa bật.", quote=True)
    count = 0
    text = "**⏳ User chờ duyệt:**\n\n"
    async for u in digital_botz.get_pending_users():
        count += 1
        try:
            us = await client.get_users(u["_id"])
            text += f"• {us.mention} `{u['_id']}` — /approve `{u['_id']}`\n"
        except Exception:
            text += f"• `{u['_id']}` — /approve `{u['_id']}`\n"
        if count >= 50:
            text += "\n_... (tối đa 50)_"
            break
    if count == 0:
        text = "Không có user nào chờ duyệt."
    await message.reply_text(text, quote=True)


@Client.on_callback_query(filters.regex(r"^aprv_\d+$") & filters.user(Config.ADMIN))
async def cb_approve_pending(c: Client, q: CallbackQuery):
    if not getattr(Config, "APPROVAL_REQUIRED", False):
        return await q.answer("Tính năng duyệt chưa bật.", show_alert=True)
    uid = int(q.data.split("_", 1)[1])
    await digital_botz.set_approved(uid, True)
    try:
        await q.message.edit_text(
            q.message.text + "\n\n✅ **Đã duyệt bởi** " + (q.from_user.mention or str(q.from_user.id)),
            reply_markup=None
        )
    except Exception:
        pass
    await q.answer("Đã duyệt user.")
    try:
        await c.send_message(uid, "✅ **Bạn đã được admin duyệt.** Bạn có thể dùng bot ngay.")
    except Exception:
        pass


@Client.on_callback_query(filters.regex(r"^rej_\d+$") & filters.user(Config.ADMIN))
async def cb_reject_pending(c: Client, q: CallbackQuery):
    if not getattr(Config, "APPROVAL_REQUIRED", False):
        return await q.answer("Tính năng duyệt chưa bật.", show_alert=True)
    uid = int(q.data.split("_", 1)[1])
    await digital_botz.set_approved(uid, False)
    try:
        await q.message.edit_text(
            q.message.text + "\n\n❌ **Đã từ chối bởi** " + (q.from_user.mention or str(q.from_user.id)),
            reply_markup=None
        )
    except Exception:
        pass
    await q.answer("Đã từ chối.")
    try:
        await c.send_message(uid, "❌ **Admin đã từ chối yêu cầu.** Bạn không thể sử dụng bot.")
    except Exception:
        pass


# Restart to cancell all process 
@Client.on_message(filters.private & filters.command("restart") & filters.user(Config.ADMIN))
async def restart_bot(b, m):
    rkn = await b.send_message(text="**🔄 ᴘʀᴏᴄᴇssᴇs sᴛᴏᴘᴘᴇᴅ. ʙᴏᴛ ɪs ʀᴇsᴛᴀʀᴛɪɴɢ.....**", chat_id=m.chat.id)
    failed = 0
    success = 0
    deactivated = 0
    blocked = 0
    start_time = time.time()
    total_users = await digital_botz.total_users_count()
    all_users = await digital_botz.get_all_users()
    async for user in all_users:
        try:
            restart_msg = f"ʜᴇʏ, {(await b.get_users(user['_id'])).mention}\n\n**🔄 ᴘʀᴏᴄᴇssᴇs sᴛᴏᴘᴘᴇᴅ. ʙᴏᴛ ɪs ʀᴇsᴛᴀʀᴛɪɴɢ.....\n\n✅️ ʙᴏᴛ ɪs ʀᴇsᴛᴀʀᴛᴇᴅ. ɴᴏᴡ ʏᴏᴜ ᴄᴀɴ ᴜsᴇ ᴍᴇ.**"
            await b.send_message(user['_id'], restart_msg)
            success += 1
        except InputUserDeactivated:
            deactivated +=1
            await digital_botz.delete_user(user['_id'])
        except UserIsBlocked:
            blocked +=1
            await digital_botz.delete_user(user['_id'])
        except Exception as e:
            failed += 1
            await digital_botz.delete_user(user['_id'])
            print(e)
            pass
        try:
            await rkn.edit(f"<u>ʀᴇsᴛᴀʀᴛ ɪɴ ᴩʀᴏɢʀᴇꜱꜱ:</u>\n\n• ᴛᴏᴛᴀʟ ᴜsᴇʀs: {total_users}\n• sᴜᴄᴄᴇssғᴜʟ: {success}\n• ʙʟᴏᴄᴋᴇᴅ ᴜsᴇʀs: {blocked}\n• ᴅᴇʟᴇᴛᴇᴅ ᴀᴄᴄᴏᴜɴᴛs: {deactivated}\n• ᴜɴsᴜᴄᴄᴇssғᴜʟ: {failed}")
        except FloodWait as e:
            await asyncio.sleep(e.value)
    completed_restart = datetime.timedelta(seconds=int(time.time() - start_time))
    await rkn.edit(f"ᴄᴏᴍᴘʟᴇᴛᴇᴅ ʀᴇsᴛᴀʀᴛ: {completed_restart}\n\n• ᴛᴏᴛᴀʟ ᴜsᴇʀs: {total_users}\n• sᴜᴄᴄᴇssғᴜʟ: {success}\n• ʙʟᴏᴄᴋᴇᴅ ᴜsᴇʀs: {blocked}\n• ᴅᴇʟᴇᴛᴇᴅ ᴀᴄᴄᴏᴜɴᴛs: {deactivated}\n• ᴜɴsᴜᴄᴄᴇssғᴜʟ: {failed}")
    os.execl(sys.executable, sys.executable, *sys.argv)

@Client.on_message(filters.private & filters.command("ban") & filters.user(Config.ADMIN))
async def ban(c: Client, m: Message):
    if len(m.command) == 1:
        await m.reply_text(
            f"Usage: `/ban @username hoặc user_id ban_duration ban_reason`\n\n"
            f"VD: `/ban @user 28 Vi phạm` hoặc `/ban 1234567 28 Vi phạm`",
            quote=True
        )
        return

    try:
        if len(m.command) < 4:
            return await m.reply_text("Thiếu tham số. Dùng: /ban @username duration reason", quote=True)
        user_id, _ = await resolve_user(c, m.command[1])
        if user_id is None:
            return await m.reply_text("Không tìm thấy user. Dùng @username hoặc user_id.", quote=True)
        ban_duration = int(m.command[2])
        ban_reason = ' '.join(m.command[3:]) or "N/A"
        ban_log_text = f"Banning user {user_id} for {ban_duration} days for the reason {ban_reason}."
        try:
            await c.send_message(user_id,              
                f"You are banned to use this bot for **{ban_duration}** day(s) for the reason __{ban_reason}__ \n\n"
                f"**Message from the admin**"
            )
            ban_log_text += '\n\nUser notified successfully!'
        except:
            traceback.print_exc()
            ban_log_text += f"\n\nUser notification failed! \n\n`{traceback.format_exc()}`"

        await digital_botz.ban_user(user_id, ban_duration, ban_reason)
        await m.reply_text(ban_log_text, quote=True)
    except:
        traceback.print_exc()
        await m.reply_text(
            f"Error occoured! Traceback given below\n\n`{traceback.format_exc()}`",
            quote=True
        )


@Client.on_message(filters.private & filters.command(["deleteuser", "deluser", "xoaten"]) & filters.user(Config.ADMIN))
async def deleteuser(c: Client, m: Message):
    if len(m.command) < 2:
        await m.reply_text(
            "Usage: `/deleteuser @username` hoặc `/deleteuser user_id`\n\nXoá user khỏi bot; khi /start lại sẽ như user mới (cần duyệt nếu bật approval).",
            quote=True
        )
        return
    try:
        user_id, user = await resolve_user(c, m.command[1])
        if user_id is None:
            return await m.reply_text("Không tìm thấy user. Dùng @username hoặc user_id.", quote=True)
        await digital_botz.delete_user(user_id)
        name = (user and getattr(user, "first_name", None)) or user_id
        await m.reply_text(f"Đã xoá user {name} (id: {user_id}) khỏi bot. Khi /start lại sẽ như user mới.", quote=True)
    except Exception:
        traceback.print_exc()
        await m.reply_text(f"Lỗi: `{traceback.format_exc()}`", quote=True)


@Client.on_message(filters.private & filters.command("unban") & filters.user(Config.ADMIN))
async def unban(c: Client, m: Message):
    if len(m.command) == 1:
        await m.reply_text(
            f"Usage: `/unban @username hoặc user_id`\n\nVD: `/unban @user` hoặc `/unban 1234567`",
            quote=True
        )
        return

    try:
        user_id, _ = await resolve_user(c, m.command[1])
        if user_id is None:
            return await m.reply_text("Không tìm thấy user. Dùng @username hoặc user_id.", quote=True)
        unban_log_text = f"Unbanning user {user_id}"
        try:
            await c.send_message(user_id, f"Your ban was lifted!")
            unban_log_text += '\n\nUser notified successfully!'
        except:
            traceback.print_exc()
            unban_log_text += f"\n\nUser notification failed! \n\n`{traceback.format_exc()}`"
        await digital_botz.remove_ban(user_id)
        await m.reply_text(unban_log_text, quote=True)
    except:
        traceback.print_exc()
        await m.reply_text(
            f"Error occurred! Traceback given below\n\n`{traceback.format_exc()}`",
            quote=True
        )


@Client.on_message(filters.private & filters.command("banned_users") & filters.user(Config.ADMIN))
async def _banned_users(_, m: Message):
    all_banned_users = await digital_botz.get_all_banned_users()
    banned_usr_count = 0
    text = ''
    async for banned_user in all_banned_users:
        user_id = banned_user['id']
        ban_duration = banned_user['ban_status']['ban_duration']
        banned_on = banned_user['ban_status']['banned_on']
        ban_reason = banned_user['ban_status']['ban_reason']
        banned_usr_count += 1
        text += f"> **user_id**: `{user_id}`, **Ban Duration**: `{ban_duration}`, " \
                f"**Banned on**: `{banned_on}`, **Reason**: `{ban_reason}`\n\n"
    reply_text = f"Total banned user(s): `{banned_usr_count}`\n\n{text}"
    if len(reply_text) > 4096:
        with open('banned-users.txt', 'w') as f:
            f.write(reply_text)
        await m.reply_document('banned-users.txt', True)
        os.remove('banned-users.txt')
        return
    await m.reply_text(reply_text, True)

     
@Client.on_message(filters.command("broadcast") & filters.user(Config.ADMIN) & filters.reply)
async def broadcast_handler(bot: Client, m: Message):
    if Config.LOG_CHANNEL:
        await bot.send_message(Config.LOG_CHANNEL, f"{m.from_user.mention} or {m.from_user.id} Iꜱ ꜱᴛᴀʀᴛᴇᴅ ᴛʜᴇ Bʀᴏᴀᴅᴄᴀꜱᴛ......")
    all_users = await digital_botz.get_all_users()
    broadcast_msg = m.reply_to_message
    sts_msg = await m.reply_text("Bʀᴏᴀᴅᴄᴀꜱᴛ Sᴛᴀʀᴛᴇᴅ..!") 
    done = 0
    failed = 0
    success = 0
    start_time = time.time()
    total_users = await digital_botz.total_users_count()
    async for user in all_users:
        sts = await send_msg(user['_id'], broadcast_msg)
        if sts == 200:
           success += 1
        else:
           failed += 1
        if sts == 400:
           await digital_botz.delete_user(user['_id'])
        done += 1
        if not done % 20:
           await sts_msg.edit(f"Bʀᴏᴀᴅᴄᴀꜱᴛ Iɴ Pʀᴏɢʀᴇꜱꜱ: \nTᴏᴛᴀʟ Uꜱᴇʀꜱ {total_users} \nCᴏᴍᴩʟᴇᴛᴇᴅ: {done} / {total_users}\nSᴜᴄᴄᴇꜱꜱ: {success}\nFᴀɪʟᴇᴅ: {failed}")
    completed_in = datetime.timedelta(seconds=int(time.time() - start_time))
    await sts_msg.edit(f"Bʀᴏᴀᴅᴄᴀꜱᴛ Cᴏᴍᴩʟᴇᴛᴇᴅ: \nCᴏᴍᴩʟᴇᴛᴇᴅ Iɴ `{completed_in}`.\n\nTᴏᴛᴀʟ Uꜱᴇʀꜱ {total_users}\nCᴏᴍᴩʟᴇᴛᴇᴅ: {done} / {total_users}\nSᴜᴄᴄᴇꜱꜱ: {success}\nFᴀɪʟᴇᴅ: {failed}")
           
async def send_msg(user_id, message):
    try:
        await message.copy(chat_id=int(user_id))
        return 200
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return send_msg(user_id, message)
    except InputUserDeactivated:
        logger.info(f"{user_id} : Dᴇᴀᴄᴛɪᴠᴀᴛᴇᴅ")
        return 400
    except UserIsBlocked:
        logger.info(f"{user_id} : Bʟᴏᴄᴋᴇᴅ Tʜᴇ Bᴏᴛ")
        return 400
    except PeerIdInvalid:
        logger.info(f"{user_id} : Uꜱᴇʀ Iᴅ Iɴᴠᴀʟɪᴅ")
        return 400
    except Exception as e:
        logger.error(f"{user_id} : {e}")
        return 500
 

# ThanhDora | DoraTeam | @DoraTeamMods
