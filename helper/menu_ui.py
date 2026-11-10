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
    row.append(btn("Quay lại", HOME))
    return row


def cancel_markup():
    return markup([[btn("Huỷ", CANCEL)]])


def nav_row(prefix, page, total_pages, back=HOME):
    row = []
    if page > 0:
        row.append(btn("Trang trước", f"{prefix}{page - 1}"))
    if page + 1 < total_pages:
        row.append(btn("Trang sau", f"{prefix}{page + 1}"))
    rows = [row] if row else []
    rows.append([btn("Quay lại", back)])
    return rows


def set_pending(user_id, action, **kwargs):
    PENDING_USERS[int(user_id)] = {"action": action, **kwargs}


def get_pending(user_id):
    return PENDING_USERS.get(int(user_id))


def pop_pending(user_id):
    return PENDING_USERS.pop(int(user_id), None)


def home_text(mention):
    return (
        f"Xin chào, {mention}\n\n"
        "Đây là bot đổi tên file, ảnh bìa và chú thích.\n\n"
        "Cách dùng:\n"
        "- Gửi file để đổi tên (bot sẽ hỏi tên mới và định dạng).\n"
        "- Dùng các nút bên dưới để cài đặt ảnh bìa, chú thích, tiền tố, hậu tố, metadata và xem gói.\n\n"
        "Liên hệ hỗ trợ: @DoraTeamMods"
    )


def help_text():
    return (
        "<b>Hướng dẫn</b>\n\n"
        "<b>Đổi tên file</b>\n"
        "Gửi file (video, tài liệu hoặc âm thanh). Bot sẽ hỏi tên mới; trả lời tin nhắn đó, rồi chọn định dạng nếu cần.\n\n"
        "<b>Ảnh bìa</b>\n"
        "Vào Ảnh bìa để xem, đặt hoặc xoá. Bạn cũng có thể gửi một ảnh bất kỳ để đặt ảnh bìa.\n\n"
        "<b>Chú thích</b>\n"
        "Vào Chú thích để xem, đặt hoặc xoá. Có thể dùng {filename}, {filesize}, {duration}.\n\n"
        "<b>Tiền tố / Hậu tố</b>\n"
        "Thêm chữ trước hoặc sau tên file khi đổi tên.\n\n"
        "<b>Metadata</b>\n"
        "Bật/tắt và đặt mã metadata tùy chỉnh.\n\n"
        "<b>Gói của tôi</b>\n"
        "Xem gói hiện tại, dung lượng đã dùng và hạn sử dụng (nếu có).\n\n"
        "Hỗ trợ: @DoraTeamMods"
    )


def about_text(client):
    name = getattr(client, "mention", None) or "MisYou"
    return (
        f"<b>Thông tin bot</b>\n\n"
        f"Tên: {name}\n"
        f"Phát triển: ThanhDora | @DoraTeamMods\n"
        f"Nguồn: https://github.com/ThanhDora"
    )


def home_markup(user_id, client):
    rows = [
        [btn("Ảnh bìa", "m:thumb"), btn("Chú thích", "m:cap")],
        [btn("Tiền tố / Hậu tố", "m:name"), btn("Metadata", "m:meta")],
    ]
    if getattr(client, "premium", False):
        rows.append([btn("Gói của tôi", "m:plan"), btn("Nâng cấp", "m:upgrade")])
    rows.append([btn("Trợ giúp", HELP), btn("Thông tin", ABOUT)])
    if is_admin(user_id):
        rows.append([btn("Quản trị", "m:admin")])
    return markup(rows)


def thumb_markup():
    return markup([
        [btn("Xem", "m:thumb:view"), btn("Đặt", "m:thumb:set"), btn("Xoá", "m:thumb:del")],
        [btn("Quay lại", HOME)],
    ])


def caption_markup():
    return markup([
        [btn("Xem", "m:cap:view"), btn("Đặt", "m:cap:set"), btn("Xoá", "m:cap:del")],
        [btn("Quay lại", HOME)],
    ])


def name_markup():
    return markup([
        [btn("Xem tiền tố", "m:pre:view"), btn("Đặt tiền tố", "m:pre:set"), btn("Xoá tiền tố", "m:pre:del")],
        [btn("Xem hậu tố", "m:suf:view"), btn("Đặt hậu tố", "m:suf:set"), btn("Xoá hậu tố", "m:suf:del")],
        [btn("Quay lại", HOME)],
    ])


def metadata_markup(enabled):
    toggle = "Tắt metadata" if enabled else "Bật metadata"
    return markup([
        [btn(toggle, "m:meta:tog")],
        [btn("Đặt mã metadata", "m:meta:set")],
        [btn("Quay lại", HOME)],
    ])


def admin_markup():
    rows = [
        [btn("Danh sách người dùng", "m:ad:users:0")],
    ]
    if getattr(Config, "APPROVAL_REQUIRED", False):
        rows.append([btn("Yêu cầu duyệt", "m:ad:pend:0")])
    rows.append([btn("Thống kê", "m:ad:stats")])
    rows.append([btn("Phát tin", "m:ad:bc"), btn("Nhật ký", "m:ad:logs")])
    if Config.PREMIUM_MODE:
        rows.append([btn("Thêm Premium", "m:ad:addpre"), btn("Gỡ Premium", "m:ad:rmpre")])
    rows.append([btn("Quay lại", HOME)])
    return markup(rows)


def upgrade_markup(with_trial=False):
    rows = [[btn("Mua Premium", url=Config.PREMIUM_LINK)]]
    if with_trial:
        rows.append([btn("Dùng thử 12 giờ", "m:trial")])
    rows.append([btn("Quay lại", HOME)])
    return markup(rows)


def plan_choice_markup(user_id, back="m:admin"):
    return markup([
        [btn("VIP", f"m:pl:{user_id}:VIP"), btn("Pro", f"m:pl:{user_id}:Pro"), btn("UltraPro", f"m:pl:{user_id}:UltraPro")],
        [btn("Huỷ", CANCEL)],
    ])


def confirm_markup(yes_data, no_data=CANCEL):
    return markup([[btn("Xác nhận", yes_data), btn("Huỷ", no_data)]])


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
