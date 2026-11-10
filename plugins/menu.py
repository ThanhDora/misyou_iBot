# ThanhDora | DoraTeam | https://github.com/ThanhDora | @DoraTeamMods
"""Button-driven menu, admin user lists, and pending-input capture."""

import datetime
import traceback

import pytz
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message

from config import Config, rkn
from helper.database import digital_botz
from helper.utils import get_seconds, humanbytes
from helper.menu_ui import (
    ABOUT, CANCEL, HELP, HOME, PAGE_SIZE,
    admin_markup, about_text, btn, cancel_markup, caption_markup,
    confirm_markup, get_pending, help_text, home_markup, home_text,
    is_admin, label_user, markup, metadata_markup, name_markup,
    nav_row, page_count, plan_choice_markup, pop_pending, set_pending,
    show, show_by_ids, thumb_markup, upgrade_markup,
    user_filter_active, user_filter_pending,
)
from plugins import require_approved
from plugins.admin_panel import resolve_user, send_msg

SAIGON = pytz.timezone("Asia/Saigon")


def _admin_only(query):
    if not is_admin(query.from_user.id):
        return False
    return True


async def _tg_map(client, ids):
    found = {}
    if not ids:
        return found
    try:
        users = await client.get_users(ids)
        if not isinstance(users, list):
            users = [users]
        for u in users:
            found[u.id] = u
    except Exception:
        for uid in ids:
            try:
                found[uid] = await client.get_users(uid)
            except Exception:
                found[uid] = None
    return found


async def _plan_line(user_id, user_doc, client):
    usertype = (user_doc or {}).get("usertype") or "Free"
    has_pre = False
    expiry = None
    if getattr(client, "premium", False):
        has_pre = await digital_botz.has_premium_access(user_id)
        data = await digital_botz.get_user(user_id) or {}
        expiry = data.get("expiry_time")
    if has_pre and expiry:
        exp = expiry
        if getattr(exp, "tzinfo", None) is None:
            exp = pytz.utc.localize(exp) if hasattr(pytz, "utc") else exp
        try:
            exp_s = expiry.astimezone(SAIGON).strftime("%d-%m-%Y %H:%M") if hasattr(expiry, "astimezone") else str(expiry)
        except Exception:
            exp_s = str(expiry)
        return f"{usertype} (đến {exp_s})"
    return usertype or "Free"


async def show_home(client, update):
    user = update.from_user
    await show(client, update, home_text(user.mention), home_markup(user.id, client))


# /start is registered in start_and_cb.py and calls show_home.

# ---------- callback router ----------
@Client.on_callback_query(filters.regex(r"^m:") & filters.create(require_approved), group=-1)
async def menu_callback(client, query: CallbackQuery):
    data = query.data or ""
    uid = query.from_user.id

    if data == CANCEL:
        pop_pending(uid)
        await show_home(client, query)
        return

    if data == HOME:
        pop_pending(uid)
        await show_home(client, query)
        return

    if data == HELP:
        await show(client, query, help_text(), markup([[btn("Quay lại", HOME)]]))
        return

    if data == ABOUT:
        await show(client, query, about_text(client), markup([[btn("Quay lại", HOME)]]))
        return

    if data == "m:thumb":
        await show(client, query, "Ảnh bìa\n\nXem, đặt hoặc xoá ảnh bìa hiện tại. Bạn cũng có thể gửi một ảnh bất kỳ để đặt ảnh bìa.", thumb_markup())
        return
    if data == "m:thumb:view":
        thumb = await digital_botz.get_thumbnail(uid)
        if not thumb:
            await query.answer("Bạn chưa có ảnh bìa.", show_alert=True)
            return
        try:
            await query.answer()
        except Exception:
            pass
        await client.send_photo(uid, thumb, caption="Ảnh bìa hiện tại.", reply_markup=markup([[btn("Quay lại", "m:thumb")]]))
        return
    if data == "m:thumb:set":
        set_pending(uid, "set_thumb", menu_msg_id=query.message.id)
        await show(client, query, "Gửi một ảnh để đặt làm ảnh bìa.", cancel_markup())
        return
    if data == "m:thumb:del":
        thumb = await digital_botz.get_thumbnail(uid)
        if not thumb:
            await query.answer("Bạn chưa có ảnh bìa.", show_alert=True)
            return
        await digital_botz.set_thumbnail(uid, file_id=None)
        await show(client, query, "Đã xoá ảnh bìa.", thumb_markup())
        return

    if data == "m:cap":
        await show(
            client, query,
            "Chú thích\n\nChú thích sẽ gắn vào file sau khi đổi tên.\nCó thể dùng: {filename}, {filesize}, {duration}.",
            caption_markup(),
        )
        return
    if data == "m:cap:view":
        caption = await digital_botz.get_caption(uid)
        text = f"Chú thích hiện tại:\n\n`{caption}`" if caption else "Bạn chưa đặt chú thích."
        await show(client, query, text, caption_markup())
        return
    if data == "m:cap:set":
        set_pending(uid, "set_caption", menu_msg_id=query.message.id)
        await show(client, query, "Gửi nội dung chú thích.\nVí dụ: {filename}\nDung lượng: {filesize}\nThời lượng: {duration}", cancel_markup())
        return
    if data == "m:cap:del":
        caption = await digital_botz.get_caption(uid)
        if not caption:
            await query.answer("Bạn chưa đặt chú thích.", show_alert=True)
            return
        await digital_botz.set_caption(uid, caption=None)
        await show(client, query, "Đã xoá chú thích.", caption_markup())
        return

    if data == "m:name":
        prefix = await digital_botz.get_prefix(uid)
        suffix = await digital_botz.get_suffix(uid)
        text = (
            "Tiền tố / Hậu tố\n\n"
            f"Tiền tố: `{prefix}`\n" if prefix else "Tiền tố / Hậu tố\n\nTiền tố: chưa đặt\n"
        )
        text += f"Hậu tố: `{suffix}`" if suffix else "Hậu tố: chưa đặt"
        await show(client, query, text, name_markup())
        return
    if data == "m:pre:view":
        prefix = await digital_botz.get_prefix(uid)
        text = f"Tiền tố hiện tại:\n\n`{prefix}`" if prefix else "Bạn chưa đặt tiền tố."
        await show(client, query, text, name_markup())
        return
    if data == "m:pre:set":
        set_pending(uid, "set_prefix", menu_msg_id=query.message.id)
        await show(client, query, "Gửi tiền tố sẽ thêm trước tên file.\nVí dụ: @DoraTeamMods", cancel_markup())
        return
    if data == "m:pre:del":
        prefix = await digital_botz.get_prefix(uid)
        if not prefix:
            await query.answer("Bạn chưa đặt tiền tố.", show_alert=True)
            return
        await digital_botz.set_prefix(uid, None)
        await show(client, query, "Đã xoá tiền tố.", name_markup())
        return
    if data == "m:suf:view":
        suffix = await digital_botz.get_suffix(uid)
        text = f"Hậu tố hiện tại:\n\n`{suffix}`" if suffix else "Bạn chưa đặt hậu tố."
        await show(client, query, text, name_markup())
        return
    if data == "m:suf:set":
        set_pending(uid, "set_suffix", menu_msg_id=query.message.id)
        await show(client, query, "Gửi hậu tố sẽ thêm sau tên file.\nVí dụ: @DoraTeamMods", cancel_markup())
        return
    if data == "m:suf:del":
        suffix = await digital_botz.get_suffix(uid)
        if not suffix:
            await query.answer("Bạn chưa đặt hậu tố.", show_alert=True)
            return
        await digital_botz.set_suffix(uid, None)
        await show(client, query, "Đã xoá hậu tố.", name_markup())
        return

    if data == "m:meta":
        enabled = bool(await digital_botz.get_metadata_mode(uid))
        code = await digital_botz.get_metadata_code(uid)
        state = "đang bật" if enabled else "đang tắt"
        text = f"Metadata ({state})\n\nMã hiện tại:\n`{code or 'chưa đặt'}`"
        await show(client, query, text, metadata_markup(enabled))
        return
    if data == "m:meta:tog":
        enabled = bool(await digital_botz.get_metadata_mode(uid))
        await digital_botz.set_metadata_mode(uid, bool_meta=not enabled)
        enabled = not enabled
        code = await digital_botz.get_metadata_code(uid)
        state = "đang bật" if enabled else "đang tắt"
        await show(client, query, f"Metadata ({state})\n\nMã hiện tại:\n`{code or 'chưa đặt'}`", metadata_markup(enabled))
        return
    if data == "m:meta:set":
        set_pending(uid, "set_metadata", menu_msg_id=query.message.id)
        await show(
            client, query,
            "Gửi mã metadata.\nVí dụ:\n`--change-title @DoraTeamMods`\n`--change-author @DoraTeamMods`",
            cancel_markup(),
        )
        return

    if data == "m:plan":
        await _show_my_plan(client, query)
        return

    if data == "m:upgrade":
        if not client.premium:
            await query.answer("Chế độ Premium đang tắt.", show_alert=True)
            return
        user = query.from_user
        upgrade_msg = rkn.UPGRADE_PLAN.format(user.mention) if client.uploadlimit else rkn.UPGRADE_PREMIUM.format(user.mention)
        trial = (not await digital_botz.has_premium_access(uid)) and (not await digital_botz.get_free_trial_status(uid))
        await show(client, query, upgrade_msg, upgrade_markup(with_trial=trial))
        return

    if data == "m:trial":
        if not client.premium:
            await query.answer("Chế độ Premium đang tắt.", show_alert=True)
            return
        if await digital_botz.get_free_trial_status(uid):
            await show(client, query, "Bạn đã dùng thử rồi. Vui lòng mua gói Premium.", upgrade_markup(False))
            return
        await digital_botz.give_free_trial(uid)
        await show(client, query, "Đã thêm dùng thử Premium 12 giờ.", upgrade_markup(False))
        return

    # ---- admin ----
    admin_prefixes = (
        "m:admin", "m:ad:", "m:u:", "m:ap:", "m:rj:", "m:pl:",
        "m:ban:", "m:unb:", "m:pr+", "m:pr-", "m:bcok:", "m:delu:",
    )
    if data == "m:admin" or data.startswith(admin_prefixes):
        if not _admin_only(query):
            return await query.answer("Bạn không có quyền.", show_alert=True)

    if data == "m:admin":
        pop_pending(uid)
        await show(client, query, "Menu quản trị\n\nChọn một mục bên dưới.", admin_markup())
        return

    if data.startswith("m:ad:users:"):
        page = int(data.split(":")[-1])
        await _show_users_list(client, query, page)
        return

    if data.startswith("m:ad:pend:"):
        page = int(data.split(":")[-1])
        await _show_pending_list(client, query, page)
        return

    if data == "m:ad:stats":
        await _show_stats(client, query)
        return

    if data == "m:ad:logs":
        try:
            await query.answer()
        except Exception:
            pass
        try:
            await client.send_document(uid, "BotLog.txt", caption="Nhật ký bot.")
        except Exception as e:
            await show(client, query, f"Không gửi được nhật ký: {e}", admin_markup())
        return

    if data == "m:ad:bc":
        set_pending(uid, "broadcast", menu_msg_id=query.message.id)
        await show(client, query, "Gửi tin nhắn cần phát (văn bản hoặc media). Nhấn Huỷ để thoát.", cancel_markup())
        return

    if data == "m:ad:addpre":
        if not client.premium:
            await query.answer("Chế độ Premium đang tắt.", show_alert=True)
            return
        set_pending(uid, "addpre_user", menu_msg_id=query.message.id)
        await show(client, query, "Gửi @username hoặc ID người dùng cần thêm Premium.", cancel_markup())
        return

    if data == "m:ad:rmpre":
        if not client.premium:
            await query.answer("Chế độ Premium đang tắt.", show_alert=True)
            return
        set_pending(uid, "rmpre_user", menu_msg_id=query.message.id)
        await show(client, query, "Gửi @username hoặc ID người dùng cần gỡ Premium.", cancel_markup())
        return

    if data.startswith("m:u:"):
        # m:u:{target}:{src}:{page}
        parts = data.split(":")
        target = int(parts[2])
        src = parts[3] if len(parts) > 3 else "u"
        page = int(parts[4]) if len(parts) > 4 else 0
        await _show_user_detail(client, query, target, src, page)
        return

    if data.startswith("m:ap:") or data.startswith("m:rj:"):
        # m:ap:{target}:{page}
        parts = data.split(":")
        target = int(parts[2])
        page = int(parts[3]) if len(parts) > 3 else 0
        approve = data.startswith("m:ap:")
        await digital_botz.set_approved(target, True if approve else False)
        try:
            if approve:
                await client.send_message(target, "Bạn đã được admin duyệt. Bạn có thể dùng bot ngay.")
            else:
                await client.send_message(target, "Admin đã từ chối yêu cầu. Bạn không thể sử dụng bot.")
        except Exception:
            pass
        await query.answer("Đã duyệt." if approve else "Đã từ chối.")
        await _show_pending_list(client, query, page)
        return

    if data.startswith("m:pl:"):
        # m:pl:{target}:VIP
        parts = data.split(":")
        target = int(parts[2])
        plan = parts[3]
        if plan not in ("VIP", "Pro", "UltraPro"):
            await query.answer("Gói không hợp lệ.", show_alert=True)
            return
        set_pending(uid, "addpre_time", target=target, plan=plan, menu_msg_id=query.message.id)
        await show(client, query, f"Đã chọn gói {plan}. Gửi thời hạn, ví dụ: 1 day, 1 month, 7 day.", cancel_markup())
        return

    if data.startswith("m:pr+:"):
        target = int(data.split(":")[2])
        src = data.split(":")[3] if len(data.split(":")) > 3 else "u"
        if client.uploadlimit:
            set_pending(uid, "addpre_plan_wait", target=target, src=src, menu_msg_id=query.message.id)
            await show(client, query, "Chọn gói Premium.", plan_choice_markup(target))
        else:
            set_pending(uid, "addpre_time", target=target, plan=None, menu_msg_id=query.message.id)
            await show(client, query, "Gửi thời hạn Premium, ví dụ: 1 day, 1 month.", cancel_markup())
        return

    if data.startswith("m:pr-:"):
        target = int(data.split(":")[2])
        src = data.split(":")[3] if len(data.split(":")) > 3 else "u"
        page = int(data.split(":")[4]) if len(data.split(":")) > 4 else 0
        if await digital_botz.has_premium_access(target):
            await digital_botz.remove_premium(target)
            try:
                await client.send_message(target, "Tài khoản của bạn đã được gỡ khỏi gói Premium.")
            except Exception:
                pass
            await query.answer("Đã gỡ Premium.")
        else:
            await query.answer("Người dùng không có Premium.", show_alert=True)
        await _show_user_detail(client, query, target, src, page)
        return

    if data.startswith("m:ban:"):
        target = int(data.split(":")[2])
        set_pending(uid, "ban_user", target=target, menu_msg_id=query.message.id, src="u", page=0)
        await show(client, query, "Gửi số ngày chặn và lý do.\nVí dụ: 7 Vi phạm nội quy", cancel_markup())
        return

    if data.startswith("m:unb:"):
        target = int(data.split(":")[2])
        src = data.split(":")[3] if len(data.split(":")) > 3 else "u"
        page = int(data.split(":")[4]) if len(data.split(":")) > 4 else 0
        await digital_botz.remove_ban(target)
        try:
            await client.send_message(target, "Lệnh chặn của bạn đã được gỡ.")
        except Exception:
            pass
        await query.answer("Đã bỏ chặn.")
        await _show_user_detail(client, query, target, src, page)
        return

    if data.startswith("m:bcok:"):
        # confirm broadcast: m:bcok:{chat}:{msg}
        parts = data.split(":")
        try:
            bchat = int(parts[2])
            bmsg = int(parts[3])
        except Exception:
            await query.answer("Không tìm thấy tin cần phát.", show_alert=True)
            return
        await _run_broadcast(client, query, bchat, bmsg)
        return

    if data.startswith("m:delu:"):
        target = int(data.split(":")[2])
        await digital_botz.delete_user(target)
        await show(client, query, f"Đã xoá user `{target}` khoi bot. Khi họ /start lại sẽ như người dùng mới.", admin_markup())
        return

    try:
        await query.answer()
    except Exception:
        pass


async def _show_my_plan(client, query):
    if not client.premium:
        await query.answer("Chế độ Premium đang tắt.", show_alert=True)
        return
    user_id = query.from_user.id
    mention = query.from_user.mention
    if await digital_botz.has_premium_access(user_id):
        data = await digital_botz.get_user(user_id) or {}
        expiry = data.get("expiry_time")
        if expiry is None:
            await show(client, query, "Không đọc được hạn Premium. Thử lại sau.", markup([[btn("Quay lại", HOME)]]))
            return
        time_left = expiry - datetime.datetime.now()
        text = f"Người dùng: {mention}\nID: `{user_id}`\n"
        if client.uploadlimit:
            await digital_botz.reset_uploadlimit_access(user_id)
            user_data = await digital_botz.get_user_data(user_id)
            limit = user_data.get("uploadlimit", 0)
            used = user_data.get("used_limit", 0)
            remain = int(limit) - int(used)
            typ = user_data.get("usertype", "Free")
            text += f"Gói: {typ}\nHạn mức ngày: {humanbytes(limit)}\nĐã dùng: {humanbytes(used)}\nCòn lại: {humanbytes(remain)}\n"
        text += f"Thời gian còn lại: {time_left}\nHết hạn: {expiry}"
        await show(client, query, text, markup([[btn("Quay lại", HOME)]]))
        return

    user_data = await digital_botz.get_user_data(user_id)
    if client.uploadlimit:
        limit = user_data.get("uploadlimit", 0)
        used = user_data.get("used_limit", 0)
        remain = int(limit) - int(used)
        typ = user_data.get("usertype", "Free")
        text = (
            f"Người dùng: {mention}\nID: `{user_id}`\n"
            f"Gói: {typ}\nHạn mức ngày: {humanbytes(limit)}\n"
            f"Đã dùng: {humanbytes(used)}\nCòn lại: {humanbytes(remain)}\n"
            "Bạn chưa có gói Premium. Nhấn Nâng cấp để xem các gói."
        )
    else:
        text = f"Người dùng: {mention}\nID: `{user_id}`\nBạn chưa có gói Premium. Nhấn Nâng cấp để xem các gói."
    await show(client, query, text, markup([[btn("Nâng cấp", "m:upgrade")], [btn("Quay lại", HOME)]]))


async def _show_users_list(client, query, page):
    query_doc = user_filter_active()
    total = await digital_botz.count_users_by(query_doc)
    pages = page_count(total)
    page = max(0, min(page, pages - 1))
    docs = await digital_botz.list_users_page(query_doc, skip=page * PAGE_SIZE, limit=PAGE_SIZE)
    ids = [int(d["_id"]) for d in docs]
    tg = await _tg_map(client, ids)
    lines = [f"Danh sách người dùng (trang {page + 1}/{pages})", f"Tổng: {total}", ""]
    rows = []
    if not docs:
        lines.append("Chưa có người dùng.")
    for d in docs:
        uid = int(d["_id"])
        u = tg.get(uid)
        plan = await _plan_line(uid, d, client)
        joined = d.get("join_date") or "không rõ"
        uname = f"@{u.username}" if u and u.username else "không có username"
        name = (u.first_name if u else None) or "Người dùng"
        lines.append(f"{name} ({uname})\nID: `{uid}` | Gói: {plan} | Tham gia: {joined}")
        rows.append([btn(label_user(u, uid), f"m:u:{uid}:u:{page}")])
    rows.extend(nav_row("m:ad:users:", page, pages, back="m:admin"))
    await show(client, query, "\n".join(lines), markup(rows))


async def _show_pending_list(client, query, page):
    if not getattr(Config, "APPROVAL_REQUIRED", False):
        await show(client, query, "Tính năng duyệt user chưa bật.", admin_markup())
        return
    query_doc = user_filter_pending()
    total = await digital_botz.count_users_by(query_doc)
    pages = page_count(total)
    page = max(0, min(page, pages - 1))
    docs = await digital_botz.list_users_page(query_doc, skip=page * PAGE_SIZE, limit=PAGE_SIZE)
    ids = [int(d["_id"]) for d in docs]
    tg = await _tg_map(client, ids)
    lines = [f"Yêu cầu chờ duyệt (trang {page + 1}/{pages})", f"Tổng: {total}", ""]
    rows = []
    if not docs:
        lines.append("Không có yêu cầu nào.")
    for d in docs:
        uid = int(d["_id"])
        u = tg.get(uid)
        uname = f"@{u.username}" if u and u.username else "không có username"
        name = (u.first_name if u else None) or "Người dùng"
        joined = d.get("join_date") or "không rõ"
        lines.append(f"{name} ({uname})\nID: `{uid}` | Tham gia: {joined}")
        lab = label_user(u, uid)
        rows.append([btn(lab, f"m:u:{uid}:p:{page}")])
        rows.append([btn("Duyệt", f"m:ap:{uid}:{page}"), btn("Từ chối", f"m:rj:{uid}:{page}")])
    rows.extend(nav_row("m:ad:pend:", page, pages, back="m:admin"))
    await show(client, query, "\n".join(lines), markup(rows))


async def _show_user_detail(client, query, target, src="u", page=0):
    doc = await digital_botz.col.find_one({"_id": int(target)})
    tg = (await _tg_map(client, [int(target)])).get(int(target))
    if not doc and not tg:
        await show(client, query, f"Không tìm thấy user `{target}`.", admin_markup())
        return
    name = (tg.first_name if tg else None) or "Người dùng"
    uname = f"@{tg.username}" if tg and tg.username else "không có"
    joined = (doc or {}).get("join_date") or "không rõ"
    plan = await _plan_line(target, doc or {}, client)
    approved = (doc or {}).get("approved", True)
    ban = await digital_botz.get_ban_status(target)
    banned = ban.get("is_banned") if ban else False
    used = humanbytes((doc or {}).get("used_limit") or 0)
    limit = humanbytes((doc or {}).get("uploadlimit") or 0)
    lines = [
        "Chi tiết người dùng",
        f"Tên: {name}",
        f"Username: {uname}",
        f"ID: `{target}`",
        f"Gói: {plan}",
        f"Tham gia: {joined}",
        f"Duyệt: {'đã duyệt' if approved else 'chờ duyệt'}",
        f"Chặn: {'đang bị chặn' if banned else 'không'}",
    ]
    if client.uploadlimit:
        lines.append(f"Đã dùng / hạn mức: {used} / {limit}")
    text = "\n".join(lines)
    back = f"m:ad:users:{page}" if src == "u" else f"m:ad:pend:{page}"
    rows = []
    if getattr(Config, "APPROVAL_REQUIRED", False):
        if not approved:
            rows.append([btn("Duyệt", f"m:ap:{target}:{page}"), btn("Từ chối", f"m:rj:{target}:{page}")])
    if client.premium:
        rows.append([btn("Thêm Premium", f"m:pr+:{target}:{src}"), btn("Gỡ Premium", f"m:pr-:{target}:{src}:{page}")])
    if banned:
        rows.append([btn("Bỏ chặn", f"m:unb:{target}:{src}:{page}")])
    else:
        rows.append([btn("Chặn", f"m:ban:{target}")])
    rows.append([btn("Xoá user", f"m:delu:{target}")])
    rows.append([btn("Quay lại", back)])
    await show(client, query, text, markup(rows))


async def _show_stats(client, query):
    total = await digital_botz.total_users_count()
    pending = await digital_botz.count_users_by(user_filter_pending()) if Config.APPROVAL_REQUIRED else 0
    premium = await digital_botz.total_premium_users_count() if client.premium else "đang tắt"
    uptime = datetime.timedelta(seconds=int(datetime.datetime.now().timestamp() - getattr(client, "uptime", 0)))
    text = (
        "Thống kê bot\n\n"
        f"Thời gian hoạt động: {uptime}\n"
        f"Tổng người dùng: {total}\n"
        f"Chờ duyệt: {pending}\n"
        f"Premium: {premium}"
    )
    await show(client, query, text, markup([[btn("Quay lại", "m:admin")]]))


async def _apply_premium(client, admin_update, target, user_obj, time_string, plan):
    seconds = await get_seconds(time_string)
    if seconds <= 0:
        return "Thời hạn không hợp lệ. Ví dụ: 1 day, 1 month, 7 day."
    expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
    user_data = {"id": target, "expiry_time": expiry_time}
    if client.uploadlimit and plan:
        if plan == "VIP":
            limit, typ = 53687091200, "VIP"
        elif plan == "Pro":
            limit, typ = 107374182400, "Pro"
        else:
            limit, typ = 1073741824000, "UltraPro"
        await digital_botz.add_premium(target, user_data, limit, typ)
    else:
        await digital_botz.add_premium(target, user_data)
        typ = plan or "Premium"
        limit = None
    mention = user_obj.mention if user_obj else f"`{target}`"
    try:
        exp = expiry_time.astimezone(SAIGON).strftime("%d-%m-%Y %H:%M")
    except Exception:
        exp = str(expiry_time)
    extra = f"\nGói: {typ}"
    if limit:
        extra += f"\nHạn mức ngày: {humanbytes(limit)}"
    text = f"Đã thêm Premium cho {mention}\nID: `{target}`{extra}\nThời hạn: {time_string}\nHết hạn: {exp} (Asia/Saigon)"
    try:
        await client.send_message(target, f"Bạn đã được thêm Premium.{extra}\nThời hạn: {time_string}\nHết hạn: {exp} (Asia/Saigon)")
    except Exception:
        text += "\n\nKhông gửi được tin nhắn cho user (chưa mở bot hoặc đã chặn bot)."
    return text


async def _run_broadcast(client, query, chat_id, msg_id):
    try:
        broadcast_msg = await client.get_messages(chat_id, msg_id)
    except Exception:
        await show(client, query, "Không lấy được tin nhắn để phát.", admin_markup())
        return
    await show(client, query, "Đang phát tin, vui lòng đợi...", markup([[btn("Quay lại", "m:admin")]]))
    all_users = await digital_botz.get_all_users()
    done = success = failed = 0
    total = await digital_botz.total_users_count()
    async for user in all_users:
        sts = await send_msg(user["_id"], broadcast_msg)
        if sts == 200:
            success += 1
        else:
            failed += 1
        if sts == 400:
            await digital_botz.delete_user(user["_id"])
        done += 1
    text = (
        f"Đã phát tin xong.\n\nTổng: {total}\nĐã gửi: {done}\nThành công: {success}\nThất bại: {failed}"
    )
    await show_by_ids(client, query.from_user.id, query.message.id, text, admin_markup())


# ---------- capture next message for button-driven prompts ----------
@Client.on_message(filters.private, group=-1)
async def capture_pending(client, message: Message):
    if not message.from_user:
        await message.continue_propagation()
        return
    uid = message.from_user.id
    # Let slash commands work as hidden fallbacks; drop the pending prompt.
    if message.text and message.text.startswith("/"):
        if get_pending(uid):
            pop_pending(uid)
        await message.continue_propagation()
        return
    pend = get_pending(uid)
    if not pend:
        await message.continue_propagation()
        return

    action = pend.get("action")
    mid = pend.get("menu_msg_id")

    async def reply_menu(text, keyboard):
        return await show_by_ids(client, uid, mid, text, keyboard)

    try:
        if action == "set_thumb":
            if not message.photo:
                await message.reply_text("Vui lòng gửi một ảnh, hoặc nhấn Huỷ.", reply_markup=cancel_markup())
                return
            await digital_botz.set_thumbnail(uid, file_id=message.photo.file_id)
            pop_pending(uid)
            await reply_menu("Đã lưu ảnh bìa.", thumb_markup())
            return

        if action == "set_caption":
            if not message.text:
                await message.reply_text("Vui lòng gửi văn bản chú thích, hoặc nhấn Huỷ.", reply_markup=cancel_markup())
                return
            await digital_botz.set_caption(uid, caption=message.text)
            pop_pending(uid)
            await reply_menu("Đã lưu chú thích.", caption_markup())
            return

        if action == "set_prefix":
            if not message.text:
                await message.reply_text("Vui lòng gửi tiền tố, hoặc nhấn Huỷ.", reply_markup=cancel_markup())
                return
            await digital_botz.set_prefix(uid, message.text)
            pop_pending(uid)
            await reply_menu("Đã lưu tiền tố.", name_markup())
            return

        if action == "set_suffix":
            if not message.text:
                await message.reply_text("Vui lòng gửi hậu tố, hoặc nhấn Huỷ.", reply_markup=cancel_markup())
                return
            await digital_botz.set_suffix(uid, message.text)
            pop_pending(uid)
            await reply_menu("Đã lưu hậu tố.", name_markup())
            return

        if action == "set_metadata":
            if not message.text:
                await message.reply_text("Vui lòng gửi mã metadata, hoặc nhấn Huỷ.", reply_markup=cancel_markup())
                return
            await digital_botz.set_metadata_code(uid, metadata_code=message.text)
            pop_pending(uid)
            enabled = bool(await digital_botz.get_metadata_mode(uid))
            await reply_menu(f"Đã lưu mã metadata.\n\n`{message.text}`", metadata_markup(enabled))
            return

        if action == "broadcast":
            if not is_admin(uid):
                pop_pending(uid)
                await message.continue_propagation()
                return
            pop_pending(uid)
            await message.reply_text(
                "Phát tin nhắn này đến tất cả người dùng?",
                quote=True,
                reply_markup=confirm_markup(f"m:bcok:{message.chat.id}:{message.id}", CANCEL),
            )
            return

        if action == "addpre_user":
            if not is_admin(uid) or not message.text:
                await message.reply_text("Gửi @username hoặc ID, hoặc nhấn Huỷ.", reply_markup=cancel_markup())
                return
            target, user = await resolve_user(client, message.text)
            if target is None:
                await message.reply_text("Không tìm thấy user. Gửi lại @username hoặc ID, hoặc nhấn Huỷ.", reply_markup=cancel_markup())
                return
            if client.uploadlimit:
                pop_pending(uid)
                set_pending(uid, "addpre_plan_wait", target=target, menu_msg_id=mid)
                await reply_menu(f"Đã chọn {user.mention if user else target}. Chọn gói Premium.", plan_choice_markup(target))
            else:
                pop_pending(uid)
                set_pending(uid, "addpre_time", target=target, plan=None, menu_msg_id=mid)
                await reply_menu("Gửi thời hạn Premium, ví dụ: 1 day, 1 month.", cancel_markup())
            return

        if action == "addpre_time":
            if not is_admin(uid) or not message.text:
                await message.reply_text("Gửi thời hạn, ví dụ: 1 day, 1 month.", reply_markup=cancel_markup())
                return
            target = pend.get("target")
            plan = pend.get("plan")
            try:
                user = await client.get_users(target)
            except Exception:
                user = None
            text = await _apply_premium(client, message, target, user, message.text.strip(), plan)
            pop_pending(uid)
            await reply_menu(text, admin_markup())
            return

        if action == "rmpre_user":
            if not is_admin(uid) or not message.text:
                await message.reply_text("Gửi @username hoặc ID, hoặc nhấn Huỷ.", reply_markup=cancel_markup())
                return
            target, user = await resolve_user(client, message.text)
            if target is None:
                await message.reply_text("Không tìm thấy user. Gửi lại @username hoặc ID.", reply_markup=cancel_markup())
                return
            if await digital_botz.has_premium_access(target):
                await digital_botz.remove_premium(target)
                try:
                    await client.send_message(target, "Tài khoản của bạn đã được gỡ khỏi gói Premium.")
                except Exception:
                    pass
                mention = user.mention if user else f"`{target}`"
                text = f"Đã gỡ Premium của {mention}."
            else:
                text = "Người dùng không có Premium hoặc không tìm thấy."
            pop_pending(uid)
            await reply_menu(text, admin_markup())
            return

        if action == "ban_user":
            if not is_admin(uid) or not message.text:
                await message.reply_text("Gửi số ngày và lý do, ví dụ: 7 Vi phạm.", reply_markup=cancel_markup())
                return
            parts = message.text.strip().split(None, 1)
            try:
                days = int(parts[0])
            except ValueError:
                await message.reply_text("Số ngày không hợp lệ. Ví dụ: 7 Vi phạm.", reply_markup=cancel_markup())
                return
            reason = parts[1] if len(parts) > 1 else "N/A"
            target = pend.get("target")
            await digital_botz.ban_user(target, days, reason)
            try:
                await client.send_message(target, f"Bạn bị chặn dùng bot trong {days} ngày. Lý do: {reason}")
            except Exception:
                pass
            pop_pending(uid)
            await reply_menu(f"Đã chặn `{target}` trong {days} ngày. Lý do: {reason}", admin_markup())
            return

        # Unknown pending action: drop and let other handlers run.
        pop_pending(uid)
        await message.continue_propagation()
    except Exception:
        traceback.print_exc()
        pop_pending(uid)
        await message.reply_text("Có lỗi khi xử lý. Thử lại từ menu.")
