# ThanhDora | Doratem | https://github.com/ThanhDora | @DoraTeamMods
"""
Apache License 2.0
"""

# pyrogram imports
from pyrogram import Client, filters
from pyrogram.enums import MessageMediaType, ParseMode
from pyrogram.errors import FloodWait
from pyrogram.file_id import FileId
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply

# hachoir imports
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from PIL import Image

# bots imports
from helper.utils import progress_for_pyrogram, convert, humanbytes, add_prefix_suffix, remove_path, fetch_itunes_artwork, fetch_itunes_artwork_and_inject_ipa, get_bundle_id_from_file, fetch_itunes_track_name, fetch_itunes_version, sanitize_filename_for_app
from helper.database import digital_botz
from helper.ffmpeg import change_metadata
from config import Config
from plugins import require_approved

# extra imports
from asyncio import sleep
from io import BytesIO
import os, time, asyncio, tempfile, shutil
import logging

_botlog = logging.getLogger(__name__)


UPLOAD_TEXT = "[>] Uploading..."
DOWNLOAD_TEXT = "[>] Downloading..."
RUNNING_ICONS = ["⚡", "🔄", "⏳", "◐", "◎"]
SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
ANIM_INTERVAL = 0.5
ICON_INFO = Config.E_LOADING
ICON_PROGRESS = Config.E_LOADING
ICON_DONE = Config.E_SUCCESS
ICON_SUCCESS = Config.E_SUCCESS
RUNNING_HEADER_ICON = Config.E_LOADING
ITUNES_LOADING_BASE = "Đang lấy ảnh từ iTunes, gắn vào file..."
ITUNES_LINE_ICONS = [Config.E_LOADING, Config.E_LOADING, Config.E_SUCCESS]

def _loading_sticker():
    v = getattr(Config, "LOADING_STICKER", None)
    if not v:
        return None
    return v if isinstance(v, list) else [v]


def _loading_gif_path():
    if _loading_sticker():
        return None
    if getattr(Config, "LOADING_GIF", None) and os.path.isfile(Config.LOADING_GIF):
        return Config.LOADING_GIF
    base = os.path.dirname(os.path.abspath(__file__))
    for name in ("loading.gif", "assets/loading.gif", "Loading.gif"):
        p = os.path.join(base, "..", name) if "assets" in name else os.path.join(base, name)
        p = os.path.normpath(p)
        if os.path.isfile(p):
            return p
    return None


def _running_msg(header_icon, *lines):
    head = f"<b>{header_icon} ĐANG XỬ LÝ...</b>"
    return head + "\n" + "\n".join(lines) if lines else head


def _running_msg_no_icon(*lines):
    head = "<b>ĐANG XỬ LÝ...</b>"
    return head + "\n" + "\n".join(lines) if lines else head


def _running_msg_auto(header_icon, *lines):
    return _running_msg_no_icon(*lines) if _use_sticker() else _running_msg(header_icon, *lines)


def _use_sticker():
    return bool(_loading_sticker())


STICKER_ROTATE_INTERVAL = 1.5


async def _rotate_stickers(bot, chat_id, reply_to_id, sticker_list, msg_ref, stop_event):
    idx = 0
    n = len(sticker_list)
    while not stop_event.is_set():
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=STICKER_ROTATE_INTERVAL)
        except asyncio.TimeoutError:
            pass
        if stop_event.is_set():
            break
        try:
            if msg_ref[0]:
                await msg_ref[0].delete()
        except Exception:
            pass
        idx = (idx + 1) % n
        try:
            msg_ref[0] = await bot.send_sticker(chat_id, sticker_list[idx], reply_to_message_id=reply_to_id)
        except Exception:
            pass


async def _animate_download_loading(message, stop_event):
    use_icon = not _use_sticker()
    i = 0
    while not stop_event.is_set():
        try:
            if use_icon:
                h = SPINNER_FRAMES[i % len(SPINNER_FRAMES)]
                await message.edit(_running_msg(h, f"{ICON_PROGRESS} Downloading..."), parse_mode=ParseMode.HTML)
            else:
                await message.edit(_running_msg_no_icon(f"{ICON_PROGRESS} Downloading..."), parse_mode=ParseMode.HTML)
            i += 1
        except Exception:
            pass
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=ANIM_INTERVAL)
        except asyncio.TimeoutError:
            pass


async def _animate_itunes_loading(message, stop_event):
    use_icon = not _use_sticker()
    i = 0
    while not stop_event.is_set():
        try:
            if use_icon:
                h = SPINNER_FRAMES[i % len(SPINNER_FRAMES)]
                line_icon = ITUNES_LINE_ICONS[(i // 2) % len(ITUNES_LINE_ICONS)]
                body = f"{line_icon} {ITUNES_LOADING_BASE}"
                await message.edit(_running_msg(h, body), parse_mode=ParseMode.HTML)
            else:
                line_icon = ITUNES_LINE_ICONS[(i // 2) % len(ITUNES_LINE_ICONS)]
                await message.edit(_running_msg_no_icon(f"{line_icon} {ITUNES_LOADING_BASE}"), parse_mode=ParseMode.HTML)
            i += 1
        except Exception:
            pass
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=ANIM_INTERVAL)
        except asyncio.TimeoutError:
            pass

app = Client("4gb_FileRenameBot", api_id=Config.API_ID, api_hash=Config.API_HASH, session_string=Config.STRING_SESSION)


@Client.on_message(filters.private & (filters.audio | filters.document | filters.video) & filters.create(require_approved))
async def rename_start(client, message):
    user_id  = message.from_user.id
    rkn_file = getattr(message, message.media.value)
    filename = rkn_file.file_name or ""
    filesize = humanbytes(rkn_file.file_size)
    mime_type = rkn_file.mime_type
    dcid = FileId.decode(rkn_file.file_id).dc_id
    extension_type = mime_type.split('/')[0]
    is_ipa_deb = filename.lower().endswith((".ipa", ".deb"))

    if client.premium and client.uploadlimit:
        await digital_botz.reset_uploadlimit_access(user_id)
        user_data = await digital_botz.get_user_data(user_id)
        limit = user_data.get('uploadlimit', 0)
        used = user_data.get('used_limit', 0)
        remain = int(limit) - int(used)
        used_percentage = int(used) / int(limit) * 100
        if remain < int(rkn_file.file_size):
            return await message.reply_text(f"{used_percentage:.2f}% Of Daily Upload Limit {humanbytes(limit)}.\n\n Media Size: {filesize}\n Your Used Daily Limit {humanbytes(used)}\n\nYou have only **{humanbytes(remain)}** Data.\nPlease, Buy Premium Plan s.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🪪 Uᴘɢʀᴀᴅᴇ", callback_data="plans")]]))

    if is_ipa_deb:
        await process_upload(client, message.chat.id, message, "document", filename.strip() or ("app.ipa" if filename.lower().endswith(".ipa") else "app.deb"))
        return

    if await digital_botz.has_premium_access(user_id) and client.premium:
        if not Config.STRING_SESSION:
            if rkn_file.file_size > 2000 * 1024 * 1024:
                 return await message.reply_text("Sᴏʀʀy Bʀᴏ Tʜɪꜱ Bᴏᴛ Iꜱ Dᴏᴇꜱɴ'ᴛ Sᴜᴩᴩᴏʀᴛ Uᴩʟᴏᴀᴅɪɴɢ Fɪʟᴇꜱ Bɪɢɢᴇʀ Tʜᴀɴ 2Gʙ+")

        try:
            await message.reply_text(
                text=f"**__ᴍᴇᴅɪᴀ ɪɴꜰᴏ:\n\n◈ ᴏʟᴅ ꜰɪʟᴇ ɴᴀᴍᴇ: `{filename}`\n\n◈ ᴇxᴛᴇɴꜱɪᴏɴ: `{extension_type.upper()}`\n◈ ꜰɪʟᴇ ꜱɪᴢᴇ: `{filesize}`\n◈ ᴍɪᴍᴇ ᴛʏᴇᴩ: `{mime_type}`\n◈ ᴅᴄ ɪᴅ: `{dcid}`\n\nᴘʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴛʜᴇ ɴᴇᴡ ғɪʟᴇɴᴀᴍᴇ ᴡɪᴛʜ ᴇxᴛᴇɴsɪᴏɴ ᴀɴᴅ ʀᴇᴘʟʏ ᴛʜɪs ᴍᴇssᴀɢᴇ....__**",
                reply_to_message_id=message.id,  
                reply_markup=ForceReply(True)
            )       
            await asyncio.sleep(30)
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await message.reply_text(
                text=f"**__ᴍᴇᴅɪᴀ ɪɴꜰᴏ:\n\n◈ ᴏʟᴅ ꜰɪʟᴇ ɴᴀᴍᴇ: `{filename}`\n\n◈ ᴇxᴛᴇɴꜱɪᴏɴ: `{extension_type.upper()}`\n◈ ꜰɪʟᴇ ꜱɪᴢᴇ: `{filesize}`\n◈ ᴍɪᴍᴇ ᴛʏᴇᴩ: `{mime_type}`\n◈ ᴅᴄ ɪᴅ: `{dcid}`\n\nᴘʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴛʜᴇ ɴᴇᴡ ғɪʟᴇɴᴀᴍᴇ ᴡɪᴛʜ ᴇxᴛᴇɴsɪᴏɴ ᴀɴᴅ ʀᴇᴘʟʏ ᴛʜɪs ᴍᴇssᴀɢᴇ....__**",
                reply_to_message_id=message.id,  
                reply_markup=ForceReply(True)
            )
        except Exception as e:
            print(f"Error in rename_start: {e}")
    else:
        if rkn_file.file_size > 2000 * 1024 * 1024 and client.premium:
            return await message.reply_text("If you want to rename 4GB+ files then you will have to buy premium. /plans")

        try:
            await message.reply_text(
                text=f"**__ᴍᴇᴅɪᴀ ɪɴꜰᴏ:\n\n◈ ᴏʟᴅ ꜰɪʟᴇ ɴᴀᴍᴇ: `{filename}`\n\n◈ ᴇxᴛᴇɴꜱɪᴏɴ: `{extension_type.upper()}`\n◈ ꜰɪʟᴇ ꜱɪᴢᴇ: `{filesize}`\n◈ ᴍɪᴍᴇ ᴛʏᴇᴩ: `{mime_type}`\n◈ ᴅᴄ ɪᴅ: `{dcid}`\n\nᴘʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴛʜᴇ ɴᴇᴡ ғɪʟᴇɴᴀᴍᴇ ᴡɪᴛʜ ᴇxᴛᴇɴsɪᴏɴ ᴀɴᴅ ʀᴇᴘʟʏ ᴛʜɪs ᴍᴇssᴀɢᴇ....__**",
                reply_to_message_id=message.id,  
                reply_markup=ForceReply(True)
            )       
            await asyncio.sleep(30)
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await message.reply_text(
                text=f"**__ᴍᴇᴅɪᴀ ɪɴꜰᴏ:\n\n◈ ᴏʟᴅ ꜰɪʟᴇ ɴᴀᴍᴇ: `{filename}`\n\n◈ ᴇxᴛᴇɴꜱɪᴏɴ: `{extension_type.upper()}`\n◈ ꜰɪʟᴇ ꜱɪᴢᴇ: `{filesize}`\n◈ ᴍɪᴍᴇ ᴛʏᴇᴩ: `{mime_type}`\n◈ ᴅᴄ ɪᴅ: `{dcid}`\n\nᴘʟᴇᴀsᴇ ᴇɴᴛᴇʀ ᴛʜᴇ ɴᴇᴡ ғɪʟᴇɴᴀᴍᴇ ᴡɪᴛʜ ᴇxᴛᴇɴsɪᴏɴ ᴀɴᴅ ʀᴇᴘʟʏ ᴛʜɪs ᴍᴇssᴀɢᴇ....__**",
                reply_to_message_id=message.id,  
                reply_markup=ForceReply(True)
            )
        except Exception as e:
            print(f"Error in rename_start (non-premium): {e}")


@Client.on_message(filters.private & filters.reply & filters.create(require_approved))
async def refunc(client, message):
    reply_message = message.reply_to_message
    if (reply_message.reply_markup) and isinstance(reply_message.reply_markup, ForceReply):
        new_name = message.text 
        await message.delete() 
        msg = await client.get_messages(message.chat.id, reply_message.id)
        file = msg.reply_to_message
        media = getattr(file, file.media.value)
        if not "." in new_name:
            if "." in media.file_name:
                extn = media.file_name.rsplit('.', 1)[-1]
            else:
                extn = "mkv"
            new_name = new_name + "." + extn
        await reply_message.delete()
        await message.delete()
        await process_upload(client, message.chat.id, file, "document", new_name)

async def process_upload(bot, chat_id, file_message, upload_type, new_filename):
    user_id = int(chat_id)
    sticker_ids = _loading_sticker()
    _gif_path = _loading_gif_path()
    if sticker_ids:
        rkn_processing = await bot.send_message(chat_id, _running_msg_no_icon(f"{ICON_INFO} Loading file..."), parse_mode=ParseMode.HTML)
    else:
        rkn_processing = await bot.send_message(chat_id, _running_msg(SPINNER_FRAMES[0], f"{ICON_INFO} Loading file..."), parse_mode=ParseMode.HTML)
    loading_media_ref = [None]
    stop_sticker_rot = None
    sticker_rot_task = None
    if sticker_ids:
        try:
            loading_media_ref[0] = await bot.send_sticker(chat_id, sticker_ids[0], reply_to_message_id=rkn_processing.id)
            if len(sticker_ids) > 1:
                stop_sticker_rot = asyncio.Event()
                sticker_rot_task = asyncio.create_task(_rotate_stickers(bot, chat_id, rkn_processing.id, sticker_ids, loading_media_ref, stop_sticker_rot))
        except Exception:
            pass
    elif _gif_path:
        try:
            loading_media_ref[0] = await bot.send_animation(chat_id, _gif_path, reply_to_message_id=rkn_processing.id)
        except Exception:
            pass
    if not os.path.isdir("Metadata"):
        os.mkdir("Metadata")
    if not new_filename:
        if sticker_rot_task:
            stop_sticker_rot.set()
            try:
                await asyncio.wait_for(sticker_rot_task, timeout=3)
            except Exception:
                pass
        if loading_media_ref[0]:
            try:
                await loading_media_ref[0].delete()
            except Exception:
                pass
        return await rkn_processing.edit(f"{Config.E_ERROR} Không lấy được tên file.", parse_mode=ParseMode.HTML)
    user_data = await digital_botz.get_user_data(user_id)
    try:
        prefix = user_data.get('prefix', None)
        suffix = user_data.get('suffix', None)
        new_filename = await add_prefix_suffix(new_filename, prefix, suffix)
    except Exception as e:
        if sticker_rot_task:
            stop_sticker_rot.set()
            try:
                await asyncio.wait_for(sticker_rot_task, timeout=3)
            except Exception:
                pass
        if loading_media_ref[0]:
            try:
                await loading_media_ref[0].delete()
            except Exception:
                pass
        return await rkn_processing.edit(f"{Config.E_ERROR} Something went wrong can't able to set Prefix or Suffix\n\nContact -> @DoraTeamMods\nError: {e}", parse_mode=ParseMode.HTML)
    media = getattr(file_message, file_message.media.value)
    file_path = f"Renames/{new_filename}"
    metadata_path = f"Metadata/{new_filename}"
    used = user_data.get('used_limit', 0)
    stop_dl_anim = asyncio.Event()
    dl_anim_task = asyncio.create_task(_animate_download_loading(rkn_processing, stop_dl_anim))
    if bot.premium and bot.uploadlimit:
        limit = user_data.get('uploadlimit', 0)
        total_used = int(used) + int(media.file_size)
        await digital_botz.set_used_limit(user_id, total_used)
    try:
        dl_path = await bot.download_media(message=file_message, file_name=file_path, progress=progress_for_pyrogram, progress_args=(f"{RUNNING_ICONS[0]} ĐANG XỬ LÝ...\n{DOWNLOAD_TEXT}", rkn_processing, time.time()))
    except Exception as e:
        if bot.premium and bot.uploadlimit:
            used_remove = int(used) - int(media.file_size)
            await digital_botz.set_used_limit(user_id, used_remove)
        stop_dl_anim.set()
        try:
            await asyncio.wait_for(dl_anim_task, timeout=2)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            dl_anim_task.cancel()
            try:
                await dl_anim_task
            except asyncio.CancelledError:
                pass
        if sticker_rot_task:
            stop_sticker_rot.set()
            try:
                await asyncio.wait_for(sticker_rot_task, timeout=3)
            except Exception:
                pass
        if loading_media_ref[0]:
            try:
                await loading_media_ref[0].delete()
            except Exception:
                pass
        return await rkn_processing.edit(f"{Config.E_ERROR} Download Error: {e}", parse_mode=ParseMode.HTML)
    finally:
        stop_dl_anim.set()
        try:
            await asyncio.wait_for(dl_anim_task, timeout=2)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            dl_anim_task.cancel()
            try:
                await dl_anim_task
            except asyncio.CancelledError:
                pass
    await rkn_processing.edit(_running_msg_auto(RUNNING_HEADER_ICON, f"{ICON_DONE} Download complete.", f"{ICON_INFO} Processing..."), parse_mode=ParseMode.HTML)
    metadata_mode = await digital_botz.get_metadata_mode(user_id)
    if metadata_mode:
        metadata = await digital_botz.get_metadata_code(user_id)
        if metadata:
            await rkn_processing.edit(_running_msg_auto(RUNNING_HEADER_ICON, f"{ICON_DONE} Download complete.", f"{ICON_INFO} Found metadata.", f"{ICON_PROGRESS} Adding metadata to file..."), parse_mode=ParseMode.HTML)
            if await change_metadata(dl_path, metadata_path, metadata):
                await rkn_processing.edit(_running_msg_auto(RUNNING_HEADER_ICON, f"{ICON_SUCCESS} Metadata added."), parse_mode=ParseMode.HTML)
            else:
                await rkn_processing.edit(_running_msg_auto(RUNNING_HEADER_ICON, f"{ICON_INFO} Failed to add metadata, uploading original file..."), parse_mode=ParseMode.HTML)
                metadata_mode = False
        else:
            await rkn_processing.edit(_running_msg_auto(RUNNING_HEADER_ICON, f"{ICON_INFO} No metadata found, uploading original file..."), parse_mode=ParseMode.HTML)
            metadata_mode = False
    else:
        await rkn_processing.edit(_running_msg_auto(RUNNING_HEADER_ICON, f"{ICON_INFO} Preparing upload..."), parse_mode=ParseMode.HTML)
    duration = 0
    try:
        parser = createParser(file_path)
        metadata_obj = extractMetadata(parser)
        if metadata_obj and metadata_obj.has("duration"):
            duration = metadata_obj.get('duration').seconds
        if parser:
            parser.close()
    except Exception:
        pass
    c_caption = user_data.get('caption', None)
    c_thumb = user_data.get('file_id', None)
    if c_caption:
        repl = {"{filename}": new_filename, "{filesize}": humanbytes(media.file_size), "{duration}": convert(duration)}
        caption = c_caption
        for k, v in repl.items():
            caption = caption.replace(k, str(v))
    else:
        caption = f"**{new_filename}**"
    ph_path = None
    actual_file = metadata_path if (metadata_mode and os.path.exists(metadata_path)) else (dl_path or file_path)
    orig_name = (media.file_name or "").strip()
    orig_low = orig_name.lower()
    new_low = (new_filename or "").lower()
    is_ipa_deb = (orig_low.endswith(".ipa") or orig_low.endswith(".deb") or new_low.endswith(".ipa") or new_low.endswith(".deb"))
    if is_ipa_deb:
        await rkn_processing.edit(_running_msg_auto(RUNNING_HEADER_ICON, f"{ICON_INFO} Đang giải nén file, tìm plist..."), parse_mode=ParseMode.HTML)
        _botlog.info("Đang giải nén file, tìm plist để đọc Bundle ID. user_id=%s file=%s", user_id, orig_name)
    ext_hint = orig_name if (orig_low.endswith(".ipa") or orig_low.endswith(".deb")) else new_filename
    bundle_id, app_name, version = get_bundle_id_from_file(actual_file, extension_hint=ext_hint)
    if is_ipa_deb:
        if bundle_id:
            _botlog.info("Bundle ID từ file | user_id=%s file=%s | bundle_id=%s app=%s version=%s", user_id, orig_name, bundle_id, app_name or "", version or "")
        else:
            _botlog.info("Không tìm thấy Bundle ID | user_id=%s file=%s", user_id, orig_name)
    modified_ipa_path = None
    if bundle_id:
        _botlog.info("Đang lấy ảnh từ iTunes, bundle_id=%s", bundle_id)
        stop_itunes_anim = asyncio.Event()
        anim_task = asyncio.create_task(_animate_itunes_loading(rkn_processing, stop_itunes_anim))
        try:
            is_ipa = orig_low.endswith(".ipa") or new_low.endswith(".ipa")
            if is_ipa:
                modified_ipa, thumb_path, _ = await fetch_itunes_artwork_and_inject_ipa(bundle_id, actual_file)
                if modified_ipa and thumb_path:
                    modified_ipa_path = modified_ipa
                    ph_path = thumb_path
                    _botlog.info("Đã chèn iTunesArtwork vào IPA. bundle_id=%s", bundle_id)
            if ph_path is None:
                itunes_path, _ = await fetch_itunes_artwork(bundle_id)
                if itunes_path:
                    ph_path = itunes_path
        finally:
            stop_itunes_anim.set()
            try:
                await asyncio.wait_for(anim_task, timeout=2)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                anim_task.cancel()
                try:
                    await anim_task
                except asyncio.CancelledError:
                    pass
        if ph_path:
            try:
                img = Image.open(ph_path).convert("RGB")
                img = img.resize((320, 320), getattr(Image, "LANCZOS", Image.BICUBIC))
                for q in [85, 70, 55, 40, 30, 20]:
                    img.save(ph_path, "JPEG", quality=q, optimize=True)
                    if os.path.getsize(ph_path) <= 200 * 1024:
                        break
            except Exception:
                pass
            _botlog.info("Ảnh iTunes đã lấy, sẽ gắn vào file khi upload. bundle_id=%s path=%s", bundle_id, ph_path)
    if ph_path is None and (media.thumbs or c_thumb):
        try:
            if c_thumb:
                ph_path = await bot.download_media(c_thumb)
            else:
                ph_path = await bot.download_media(media.thumbs[0].file_id)
        except Exception:
            ph_path = None
    if ph_path and os.path.exists(ph_path):
        try:
            img = Image.open(ph_path).convert("RGB")
            img = img.resize((320, 320), Image.LANCZOS)
            for q in [85, 70, 55, 40, 30, 20]:
                img.save(ph_path, "JPEG", quality=q, optimize=True)
                if os.path.getsize(ph_path) <= 200 * 1024:
                    break
        except Exception:
            pass
    final_file_path = modified_ipa_path if modified_ipa_path else (metadata_path if metadata_mode and os.path.exists(metadata_path) else (dl_path or file_path))
    itunes_upload_path = None
    if bundle_id:
        itunes_track_name = await fetch_itunes_track_name(bundle_id)
        if itunes_track_name:
            caption = caption.replace("{gamename}", itunes_track_name)
        if is_ipa_deb and (app_name or version or bundle_id):
            itunes_version = await fetch_itunes_version(bundle_id) if not version and bundle_id else None
            app_name_val = itunes_track_name or app_name or 'N/A'
            app_version_val = version or itunes_version or 'N/A'
            caption = f"<b>AppName</b> : {app_name_val}\n<b>App Version</b> : {app_version_val}\n<b>Bundle ID</b> : {bundle_id or 'N/A'}"
        elif itunes_track_name:
            caption = f"**{itunes_track_name}**\n{caption}"
        if itunes_track_name:
            safe_name = sanitize_filename_for_app(itunes_track_name)
            p = user_data.get('prefix') or ''
            s = user_data.get('suffix') or ''
            upload_basename = p + safe_name + s
            ext = os.path.splitext(final_file_path)[1] or (".ipa" if new_low.endswith(".ipa") else ".deb")
            try:
                itunes_upload_path = os.path.join(tempfile.gettempdir(), upload_basename + ext)
                shutil.copy2(final_file_path, itunes_upload_path)
                final_file_path = itunes_upload_path
            except Exception:
                itunes_upload_path = None
    if media.file_size > 2000 * 1024 * 1024:
        target_id = Config.LOG_CHANNEL if Config.LOG_CHANNEL else user_id
        client_for_upload = app if Config.LOG_CHANNEL else bot
        filw, error = await upload_files(client_for_upload, target_id, upload_type, final_file_path, ph_path, caption, duration, rkn_processing)
        if error:
            if bot.premium and bot.uploadlimit:
                used_remove = int(used) - int(media.file_size)
                await digital_botz.set_used_limit(user_id, used_remove)
            await remove_path(ph_path, file_path, dl_path, metadata_path, modified_ipa_path, itunes_upload_path)
            if sticker_rot_task:
                stop_sticker_rot.set()
                try:
                    await asyncio.wait_for(sticker_rot_task, timeout=3)
                except Exception:
                    pass
            if loading_media_ref[0]:
                try:
                    await loading_media_ref[0].delete()
                except Exception:
                    pass
            return await rkn_processing.edit(f"{Config.E_ERROR} Upload Error: {error}", parse_mode=ParseMode.HTML)
        if Config.LOG_CHANNEL:
            from_chat = filw.chat.id
            mg_id = filw.id
            await asyncio.sleep(2)
            await bot.copy_message(user_id, from_chat, mg_id)
            await bot.delete_messages(from_chat, mg_id)
    else:
        filw, error = await upload_files(bot, user_id, upload_type, final_file_path, ph_path, caption, duration, rkn_processing)
        if error:
            if bot.premium and bot.uploadlimit:
                used_remove = int(used) - int(media.file_size)
                await digital_botz.set_used_limit(user_id, used_remove)
            await remove_path(ph_path, file_path, dl_path, metadata_path, modified_ipa_path, itunes_upload_path)
            if sticker_rot_task:
                stop_sticker_rot.set()
                try:
                    await asyncio.wait_for(sticker_rot_task, timeout=3)
                except Exception:
                    pass
            if loading_media_ref[0]:
                try:
                    await loading_media_ref[0].delete()
                except Exception:
                    pass
            return await rkn_processing.edit(f"{Config.E_ERROR} Upload Error: {error}", parse_mode=ParseMode.HTML)
    await remove_path(ph_path, file_path, dl_path, metadata_path, modified_ipa_path, itunes_upload_path)
    if sticker_rot_task:
        stop_sticker_rot.set()
        try:
            await asyncio.wait_for(sticker_rot_task, timeout=3)
        except Exception:
            pass
    if loading_media_ref[0]:
        try:
            await loading_media_ref[0].delete()
        except Exception:
            pass
    try:
        await rkn_processing.delete()
    except Exception:
        pass

def _make_document_thumb(ph_path):
    if not ph_path or not os.path.exists(ph_path):
        return None
    try:
        img = Image.open(ph_path).convert("RGB")
        img.thumbnail((320, 320), getattr(Image, "LANCZOS", Image.BICUBIC))
        fd, jpg_path = tempfile.mkstemp(suffix=".jpg", prefix="thumb_")
        os.close(fd)
        for q in [85, 70, 55, 40, 30, 20]:
            img.save(jpg_path, "JPEG", quality=q, optimize=True)
            if os.path.getsize(jpg_path) <= 200 * 1024:
                return jpg_path
        img.save(jpg_path, "JPEG", quality=20, optimize=True)
        return jpg_path if os.path.getsize(jpg_path) <= 200 * 1024 else None
    except Exception:
        return None


async def upload_files(bot, sender_id, upload_type, file_path, ph_path, caption, duration, rkn_processing):
    try:
        if not os.path.exists(file_path):
            return None, f"File not found: {file_path}"
        thumb_arg = _make_document_thumb(ph_path)
        if upload_type == "document":
            filw = await bot.send_document(
                sender_id,
                document=file_path,
                thumb=thumb_arg,
                caption=caption,
                parse_mode=ParseMode.HTML,
                progress=progress_for_pyrogram,
                progress_args=(f"{RUNNING_ICONS[0]} ĐANG XỬ LÝ...\n{UPLOAD_TEXT}", rkn_processing, time.time()))
        
        elif upload_type == "video":
            filw = await bot.send_video(
                sender_id,
                video=file_path,
                caption=caption,
                thumb=thumb_arg,
                duration=duration,
                parse_mode=ParseMode.HTML,
                progress=progress_for_pyrogram,
                progress_args=(f"{RUNNING_ICONS[0]} ĐANG XỬ LÝ...\n{UPLOAD_TEXT}", rkn_processing, time.time()))
        
        elif upload_type == "audio":
            filw = await bot.send_audio(
                sender_id,
                audio=file_path,
                caption=caption,
                thumb=thumb_arg,
                duration=duration,
                parse_mode=ParseMode.HTML,
                progress=progress_for_pyrogram,
                progress_args=(f"{RUNNING_ICONS[0]} ĐANG XỬ LÝ...\n{UPLOAD_TEXT}", rkn_processing, time.time()))
        else:
            return None, f"Unknown upload type: {upload_type}"
        if isinstance(thumb_arg, str) and thumb_arg.endswith(".jpg"):
            try:
                os.remove(thumb_arg)
            except Exception:
                pass
        return filw, None
    except Exception as e:
        return None, str(e)


#@Client.on_callback_query(filters.regex("upload"))
async def upload_doc(bot, update):
    rkn_processing = await update.message.edit(_running_msg_auto(RUNNING_HEADER_ICON, f"{ICON_INFO} Loading file..."), parse_mode=ParseMode.HTML)
    
    # Creating Directory for Metadata
    if not os.path.isdir("Metadata"):
        os.mkdir("Metadata")

    user_id = int(update.message.chat.id)
    new_name = update.message.text
    new_filename_ = new_name.split(":-")[1].strip().strip("*`\n\t ").strip() if ":-" in (new_name or "") else ""
    if not new_filename_:
        return await rkn_processing.edit(f"{Config.E_ERROR} Không lấy được tên file.", parse_mode=ParseMode.HTML)
    user_data = await digital_botz.get_user_data(user_id)
    try:
        prefix = user_data.get('prefix', None)
        suffix = user_data.get('suffix', None)
        new_filename = await add_prefix_suffix(new_filename_, prefix, suffix)
    except Exception as e:
        return await rkn_processing.edit(f"{Config.E_ERROR} Something went wrong can't able to set Prefix or Suffix\n\nContact -> @DoraTeamMods\nError: {e}", parse_mode=ParseMode.HTML)

    # msg file location 
    file = update.message.reply_to_message
    media = getattr(file, file.media.value)
    
    # File paths for download and metadata
    file_path = f"Renames/{new_filename}"
    metadata_path = f"Metadata/{new_filename}"

    stop_dl_anim = asyncio.Event()
    dl_anim_task = asyncio.create_task(_animate_download_loading(rkn_processing, stop_dl_anim))
    if bot.premium and bot.uploadlimit:
        limit = user_data.get('uploadlimit', 0)
        used = user_data.get('used_limit', 0)
        total_used = int(used) + int(media.file_size)
        await digital_botz.set_used_limit(user_id, total_used)
    try:
        dl_path = await bot.download_media(message=file, file_name=file_path, progress=progress_for_pyrogram, progress_args=(f"{RUNNING_ICONS[0]} ĐANG XỬ LÝ...\n{DOWNLOAD_TEXT}", rkn_processing, time.time()))
    except Exception as e:
        if bot.premium and bot.uploadlimit:
            used_remove = int(used) - int(media.file_size)
            await digital_botz.set_used_limit(user_id, used_remove)
        stop_dl_anim.set()
        try:
            await asyncio.wait_for(dl_anim_task, timeout=2)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            dl_anim_task.cancel()
            try:
                await dl_anim_task
            except asyncio.CancelledError:
                pass
        return await rkn_processing.edit(f"{Config.E_ERROR} Download Error: {e}", parse_mode=ParseMode.HTML)
    finally:
        stop_dl_anim.set()
        try:
            await asyncio.wait_for(dl_anim_task, timeout=2)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            dl_anim_task.cancel()
            try:
                await dl_anim_task
            except asyncio.CancelledError:
                pass

    await rkn_processing.edit(_running_msg_auto(RUNNING_HEADER_ICON, f"{ICON_DONE} Download complete.", f"{ICON_INFO} Processing..."), parse_mode=ParseMode.HTML)
    metadata_mode = await digital_botz.get_metadata_mode(user_id)
    if metadata_mode:
        metadata = await digital_botz.get_metadata_code(user_id)
        if metadata:
            await rkn_processing.edit(_running_msg_auto(RUNNING_HEADER_ICON, f"{ICON_DONE} Download complete.", f"{ICON_INFO} Found metadata.", f"{ICON_PROGRESS} Adding metadata to file..."), parse_mode=ParseMode.HTML)
            if await change_metadata(dl_path, metadata_path, metadata):
                await rkn_processing.edit(_running_msg_auto(RUNNING_HEADER_ICON, f"{ICON_SUCCESS} Metadata added."), parse_mode=ParseMode.HTML)
            else:
                await rkn_processing.edit(_running_msg_auto(RUNNING_HEADER_ICON, f"{ICON_INFO} Failed to add metadata, uploading original file..."), parse_mode=ParseMode.HTML)
                metadata_mode = False
        else:
            await rkn_processing.edit(_running_msg_auto(RUNNING_HEADER_ICON, f"{ICON_INFO} No metadata found, uploading original file..."), parse_mode=ParseMode.HTML)
            metadata_mode = False
    else:
        await rkn_processing.edit(_running_msg_auto(RUNNING_HEADER_ICON, f"{ICON_INFO} Preparing upload..."), parse_mode=ParseMode.HTML)
        
    duration = 0
    try:
        parser = createParser(file_path)
        metadata = extractMetadata(parser)
        if metadata and metadata.has("duration"):
            duration = metadata.get('duration').seconds
        if parser:
            parser.close()
    except Exception as e:
        print(f"Error extracting metadata: {e}")
        pass
        
    ph_path = None
    c_caption = user_data.get('caption', None)
    c_thumb = user_data.get('file_id', None)

    if c_caption:
        repl = {
            "{filename}": new_filename,
            "{filesize}": humanbytes(media.file_size),
            "{duration}": convert(duration),
        }
        caption = c_caption
        for k, v in repl.items():
            caption = caption.replace(k, str(v))
    else:
         caption = f"**{new_filename}**"

    ph_path = None
    actual_file = metadata_path if (metadata_mode and os.path.exists(metadata_path)) else (dl_path or file_path)
    orig_name = (media.file_name or "").strip()
    orig_low = orig_name.lower()
    new_low = (new_filename or "").lower()
    is_ipa_deb = (orig_low.endswith(".ipa") or orig_low.endswith(".deb") or
                  new_low.endswith(".ipa") or new_low.endswith(".deb"))
    if is_ipa_deb:
        await rkn_processing.edit(_running_msg_auto(RUNNING_HEADER_ICON, f"{ICON_INFO} Đang giải nén file, tìm plist..."), parse_mode=ParseMode.HTML)
        _botlog.info("Đang giải nén file, tìm plist để đọc Bundle ID. user_id=%s file=%s", user_id, orig_name)
    ext_hint = orig_name if (orig_low.endswith(".ipa") or orig_low.endswith(".deb")) else new_filename
    bundle_id, app_name, version = get_bundle_id_from_file(actual_file, extension_hint=ext_hint)
    if is_ipa_deb:
        if bundle_id:
            _botlog.info("Bundle ID từ file | user_id=%s user=%s file=%s | bundle_id=%s app=%s version=%s",
                         user_id, getattr(update.from_user, "username", "") or user_id, orig_name, bundle_id, app_name or "", version or "")
        else:
            _botlog.info("Không tìm thấy Bundle ID | user_id=%s file=%s", user_id, orig_name)
    modified_ipa_path = None
    if bundle_id:
        _botlog.info("Đang lấy ảnh từ iTunes, bundle_id=%s", bundle_id)
        stop_itunes_anim = asyncio.Event()
        anim_task = asyncio.create_task(_animate_itunes_loading(rkn_processing, stop_itunes_anim))
        try:
            is_ipa = orig_low.endswith(".ipa") or new_low.endswith(".ipa")
            if is_ipa:
                modified_ipa, thumb_path, _ = await fetch_itunes_artwork_and_inject_ipa(bundle_id, actual_file)
                if modified_ipa and thumb_path:
                    modified_ipa_path = modified_ipa
                    ph_path = thumb_path
                    _botlog.info("Đã chèn iTunesArtwork vào IPA. bundle_id=%s", bundle_id)
            if ph_path is None:
                itunes_path, _ = await fetch_itunes_artwork(bundle_id)
                if itunes_path:
                    ph_path = itunes_path
        finally:
            stop_itunes_anim.set()
            try:
                await asyncio.wait_for(anim_task, timeout=2)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                anim_task.cancel()
                try:
                    await anim_task
                except asyncio.CancelledError:
                    pass
        if ph_path:
            try:
                img = Image.open(ph_path).convert("RGB")
                img = img.resize((320, 320), getattr(Image, "LANCZOS", Image.BICUBIC))
                for q in [85, 70, 55, 40, 30, 20]:
                    img.save(ph_path, "JPEG", quality=q, optimize=True)
                    if os.path.getsize(ph_path) <= 200 * 1024:
                        break
            except Exception:
                pass
            _botlog.info("Ảnh iTunes đã lấy, sẽ gắn vào file khi upload. bundle_id=%s path=%s", bundle_id, ph_path)
    if ph_path is None and (media.thumbs or c_thumb):
        try:
            if c_thumb:
                ph_path = await bot.download_media(c_thumb)
            else:
                ph_path = await bot.download_media(media.thumbs[0].file_id)
        except Exception as e:
            print(f"Error processing thumbnail: {e}")
            ph_path = None

    if ph_path and os.path.exists(ph_path):
        try:
            img = Image.open(ph_path).convert("RGB")
            img = img.resize((320, 320), Image.LANCZOS)
            for q in [85, 70, 55, 40, 30, 20]:
                img.save(ph_path, "JPEG", quality=q, optimize=True)
                if os.path.getsize(ph_path) <= 200 * 1024:
                    break
        except Exception as e:
            print(f"Error resizing thumbnail: {e}")

    upload_type = update.data.split("#")[1]
    
    final_file_path = modified_ipa_path if modified_ipa_path else (metadata_path if metadata_mode and os.path.exists(metadata_path) else (dl_path or file_path))
    itunes_upload_path = None
    if bundle_id:
        itunes_track_name = await fetch_itunes_track_name(bundle_id)
        if itunes_track_name:
            caption = caption.replace("{gamename}", itunes_track_name)
        if is_ipa_deb and (app_name or version or bundle_id):
            itunes_version = await fetch_itunes_version(bundle_id) if not version and bundle_id else None
            app_name_val = itunes_track_name or app_name or 'N/A'
            app_version_val = version or itunes_version or 'N/A'
            caption = f"<b>AppName</b> : {app_name_val}\n<b>App Version</b> : {app_version_val}\n<b>Bundle ID</b> : {bundle_id or 'N/A'}"
        elif itunes_track_name:
            caption = f"**{itunes_track_name}**\n{caption}"
        if itunes_track_name:
            safe_name = sanitize_filename_for_app(itunes_track_name)
            p = user_data.get('prefix') or ''
            s = user_data.get('suffix') or ''
            upload_basename = p + safe_name + s
            ext = os.path.splitext(final_file_path)[1] or (".ipa" if new_low.endswith(".ipa") else ".deb")
            try:
                itunes_upload_path = os.path.join(tempfile.gettempdir(), upload_basename + ext)
                shutil.copy2(final_file_path, itunes_upload_path)
                final_file_path = itunes_upload_path
            except Exception:
                itunes_upload_path = None
    if media.file_size > 2000 * 1024 * 1024:
        target_id = Config.LOG_CHANNEL if Config.LOG_CHANNEL else update.from_user.id
        client_for_upload = app if Config.LOG_CHANNEL else bot
        filw, error = await upload_files(
            client_for_upload, target_id, upload_type, final_file_path,
            ph_path, caption, duration, rkn_processing
        )
        if error:
            if bot.premium and bot.uploadlimit:
                used_remove = int(used) - int(media.file_size)
                await digital_botz.set_used_limit(user_id, used_remove)
            await remove_path(ph_path, file_path, dl_path, metadata_path, modified_ipa_path, itunes_upload_path)
            return await rkn_processing.edit(f"{Config.E_ERROR} Upload Error: {error}", parse_mode=ParseMode.HTML)
        if Config.LOG_CHANNEL:
            from_chat = filw.chat.id
            mg_id = filw.id
            await asyncio.sleep(2)
            await bot.copy_message(update.from_user.id, from_chat, mg_id)
            await bot.delete_messages(from_chat, mg_id)
        # For big files without LOG_CHANNEL, upload already done in upload_files

    else:
        # Regular files (<2GB)
        filw, error = await upload_files(
            bot, update.message.chat.id, upload_type, final_file_path, 
            ph_path, caption, duration, rkn_processing
        )
                   
        if error:
            if bot.premium and bot.uploadlimit:
                used_remove = int(used) - int(media.file_size)
                await digital_botz.set_used_limit(user_id, used_remove)
            await remove_path(ph_path, file_path, dl_path, metadata_path, modified_ipa_path, itunes_upload_path)
            return await rkn_processing.edit(f"{Config.E_ERROR} Upload Error: {error}", parse_mode=ParseMode.HTML)

    await remove_path(ph_path, file_path, dl_path, metadata_path, modified_ipa_path, itunes_upload_path)
    try:
        await rkn_processing.delete()
    except Exception:
        pass
    return



# ThanhDora | Doratem | @DoraTeamMods
