import asyncio
import time
import tempfile
import zipfile
from pathlib import Path

from pyrogram import Client, filters
from pyrogram.enums import ParseMode

from config import Config
from helper.dump_state import DUMP_ACTIVE
from helper.utils import humanbytes, progress_for_pyrogram
from plugins import require_approved

DUMP_PENDING = {}
MAX_FILE_SIZE = 500 * 1024 * 1024
SPINNER = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
ANIM_INTERVAL = 0.5

EXEC_EXT = (".so", ".dll", ".dylib")
META_EXT = (".dat",)
EXEC_NAMES = ("libil2cpp", "gameassembly", "unityplayer", "unityframework", "libmain")


def _is_executable(filename):
    if not filename:
        return False
    fn = filename.lower()
    return fn.endswith(EXEC_EXT) or any(x in fn for x in EXEC_NAMES)


def _is_metadata(filename):
    if not filename:
        return False
    return filename.lower().endswith(META_EXT) or "metadata" in filename.lower()


def _cleanup_user(user_id):
    DUMP_ACTIVE.discard(user_id)
    state = DUMP_PENDING.pop(user_id, None)
    if state and state.get("tmp"):
        import shutil
        try:
            shutil.rmtree(state["tmp"], ignore_errors=True)
        except Exception:
            pass


async def _animate_phase(prog_msg, phase_ref, stop_event):
    i = 0
    while not stop_event.is_set():
        try:
            h = SPINNER[i % len(SPINNER)]
            text = phase_ref.get("text", "Đang xử lý...")
            await prog_msg.edit(
                f"<b>{h} {text}</b>",
                parse_mode=ParseMode.HTML,
            )
            i += 1
        except Exception:
            pass
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=ANIM_INTERVAL)
        except asyncio.TimeoutError:
            pass


@Client.on_message(filters.private & filters.command("dump") & filters.create(require_approved))
async def cmd_dump(client, message):
    _cleanup_user(message.from_user.id)
    DUMP_PENDING[message.from_user.id] = {"exec": None, "meta": None}
    DUMP_ACTIVE.add(message.from_user.id)
    await message.reply_text(
        "<b>IL2CPP Dumper</b>\n\n"
        "Gửi <b>đủ 2 file</b> rồi bot mới bắt đầu tải và dump:\n"
        "1️⃣ File thực thi: <code>UnityFramework</code>, <code>libil2cpp.so</code>, <code>GameAssembly.dll</code>, ...\n"
        "2️⃣ File metadata: <code>global-metadata.dat</code>\n\n"
        "⚠️ Mỗi file tối đa 500MB",
        parse_mode=ParseMode.HTML,
    )


@Client.on_message(
    filters.private
    & filters.document
    & filters.create(lambda _, __, m: m.from_user and m.from_user.id in DUMP_PENDING)
    & filters.create(require_approved)
)
async def handle_dump_file(client, message):
    user_id = message.from_user.id
    if user_id not in DUMP_PENDING:
        return
    doc = message.document
    fn = (doc.file_name or "").strip() or "file"
    size = doc.file_size or 0
    if size > MAX_FILE_SIZE:
        await message.reply_text(f"File quá lớn ({humanbytes(size)}). Tối đa 500MB.")
        return
    state = DUMP_PENDING[user_id]
    is_exec = _is_executable(fn)
    is_meta = _is_metadata(fn)
    if is_exec and not is_meta:
        if state["exec"]:
            await message.reply_text("Đã nhận file thực thi. Chỉ cần gửi tiếp file metadata (.dat).")
            return
        state["exec"] = {"chat_id": message.chat.id, "message_id": message.id, "filename": fn}
    elif is_meta:
        if state["meta"]:
            await message.reply_text("Đã nhận file metadata. Chỉ cần gửi tiếp file thực thi.")
            return
        state["meta"] = {"chat_id": message.chat.id, "message_id": message.id, "filename": fn}
    else:
        await message.reply_text(
            f"Không xác định loại file <code>{fn}</code>.\n"
            "Cần: file thực thi (.so, .dll, UnityFramework) hoặc metadata (.dat)",
            parse_mode=ParseMode.HTML,
        )
        return
    if not (state["exec"] and state["meta"]):
        want = "file metadata (.dat)" if not state["meta"] else "file thực thi"
        await message.reply_text(f"Đã nhận 1 file. Gửi tiếp {want}.")
        return
    prog = await message.reply_text(f"{Config.E_LOADING} Đang tải file 1/2...")
    tmp = tempfile.mkdtemp(prefix="il2cpp_dump_")
    anim_task = None
    stop_event = asyncio.Event()
    try:
        exec_ref = state["exec"]
        meta_ref = state["meta"]
        exec_msg = await client.get_messages(exec_ref["chat_id"], exec_ref["message_id"])
        meta_msg = await client.get_messages(meta_ref["chat_id"], meta_ref["message_id"])
        if not exec_msg or not exec_msg.document:
            raise ValueError("Không lấy được file thực thi.")
        if not meta_msg or not meta_msg.document:
            raise ValueError("Không lấy được file metadata.")
        exec_path = Path(tmp) / exec_ref["filename"]
        meta_path = Path(tmp) / meta_ref["filename"]
        await client.download_media(
            exec_msg,
            str(exec_path),
            progress=progress_for_pyrogram,
            progress_args=(
                f"{Config.E_LOADING} Đang tải file 1/2...",
                prog,
                time.time(),
            ),
        )
        await prog.edit_text(f"{Config.E_LOADING} Đang tải file 2/2...")
        await client.download_media(
            meta_msg,
            str(meta_path),
            progress=progress_for_pyrogram,
            progress_args=(
                f"{Config.E_LOADING} Đang tải file 2/2...",
                prog,
                time.time(),
            ),
        )
        phase_ref = {"text": "Đang dump IL2CPP..."}
        anim_task = asyncio.create_task(_animate_phase(prog, phase_ref, stop_event))
        from dumper.run import run
        out_dir = Path(tmp) / "output"
        ok, log = await asyncio.to_thread(
            run, str(exec_path), str(meta_path), str(out_dir), copy_scripts=True
        )
        stop_event.set()
        if anim_task:
            await anim_task
        if not ok:
            await prog.edit_text(
                f"{Config.E_ERROR} Dump thất bại:\n<pre>{log[:3000]}</pre>",
                parse_mode=ParseMode.HTML,
            )
            _cleanup_user(user_id)
            return
        phase_ref["text"] = "Đang nén kết quả..."
        stop_event.clear()
        anim_task = asyncio.create_task(_animate_phase(prog, phase_ref, stop_event))
        zip_path = Path(tmp) / "dump_output.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in out_dir.rglob("*"):
                if f.is_file():
                    zf.write(f, f.relative_to(out_dir))
        stop_event.set()
        await anim_task
        anim_task = None
        await prog.edit_text(f"{Config.E_LOADING} Đang gửi kết quả...")
        await client.send_document(
            message.chat.id,
            str(zip_path),
            caption=f"{Config.E_SUCCESS} Dump hoàn tất.",
        )
        await prog.delete()
    except Exception as e:
        try:
            stop_event.set()
            if anim_task:
                await anim_task
        except Exception:
            pass
        await prog.edit_text(f"{Config.E_ERROR} Lỗi: {e}")
    finally:
        _cleanup_user(user_id)
        import shutil
        try:
            shutil.rmtree(tmp, ignore_errors=True)
        except Exception:
            pass
