# ThanhDora | DoraTeam | https://github.com/ThanhDora | @DoraTeamMods
"""Button menu helpers for misyou_iBot."""

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message
from pyrogram.errors import MessageNotModified, MessageIdInvalid
from config import Config

PAGE_SIZE = 6
PENDING_USERS = {}

HOME = "m:home"
HELP = "m:help"
ABOUT = "m:about"
CANCEL = "m:cancel"


def is_admin(user_id):
    return int(user_id) in {int(a) for a in Config.ADMIN if str(a).lstrip("-").isdigit()}


def btn(text, data=None, url=None):
    if url:
        return InlineKeyboardButton(text, url=url)
    return InlineKeyboardButton(text, callback_data=data)


def markup(rows):
    return InlineKeyboardMarkup(rows)


def back_row(*extra):
    row = list(extra)
    row.append(btn("Quay lai", HOME))
    return row


def cancel_markup():
    return markup([[btn("Huy", CANCEL)]])


def nav_row(prefix, page, total_pages, back=HOME):
    row = []
    if page > 0:
        row.append(btn("Truoc", f"{prefix}{page - 1}"))
    if page + 1 < total_pages:
        row.append(btn("Sau", f"{prefix}{page + 1}"))
    rows = [row] if row else []
    rows.append([btn("Quay lai", back)])
    return rows


def set_pending(user_id, action, **kwargs):
    PENDING_USERS[int(user_id)] = {"action": action, **kwargs}


def get_pending(user_id):
    return PENDING_USERS.get(int(user_id))


def pop_pending(user_id):
    return PENDING_USERS.pop(int(user_id), None)


def home_text(mention):
    return (
        f"Xin chao, {mention}\n\n"
        "Day la bot doi ten file, anh bia va chu thich.\n\n"
        "Cach dung:\n"
        "- Gui file de doi ten (bot se hoi ten moi va dinh dang).\n"
        "- Dung cac nut ben duoi de cai dat anh bia, chu thich, tien to, hau to, metadata va xem goi.\n\n"
        "Lien he ho tro: @DoraTeamMods"
    )


def help_text():
    return (
        "<b>Huong dan</b>\n\n"
        "<b>Doi ten file</b>\n"
        "Gui file (video, tai lieu hoac am thanh). Bot se hoi ten moi; tra loi tin nhan do, roi chon dinh dang neu can.\n\n"
        "<b>Anh bia</b>\n"
        "Vao Anh bia de xem, dat hoac xoa. Ban cung co the gui mot anh bat ky de dat anh bia.\n\n"
        "<b>Chu thich</b>\n"
        "Vao Chu thich de xem, dat hoac xoa. Co the dung {filename}, {filesize}, {duration}.\n\n"
        "<b>Tien to / Hau to</b>\n"
        "Them chu truoc hoac sau ten file khi doi ten.\n\n"
        "<b>Metadata</b>\n"
        "Bat/tat va dat ma metadata tuy chinh.\n\n"
        "<b>Goi cua toi</b>\n"
        "Xem goi hien tai, dung luong da dung va han su dung (neu co).\n\n"
        "Ho tro: @DoraTeamMods"
    )


def about_text(client):
    name = getattr(client, "mention", None) or "MisYou"
    return (
        f"<b>Thong tin bot</b>\n\n"
        f"Ten: {name}\n"
        f"Phat trien: ThanhDora | @DoraTeamMods\n"
        f"Nguon: https://github.com/ThanhDora"
    )


def home_markup(user_id, client):
    rows = [
        [btn("Anh bia", "m:thumb"), btn("Chu thich", "m:cap")],
        [btn("Tien to / Hau to", "m:name"), btn("Metadata", "m:meta")],
    ]
    if getattr(client, "premium", False):
        rows.append([btn("Goi cua toi", "m:plan"), btn("Nang cap", "m:upgrade")])
    rows.append([btn("Tro giup", HELP), btn("Thong tin", ABOUT)])
    if is_admin(user_id):
        rows.append([btn("Admin", "m:admin")])
    return markup(rows)


def thumb_markup():
    return markup([
        [btn("Xem", "m:thumb:view"), btn("Dat", "m:thumb:set"), btn("Xoa", "m:thumb:del")],
        [btn("Quay lai", HOME)],
    ])


def caption_markup():
    return markup([
        [btn("Xem", "m:cap:view"), btn("Dat", "m:cap:set"), btn("Xoa", "m:cap:del")],
        [btn("Quay lai", HOME)],
    ])


def name_markup():
    return markup([
        [btn("Xem tien to", "m:pre:view"), btn("Dat tien to", "m:pre:set"), btn("Xoa tien to", "m:pre:del")],
        [btn("Xem hau to", "m:suf:view"), btn("Dat hau to", "m:suf:set"), btn("Xoa hau to", "m:suf:del")],
        [btn("Quay lai", HOME)],
    ])


def metadata_markup(enabled):
    toggle = "Tat metadata" if enabled else "Bat metadata"
    return markup([
        [btn(toggle, "m:meta:tog")],
        [btn("Dat ma metadata", "m:meta:set")],
        [btn("Quay lai", HOME)],
    ])


def admin_markup():
    rows = [
        [btn("Danh sach nguoi dung", "m:ad:users:0")],
    ]
    if getattr(Config, "APPROVAL_REQUIRED", False):
        rows.append([btn("Yeu cau duyet", "m:ad:pend:0")])
    rows.append([btn("Thong ke", "m:ad:stats")])
    rows.append([btn("Phat tin", "m:ad:bc"), btn("Nhat ky", "m:ad:logs")])
    if Config.PREMIUM_MODE:
        rows.append([btn("Them Premium", "m:ad:addpre"), btn("Go Premium", "m:ad:rmpre")])
    rows.append([btn("Quay lai", HOME)])
    return markup(rows)


def upgrade_markup(with_trial=False):
    rows = [[btn("Mua Premium", url=Config.PREMIUM_LINK)]]
    if with_trial:
        rows.append([btn("Dung thu 12 gio", "m:trial")])
    rows.append([btn("Quay lai", HOME)])
    return markup(rows)


def plan_choice_markup(user_id, back="m:admin"):
    return markup([
        [btn("VIP", f"m:pl:{user_id}:VIP"), btn("Pro", f"m:pl:{user_id}:Pro"), btn("UltraPro", f"m:pl:{user_id}:UltraPro")],
        [btn("Huy", CANCEL)],
    ])


def confirm_markup(yes_data, no_data=CANCEL):
    return markup([[btn("Xac nhan", yes_data), btn("Huy", no_data)]])


def label_user(tg_user, uid):
    if tg_user:
        name = (tg_user.first_name or "").strip() or str(uid)
        if getattr(tg_user, "username", None):
            return f"{name} (@{tg_user.username})"[:60]
        return name[:60]
    return str(uid)


async def show(client, update, text, keyboard):
    """Edit the current menu message when possible; otherwise send a new one."""
    if isinstance(update, CallbackQuery):
        msg = update.message
        try:
            await msg.edit_text(text, reply_markup=keyboard, disable_web_page_preview=True)
        except MessageNotModified:
            pass
        except Exception:
            try:
                await msg.delete()
            except Exception:
                pass
            sent = await client.send_message(
                update.from_user.id, text, reply_markup=keyboard, disable_web_page_preview=True
            )
            try:
                await update.answer()
            except Exception:
                pass
            return sent
        try:
            await update.answer()
        except Exception:
            pass
        return msg
    sent = await update.reply_text(text, reply_markup=keyboard, disable_web_page_preview=True, quote=True)
    return sent


async def show_by_ids(client, chat_id, message_id, text, keyboard):
    if message_id:
        try:
            return await client.edit_message_text(
                chat_id, message_id, text, reply_markup=keyboard, disable_web_page_preview=True
            )
        except (MessageNotModified, MessageIdInvalid):
            pass
        except Exception:
            pass
    return await client.send_message(chat_id, text, reply_markup=keyboard, disable_web_page_preview=True)


def user_filter_active():
    if getattr(Config, "APPROVAL_REQUIRED", False):
        return {"approved": True}
    return {}


def user_filter_pending():
    return {"approved": False}


def page_count(total, size=PAGE_SIZE):
    if total <= 0:
        return 1
    return (total + size - 1) // size
