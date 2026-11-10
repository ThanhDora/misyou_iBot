# (c) ThanhDora / DoraTeam
# https://github.com/ThanhDora
# Telegram @DoraTeamMods
"""
Apache License 2.0
Copyright (c) 2022 @Digital_Botz | ThanhDora | @DoraTeamMods

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Telegram: https://t.me/DoraTeamMods
Repo: https://github.com/ThanhDora
"""

import re, os, time
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")
id_pattern = re.compile(r'^.\d+$') 

class Config(object):
    # digital_botz client config
    API_ID = os.environ.get("API_ID", "")
    API_HASH = os.environ.get("API_HASH", "")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "") 
    BOT = None

    # premium account string session required 😢 
    STRING_SESSION = os.environ.get("STRING_SESSION", "")
    
    # database config
    DB_NAME = os.environ.get("DB_NAME","Digital_Rename_Bot")     
    DB_URL = os.environ.get("DB_URL","")
 
    E_LOADING = '<tg-emoji emoji-id="5350752364246606166">✍️</tg-emoji>'
    E_LIMIT = '<tg-emoji emoji-id="5424857974784925603">🚫</tg-emoji>'
    E_SUCCESS = '<tg-emoji emoji-id="5260463209562776385">✅</tg-emoji>'
    E_ERROR = '<tg-emoji emoji-id="5318840353510408444">🔴</tg-emoji>'
    E_TIP = '<tg-emoji emoji-id="4968003407315993509">💡</tg-emoji>'
    E_MENU = '<tg-emoji emoji-id="5449601904147440135">👑</tg-emoji>'
    E_USER = '<tg-emoji emoji-id="5974048815789903111">👤</tg-emoji>'
    E_ID = '<tg-emoji emoji-id="5974526806995242353">🆔</tg-emoji>'
    E_TAG = '<tg-emoji emoji-id="5240228673738527951">🏷️</tg-emoji>'
    E_STAT = '<tg-emoji emoji-id="4967519884192777037">📊</tg-emoji>'
    E_GLOBE = '<tg-emoji emoji-id="5231489647946768652">🌐</tg-emoji>'
    E_SOS = '<tg-emoji emoji-id="6301027265899661025">🆘</tg-emoji>'
    E_SHIELD = '<tg-emoji emoji-id="5352888345972187597">🛡️</tg-emoji>'
    E_CALENDAR = '<tg-emoji emoji-id="5413879192267805083">📅</tg-emoji>'
    E_IOS = '<tg-emoji emoji-id="5350556204500263431">🍏</tg-emoji>'
    E_ANDROID = '<tg-emoji emoji-id="5303145396254563405">🤖</tg-emoji>'

    RKN_PIC = os.environ.get("RKN_PIC", "https://avatars.githubusercontent.com/u/164619909?v=4")
    LOADING_GIF = os.environ.get("LOADING_GIF", "").strip() or None
    _st = [x.strip() for x in os.environ.get("LOADING_STICKER", "").split(",") if x and x.strip()]
    LOADING_STICKER = _st if _st else None
    ADMIN = [int(admin) if id_pattern.search(admin) else admin for admin in os.environ.get('ADMIN', '5341455835').split()]
    try:
        LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", "0")) or None
    except (ValueError, TypeError):
        LOG_CHANNEL = None

    # free upload limit 
    FREE_UPLOAD_LIMIT = 6442450944 # calculation 6*1024*1024*1024=results

    # premium mode feature ✅
    UPLOAD_LIMIT_MODE = True 
    PREMIUM_MODE = True 
    PREMIUM_LINK = os.environ.get("PREMIUM_LINK", "https://t.me/DoraTeamMods")

    _fs = (os.environ.get("FORCE_SUB") or "").strip()
    if _fs in ("", "0"):
        FORCE_SUB = 0
    else:
        try:
            FORCE_SUB = int(_fs)
        except ValueError:
            FORCE_SUB = _fs

    APPROVAL_REQUIRED = os.environ.get("APPROVAL_REQUIRED", "false").strip().lower() in ("1", "true", "yes")
    try:
        _aid = (os.environ.get("APPROVAL_GROUP_ID") or "0").strip()
        APPROVAL_GROUP_ID = int(_aid) if _aid else None
        if APPROVAL_GROUP_ID == 0:
            APPROVAL_GROUP_ID = None
    except (ValueError, TypeError):
        APPROVAL_GROUP_ID = None

    # wes response configuration     
    PORT = int(os.environ.get("PORT", "8080"))
    BOT_UPTIME = time.time()

class rkn(object):
    # part of text configuration
    START_TXT = """<b>Xin chào, {}

Đây là bot đổi tên file, ảnh bìa và chú thích.

Cách dùng:
- Gửi file để đổi tên
- Dùng các nút bên dưới để cài đặt

Hỗ trợ: @DoraTeamMods</b>"""

    ABOUT_TXT = """<b>╭───────────⍟
├🤖 ᴍy ɴᴀᴍᴇ : {}
├🖥️ Dᴇᴠᴇʟᴏᴩᴇʀꜱ : {}
├👨‍💻 Pʀᴏɢʀᴀᴍᴇʀ : {}
├📕 Lɪʙʀᴀʀy : {}
├✏️ Lᴀɴɢᴜᴀɢᴇ: {}
├💾 Dᴀᴛᴀ Bᴀꜱᴇ: {}
├📊 ᴠᴇʀsɪᴏɴ: <a href=https://github.com/ThanhDora>{}</a></b>     
╰───────────────⍟ """

    HELP_TXT = """
<b>Hướng dẫn</b>

<b>Đổi tên file</b>
Gửi file, rồi nhập tên mới theo hướng dẫn của bot.

<b>Cài đặt</b>
Dùng các nút trong menu: Ảnh bìa, Chú thích, Tiền tố / Hậu tố, Metadata, Gói của tôi.

Hỗ trợ: <a href=https://t.me/DoraTeamMods>@DoraTeamMods</a>
"""

    UPGRADE_PREMIUM= """
•⪼ ★𝘗𝘭𝘢𝘯𝘴    -  ⏳𝘋𝘢𝘵𝘦 - 💸𝘗𝘳𝘪𝘤𝘦 
•⪼ 🥉𝘉𝘳𝘰𝘯𝘻𝘦  -   3𝘥𝘢𝘺𝘴 -   39
•⪼ 🥈𝘚𝘪𝘭𝘷𝘦𝘳   -   7𝘥𝘢𝘺𝘴 -   59
•⪼ 🥇𝘎𝘰𝘭𝘥    -  15𝘥𝘢𝘺𝘴 -  99
•⪼ 🏆𝘗𝘭𝘢𝘵𝘪𝘯𝘶𝘮 -  1𝘮𝘰𝘯𝘵𝘩 -  179
•⪼ 💎𝘋𝘪𝘢𝘮𝘰𝘯𝘥 -  2𝘮𝘰𝘯𝘵𝘩 -  339

- 𝘋𝘢𝘪𝘭𝘺 𝘜𝘱𝘭𝘰𝘢𝘥 𝘓𝘪𝘮𝘪𝘵 𝘜𝘯𝘭𝘪𝘮𝘪𝘵𝘦𝘥
- 𝘋𝘪𝘴𝘤𝘰𝘶𝘯𝘵 𝘈𝘭𝘭 𝘗𝘭𝘢𝘯 𝘙𝘴.9
    """
    
    UPGRADE_PLAN= """
𝘗𝘭𝘢𝘯: 𝘗𝘳𝘰
𝘋𝘢𝘵𝘦: 1 𝘮𝘰𝘯𝘵𝘩 
𝘗𝘳𝘪𝘤𝘦: 179
𝘓𝘪𝘮𝘪𝘵: 100 𝘎𝘉

𝘗𝘭𝘢𝘯: 𝘜𝘭𝘵𝘢 𝘗𝘳𝘰 
𝘋𝘢𝘵𝘦: 1 𝘮𝘰𝘯𝘵𝘩 
𝘗𝘳𝘪𝘤𝘦: 199
𝘓𝘪𝘮𝘪𝘵: 1000 𝘎𝘉

- 𝘋𝘪𝘴𝘤𝘰𝘶𝘯𝘵 𝘈𝘭𝘭 𝘗𝘭𝘢𝘯 𝘙𝘴.9
    """
    
    THUMBNAIL = """
<b>Ảnh bìa</b>

Mở menu Ảnh bìa để xem, đặt hoặc xoá. Bạn cũng có thể gửi một ảnh bất kỳ để đặt ảnh bìa.
"""
    CAPTION= """
<b>Chú thích</b>

Mở menu Chú thích để xem, đặt hoặc xoá. Có thể dùng {filename}, {filesize}, {duration}.
"""
    BOT_STATUS = """
⚡️ ʙᴏᴛ sᴛᴀᴛᴜs ⚡️

⌚️ ʙᴏᴛ ᴜᴩᴛɪᴍᴇ: `{}`
👭 ᴛᴏᴛᴀʟ ᴜsᴇʀꜱ: `{}`
💸 ᴛᴏᴛᴀʟ ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀs: `{}`
֍ ᴜᴘʟᴏᴀᴅ: `{}`
⊙ ᴅᴏᴡɴʟᴏᴀᴅ: `{}`
"""
    LIVE_STATUS = """
⚡ ʟɪᴠᴇ sᴇʀᴠᴇʀ sᴛᴀᴛᴜs ⚡

ᴜᴘᴛɪᴍᴇ: `{}`
ᴄᴘᴜ: `{}%`
ʀᴀᴍ: `{}%` 
ᴛᴏᴛᴀʟ ᴅɪsᴋ: `{}`
ᴜsᴇᴅ sᴘᴀᴄᴇ: `{} {}%`
ғʀᴇᴇ sᴘᴀᴄᴇ: `{}`
ᴜᴘʟᴏᴀᴅ: `{}`
ᴅᴏᴡɴʟᴏᴀᴅ: `{}`
V𝟹.𝟶.𝟶 [STABLE]
"""
    CUSTOM_FILE_NAME = """
<b>Tiền tố / Hậu tố</b>

Mở menu Tiền tố / Hậu tố để xem, đặt hoặc xoá chữ đứng trước và sau tên file khi đổi tên.
"""

    DIGITAL_METADATA = """
<b>Metadata</b>

Mở menu Metadata để bật/tắt và đặt mã tùy chỉnh.

Ví dụ:
`--change-title @DoraTeamMods
--change-author @DoraTeamMods`

Hỗ trợ: @DoraTeamMods
"""
    
    SEND_METADATA = """
❪ SET CUSTOM METADATA ❫

☞ Fᴏʀ Exᴀᴍᴘʟᴇ:-

`--change-title @DoraTeamMods
--change-video-title @DoraTeamMods
--change-audio-title @DoraTeamMods
--change-subtitle-title @DoraTeamMods
--change-author @DoraTeamMods`

📥 Fᴏʀ Hᴇʟᴘ Cᴏɴᴛ. @DoraTeamMods
"""
    
    RKN_PROGRESS = """<b>
╭━━━━━━━━◉🚀◉━━━━━━━━╮
┃   𝗥𝗞𝗡 𝗣𝗥𝗢𝗖𝗘𝗦𝗦𝗜𝗡𝗚...❱━➣  
┣━━━━━━━━━━━━━━━━━━━━╯
┣⪼ 📦 𝗦𝗜𝗭𝗘: {1} | {2}
┣⪼ 📊 𝗗𝗢𝗡𝗘: {0}%
┣⪼ 🚀 𝗦𝗣𝗘𝗘𝗗: {3}/s
┣⪼ ⏰ 𝗘𝗧𝗔: {4}
╰━━━━━━━━◉🔥◉━━━━━━━━╯</b>"""

# ThanhDora | DoraTeam | https://github.com/ThanhDora | @DoraTeamMods
