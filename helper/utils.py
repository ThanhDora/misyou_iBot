# ThanhDora | DoraTeam | https://github.com/ThanhDora | @DoraTeamMods
"""
Apache License 2.0
"""

# extra imports
import asyncio
import math, time, re, datetime, pytz, os, json, tempfile, plistlib, zipfile, tarfile, shutil, logging
from io import BytesIO
from pathlib import Path
import aiohttp
import requests
from PIL import Image
from config import Config, rkn

_botlog = logging.getLogger(__name__)
BOTLOG_FILE = "BotLog.txt"
ITUNES_HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
ARTWORK_HEADERS = {**ITUNES_HEADERS, "Referer": "https://itunes.apple.com/"}
LOOKUP_COUNTRIES = ("us", "vn", "gb", "kr", "jp", "sg", "au", "ca")
def _artwork_url_larger(url):
    if not url:
        return url
    if "100x100" in url or "60x60" in url:
        return re.sub(r"\d+x\d+", "512x512", url, count=1)
    return url


def sanitize_filename_for_app(name):
    s = re.sub(r'[/\\:*?"<>|]', "", (name or "").strip())
    return (s[:200] or "App").strip()


def _append_artwork_url_to_botlog(bundle_id, source, url):
    try:
        with open(BOTLOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{datetime.datetime.now().isoformat()} - iTunes artwork URL | bundle_id={bundle_id} source={source} url={url}\n")
    except Exception:
        pass

# pyrogram imports
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram import errors

async def progress_for_pyrogram(current, total, ud_type, message, start):
    now = time.time()
    diff = now - start
    if round(diff % 5.00) == 0 or current == total:        
        percentage = current * 100 / total
        speed = current / diff
        elapsed_time = round(diff) * 1000
        time_to_completion = round((total - current) / speed) * 1000
        estimated_total_time = elapsed_time + time_to_completion

        elapsed_time = TimeFormatter(milliseconds=elapsed_time)
        estimated_total_time = TimeFormatter(milliseconds=estimated_total_time)

        progress = "{0}{1}".format(
            ''.join(["▣" for i in range(math.floor(percentage / 5))]),
            ''.join(["▢" for i in range(20 - math.floor(percentage / 5))])
        )            
        tmp = progress + rkn.RKN_PROGRESS.format( 
            round(percentage, 2),
            humanbytes(current),
            humanbytes(total),
            humanbytes(speed),            
            estimated_total_time if estimated_total_time != '' else "0 s"
        )
        try:
            await message.edit(
                text=f"{ud_type}\n\n{tmp}",               
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✖️ 𝙲𝙰𝙽𝙲𝙴𝙻 ✖️", callback_data="close")]])                                               
            )
        except:
            pass

def humanbytes(size):    
    if not size:
        return ""
    power = 2**10
    n = 0
    Dic_powerN = {0: ' ', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'ʙ'


def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "ᴅ, ") if days else "") + \
        ((str(hours) + "ʜ, ") if hours else "") + \
        ((str(minutes) + "ᴍ, ") if minutes else "") + \
        ((str(seconds) + "ꜱ, ") if seconds else "") + \
        ((str(milliseconds) + "ᴍꜱ, ") if milliseconds else "")
    return tmp[:-2] 

def convert(seconds):
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60      
    return "%d:%02d:%02d" % (hour, minutes, seconds)

async def send_log(b, u):
    if not Config.LOG_CHANNEL:
        return
    try:
        curr = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
        log_message = (
            "**--Nᴇᴡ Uꜱᴇʀ Sᴛᴀʀᴛᴇᴅ Tʜᴇ Bᴏᴛ--**\n\n"
            f"Uꜱᴇʀ: {u.mention}\n"
            f"Iᴅ: `{u.id}`\n"
            f"Uɴ: @{u.username}\n\n"
            f"Dᴀᴛᴇ: {curr.strftime('%d %B, %Y')}\n"
            f"Tɪᴍᴇ: {curr.strftime('%I:%M:%S %p')}\n\n"
            f"By: {b.mention}"
        )
        await b.send_message(Config.LOG_CHANNEL, log_message)
    except (errors.ChannelInvalid, errors.ChatWriteForbidden, errors.ChannelPrivate, errors.PeerIdInvalid):
        pass


async def send_pending_approval_notification(b, u):
    if not getattr(Config, "APPROVAL_REQUIRED", False):
        return
    curr = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
    msg = (
        "**⏳ User yêu cầu duyệt**\n\n"
        f"User: {u.mention}\n"
        f"ID: `{u.id}`\n"
        f"Username: @{u.username or '—'}\n\n"
        f"Thời gian: {curr.strftime('%d/%m/%Y %H:%M')}"
    )
    btn = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Duyệt", callback_data=f"aprv_{u.id}"),
        InlineKeyboardButton("❌ Từ chối", callback_data=f"rej_{u.id}")
    ]])
    async def _send_notify(b, chat_id, msg, btn):
        try:
            await b.send_message(chat_id, msg, reply_markup=btn)
            return True
        except Exception:
            return False
    sent = False
    gid = getattr(Config, "APPROVAL_GROUP_ID", None)
    if gid:
        sent = await _send_notify(b, gid, msg, btn) or sent
        if not sent and -1000000000000 < gid < 0:
            try:
                await b.send_message(-1000000000000 + gid, msg, reply_markup=btn)
                sent = True
            except Exception:
                pass
    if getattr(Config, "LOG_CHANNEL", None):
        sent = await _send_notify(b, Config.LOG_CHANNEL, msg, btn) or sent
    for admin_id in getattr(Config, "ADMIN", None) or []:
        try:
            aid = int(admin_id)
            sent = await _send_notify(b, aid, msg, btn) or sent
        except (ValueError, TypeError):
            pass

async def get_seconds_first(time_string):
    conversion_factors = {
        's': 1,
        'min': 60,
        'hour': 3600,
        'day': 86400,
        'month': 86400 * 30,
        'year': 86400 * 365
    }

    parts = time_string.split()
    total_seconds = 0

    for i in range(0, len(parts), 2):
        value = int(parts[i])
        unit = parts[i+1].rstrip('s')  # Remove 's' from unit
        total_seconds += value * conversion_factors.get(unit, 0)

    return total_seconds

async def get_seconds(time_string):
    conversion_factors = {
        's': 1,
        'min': 60,
        'hour': 3600,
        'day': 86400,
        'month': 86400 * 30,
        'year': 86400 * 365
    }

    total_seconds = 0
    pattern = r'(\d+)\s*(\w+)'
    matches = re.findall(pattern, time_string)

    for value, unit in matches:
        total_seconds += int(value) * conversion_factors.get(unit, 0)

    return total_seconds

async def add_prefix_suffix(input_string, prefix='', suffix=''):
    pattern = r'(?P<filename>.*?)(\.\w+)?$'
    match = re.search(pattern, input_string)
    
    if match:
        filename = match.group('filename')
        extension = match.group(2) or ''
        
        prefix_str = f"{prefix} " if prefix else ""
        suffix_str = f" {suffix}" if suffix else ""
        
        return f"{prefix_str}{filename}{suffix_str}{extension}"
    else:
        return input_string

async def remove_path(*paths):
    for path in paths:
        if path and os.path.lexists(path):
            os.remove(path)

async def metadata_text(metadata_text):
    author = None
    title = None
    video_title = None
    audio_title = None
    subtitle_title = None

    flags = [i.strip() for i in metadata_text.split('--')]
    for f in flags:
        if "change-author" in f:
            author = f[len("change-author"):].strip()
        if "change-title" in f:
            title = f[len("change-title"):].strip()
        if "change-video-title" in f:
            video_title = f[len("change-video-title"):].strip()
        if "change-audio-title" in f:
            audio_title = f[len("change-audio-title"):].strip()
        if "change-subtitle-title" in f:
            subtitle_title = f[len("change-subtitle-title"):].strip()

    return author, title, video_title, audio_title, subtitle_title


def _bundle_id_from_plist(plist):
    try:
        bundle_id = plist.get("CFBundleIdentifier")
        if bundle_id and isinstance(bundle_id, str):
            app_name = plist.get("CFBundleDisplayName") or plist.get("CFBundleName") or None
            version = plist.get("CFBundleShortVersionString") or plist.get("CFBundleVersion") or None
            return bundle_id, app_name, version
        filter_dict = plist.get("Filter")
        if isinstance(filter_dict, dict):
            bundles = filter_dict.get("Bundles")
            if isinstance(bundles, list):
                for b in bundles:
                    if b and isinstance(b, str):
                        return b, None, None
                    if b:
                        return str(b), None, None
            if isinstance(bundles, dict):
                for b in bundles:
                    if b:
                        return (b, None, None) if isinstance(b, str) else (str(b), None, None)
    except Exception:
        pass
    return None, None, None


def _scan_plists_for_bundle_id(root_dir):
    for dirpath, _, filenames in os.walk(root_dir):
        for name in filenames:
            if not name.lower().endswith(".plist"):
                continue
            path = os.path.join(dirpath, name)
            try:
                with open(path, "rb") as fp:
                    plist = plistlib.load(fp)
                bundle_id, app_name, version = _bundle_id_from_plist(plist)
                if bundle_id:
                    return bundle_id, app_name, version
            except Exception:
                continue
    return None, None, None


def extract_bundle_info_from_ipa(ipa_path):
    if not ipa_path or not os.path.lexists(ipa_path):
        return None, None, None
    try:
        with zipfile.ZipFile(ipa_path, "r") as z:
            for name in z.namelist():
                if name.startswith("Payload/") and name.endswith(".app/Info.plist"):
                    with z.open(name) as plist_file:
                        plist = plistlib.load(plist_file)
                        bundle_id = plist.get("CFBundleIdentifier")
                        if bundle_id and isinstance(bundle_id, str):
                            app_name = plist.get("CFBundleDisplayName") or plist.get("CFBundleName") or None
                            version = plist.get("CFBundleShortVersionString") or plist.get("CFBundleVersion") or None
                            return bundle_id, app_name, version
        with tempfile.TemporaryDirectory() as tmp:
            with zipfile.ZipFile(ipa_path, "r") as z:
                z.extractall(tmp)
            return _scan_plists_for_bundle_id(tmp)
    except Exception:
        return None, None, None


def _extract_data_tar_io_from_deb(deb_path):
    with open(deb_path, "rb") as f:
        data = f.read()
    if not data.startswith(b"!<arch>\n"):
        return None
    offset = 8
    while offset < len(data):
        header = data[offset:offset + 60]
        if len(header) < 60:
            break
        name = header[:16].decode("ascii", errors="ignore").strip()
        try:
            size = int(header[48:58].decode("ascii", errors="ignore").strip())
        except ValueError:
            break
        offset += 60
        if offset + size > len(data):
            break
        file_data = data[offset:offset + size]
        offset += size
        if offset % 2:
            offset += 1
        if name.startswith("data.tar"):
            return BytesIO(file_data)
    return None


def extract_bundle_info_from_deb(deb_path):
    if not deb_path or not os.path.lexists(deb_path):
        return None, None, None
    try:
        data_tar_io = _extract_data_tar_io_from_deb(deb_path)
        if not data_tar_io:
            return None, None, None
        with tempfile.TemporaryDirectory() as tmp:
            try:
                with tarfile.open(fileobj=data_tar_io, mode="r:*") as tar:
                    tar.extractall(tmp)
            except Exception:
                return None, None, None
            dylib_dir = os.path.join(tmp, "Library", "MobileSubstrate", "DynamicLibraries")
            if os.path.isdir(dylib_dir):
                for fname in os.listdir(dylib_dir):
                    if fname.endswith(".plist"):
                        try:
                            with open(os.path.join(dylib_dir, fname), "rb") as fp:
                                plist = plistlib.load(fp)
                            bundles = plist.get("Filter", {}).get("Bundles", [])
                            if isinstance(bundles, list) and bundles:
                                b = bundles[0]
                                return (b, None, None) if isinstance(b, str) else (str(b), None, None)
                        except Exception:
                            continue
            return _scan_plists_for_bundle_id(tmp)
    except Exception:
        return None, None, None


def get_bundle_id_from_file(file_path, extension_hint=None):
    if not file_path or not os.path.lexists(file_path):
        return None, None, None
    low = (extension_hint or file_path).lower()
    if low.endswith(".ipa"):
        return extract_bundle_info_from_ipa(file_path)
    if low.endswith(".deb"):
        return extract_bundle_info_from_deb(file_path)
    return None, None, None


def _itunes_lookup_requests(bundle_id):
    for url in (
        f"https://itunes.apple.com/lookup?bundleId={bundle_id}",
        f"https://itunes.apple.com/lookup?bundleId={bundle_id}&country=us",
    ):
        try:
            data = requests.get(url, timeout=15, headers=ITUNES_HEADERS).json()
            if data.get("resultCount", 0) == 0:
                continue
            app = data["results"][0]
            icon = app.get("artworkUrl512") or app.get("artworkUrl100")
            return {"icon_512": app.get("artworkUrl512"), "icon_100": app.get("artworkUrl100"), "icon": icon, "track_name": app.get("trackName"), "version": app.get("version")}
        except Exception:
            continue
    return None


def _download_artwork_requests(icon_url):
    try:
        return requests.get(icon_url, timeout=10, headers=ITUNES_HEADERS).content
    except Exception:
        return None


def _fetch_icon_bytes_requests_sync(bundle_id):
    info = _itunes_lookup_requests(bundle_id)
    if not info or not info.get("icon"):
        return None
    return _download_artwork_requests(info["icon"])


async def _download_artwork_bytes(art_url):
    if not art_url:
        return None
    urls_to_try = [art_url]
    larger = _artwork_url_larger(art_url)
    if larger and larger != art_url:
        urls_to_try.append(larger)
    for headers in (ARTWORK_HEADERS, ITUNES_HEADERS):
        try:
            async with aiohttp.ClientSession() as session:
                for url in urls_to_try:
                    try:
                        async with session.get(url, timeout=aiohttp.ClientTimeout(total=25), headers=headers) as resp:
                            if resp.status == 200:
                                return await resp.read()
                    except Exception:
                        continue
        except Exception:
            pass
    return None


async def fetch_icon_from_bundle(bundle_id):
    bundle_id = (bundle_id or "").strip()
    if not bundle_id:
        return None
    try:
        assets = await get_itunes_assets(bundle_id)
        if assets:
            art = assets.get("icon_512") or assets.get("icon_100") or assets.get("icon_60") or ""
            if art:
                raw = await _download_artwork_bytes(art)
                if raw:
                    return raw
    except Exception:
        pass
    try:
        assets = await get_itunes_assets_via_search(bundle_id)
        if assets:
            art = assets.get("icon_512") or assets.get("icon_100") or assets.get("icon_60") or ""
            if art:
                raw = await _download_artwork_bytes(art)
                if raw:
                    return raw
    except Exception:
        pass
    try:
        assets = await get_itunes_assets_via_appstore_web(bundle_id)
        if assets:
            art = assets.get("icon_512") or assets.get("icon_100") or assets.get("icon_60") or ""
            if art:
                raw = await _download_artwork_bytes(art)
                if raw:
                    return raw
    except Exception:
        pass
    try:
        loop = asyncio.get_event_loop()
        raw = await loop.run_in_executor(None, _fetch_icon_bytes_requests_sync, bundle_id)
        if raw:
            return raw
    except Exception:
        pass
    return None


def create_itunes_artwork(icon_data, size=1024):
    img = Image.open(BytesIO(icon_data)).convert("RGBA")
    img.thumbnail((size, size), getattr(Image, "LANCZOS", Image.BICUBIC))
    bg = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    offset = ((size - img.width) // 2, (size - img.height) // 2)
    bg.paste(img, offset, img)
    out = BytesIO()
    bg.save(out, format="PNG", optimize=True)
    return out.getvalue()


def inject_itunes_artwork_into_ipa(ipa_path, artwork_bytes):
    ipa_path = Path(ipa_path).resolve()
    if not ipa_path.exists():
        return None
    fd, out_ipa = tempfile.mkstemp(suffix=".ipa", prefix="ipa_art_")
    os.close(fd)
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)
            with zipfile.ZipFile(ipa_path, "r") as z:
                z.extractall(temp_dir)
            (temp_dir / "iTunesArtwork").write_bytes(artwork_bytes)
            with zipfile.ZipFile(out_ipa, "w", zipfile.ZIP_DEFLATED) as new_zip:
                for f in temp_dir.rglob("*"):
                    if f.is_file():
                        new_zip.write(f, f.relative_to(temp_dir))
        return out_ipa
    except Exception:
        try:
            os.unlink(out_ipa)
        except Exception:
            pass
        return None


async def _lookup_one(bundle_id, country=None):
    url = f"https://itunes.apple.com/lookup?bundleId={bundle_id}"
    if country:
        url += f"&country={country}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15), headers=ITUNES_HEADERS) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
        if data.get("resultCount", 0) == 0:
            return None
        return data["results"][0]
    except Exception:
        return None


def _icon_urls_from_app(app, bundle_id, source):
    icon_512 = app.get("artworkUrl512")
    icon_100 = app.get("artworkUrl100")
    icon_60 = app.get("artworkUrl60")
    if icon_512:
        _append_artwork_url_to_botlog(bundle_id, source, icon_512)
    if icon_100 and icon_100 != icon_512:
        _append_artwork_url_to_botlog(bundle_id, source, icon_100)
    return icon_512 or icon_100 or icon_60


async def get_itunes_assets(bundle_id):
    app = await _lookup_one(bundle_id)
    if not app:
        for country in LOOKUP_COUNTRIES:
            app = await _lookup_one(bundle_id, country)
            if app:
                break
    if not app:
        return None
    _icon_urls_from_app(app, bundle_id, "lookup")
    return {
        "track_name": app.get("trackName"),
        "icon_512": app.get("artworkUrl512"),
        "icon_100": app.get("artworkUrl100"),
        "icon_60": app.get("artworkUrl60"),
        "screenshot_iphone": app.get("screenshotUrls", []),
        "screenshot_ipad": app.get("ipadScreenshotUrls", []),
        "version": app.get("version"),
    }


def _search_terms_for_bundle(bundle_id):
    b = (bundle_id or "").strip()
    if not b:
        return []
    parts = [p for p in b.split(".") if p]
    terms = [b]
    if len(parts) >= 2:
        terms.append(parts[-1])
        terms.append(parts[-2])
        terms.append(f"{parts[-2]} {parts[-1]}")
        last = parts[-1].lower()
        if "demon" in last or "kdemon" in last:
            terms.append("k-demon")
            terms.append("k-demon hunter")
        slug = parts[-1].replace("_", "-")
        if slug != parts[-1]:
            terms.append(slug)
    elif len(parts) == 1:
        terms.append(parts[0])
    return list(dict.fromkeys(terms))


async def _search_itunes_one(session, term, country):
    url = f"https://itunes.apple.com/search?term={re.escape(term)}&entity=software&limit=25&country={country}"
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15), headers=ITUNES_HEADERS) as resp:
            if resp.status != 200:
                return []
            data = await resp.json()
        return data.get("results") or []
    except Exception:
        return []


async def _lookup_by_track_id(session, track_id):
    url = f"https://itunes.apple.com/lookup?id={track_id}"
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15), headers=ITUNES_HEADERS) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
        if data.get("resultCount", 0) == 0:
            return None
        return data["results"][0]
    except Exception:
        return None


def _extract_app_ids_from_appstore_html(html):
    return list(dict.fromkeys(re.findall(r"/app/[^/]+/id(\d+)", html)))


async def get_itunes_assets_via_appstore_web(bundle_id):
    bundle_lower = (bundle_id or "").strip().lower()
    terms = _search_terms_for_bundle(bundle_id)
    try:
        async with aiohttp.ClientSession() as session:
            for term in terms[:6]:
                url = f"https://apps.apple.com/us/search?term={re.escape(term)}"
                try:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=20), headers=ITUNES_HEADERS) as resp:
                        if resp.status != 200:
                            continue
                        html = await resp.text()
                except Exception:
                    continue
                for app_id in _extract_app_ids_from_appstore_html(html)[:15]:
                    app = await _lookup_by_track_id(session, app_id)
                    if app and (app.get("bundleId") or "").strip().lower() == bundle_lower:
                        _icon_urls_from_app(app, bundle_id, "appstore_web")
                        return {
                            "track_name": app.get("trackName"),
                            "icon_512": app.get("artworkUrl512"),
                            "icon_100": app.get("artworkUrl100"),
                            "icon_60": app.get("artworkUrl60"),
                            "screenshot_iphone": app.get("screenshotUrls", []),
                            "screenshot_ipad": app.get("ipadScreenshotUrls", []),
                            "version": app.get("version"),
                        }
    except Exception:
        pass
    return None


async def get_itunes_assets_via_search(bundle_id):
    bundle_lower = (bundle_id or "").strip().lower()
    terms = _search_terms_for_bundle(bundle_id)
    countries = ("us", "vn", "gb", "kr", "jp")
    try:
        async with aiohttp.ClientSession() as session:
            for country in countries:
                for term in terms:
                    results = await _search_itunes_one(session, term, country)
                    for app in results:
                        if (app.get("bundleId") or "").strip().lower() == bundle_lower:
                            _icon_urls_from_app(app, bundle_id, "search")
                            return {
                                "track_name": app.get("trackName"),
                                "icon_512": app.get("artworkUrl512"),
                                "icon_100": app.get("artworkUrl100"),
                                "icon_60": app.get("artworkUrl60"),
                                "screenshot_iphone": app.get("screenshotUrls", []),
                                "screenshot_ipad": app.get("ipadScreenshotUrls", []),
                                "version": app.get("version"),
                            }
    except Exception:
        pass
    return None


def _fetch_track_name_requests_sync(bundle_id):
    info = _itunes_lookup_requests(bundle_id)
    return (info or {}).get("track_name") or None


async def fetch_itunes_track_name(bundle_id):
    bundle_id = (bundle_id or "").strip()
    if not bundle_id:
        return None
    try:
        assets = await get_itunes_assets(bundle_id)
        if assets:
            name = (assets.get("track_name") or "").strip()
            if name:
                return name
    except Exception:
        pass
    try:
        assets = await get_itunes_assets_via_search(bundle_id)
        if assets:
            name = (assets.get("track_name") or "").strip()
            if name:
                return name
    except Exception:
        pass
    try:
        assets = await get_itunes_assets_via_appstore_web(bundle_id)
        if assets:
            name = (assets.get("track_name") or "").strip()
            if name:
                return name
    except Exception:
        pass
    try:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _fetch_track_name_requests_sync, bundle_id)
    except Exception:
        pass
    return None


def _fetch_itunes_version_sync(bundle_id):
    info = _itunes_lookup_requests(bundle_id)
    return (info or {}).get("version") or None


async def fetch_itunes_version(bundle_id):
    bundle_id = (bundle_id or "").strip()
    if not bundle_id:
        return None
    for get_assets in (get_itunes_assets, get_itunes_assets_via_search, get_itunes_assets_via_appstore_web):
        try:
            assets = await get_assets(bundle_id)
            if assets:
                v = assets.get("version")
                if v is not None and str(v).strip():
                    return str(v).strip()
        except Exception:
            pass
    try:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _fetch_itunes_version_sync, bundle_id)
    except Exception:
        pass
    return None


async def fetch_itunes_artwork(bundle_id):
    bundle_id = (bundle_id or "").strip()
    if not bundle_id:
        return None, "Bundle ID trống."
    try:
        assets = await get_itunes_assets(bundle_id)
        if assets:
            art = assets.get("icon_512") or assets.get("icon_100") or assets.get("icon_60") or ""
            if art:
                raw = await _download_artwork_bytes(art)
                if raw:
                    suf = ".jpg" if art.lower().endswith(".jpg") or "jpg" in art else ".png"
                    fd, path = tempfile.mkstemp(suffix=suf, prefix="itunes_")
                    os.close(fd)
                    with open(path, "wb") as f:
                        f.write(raw)
                    return path, None
    except Exception:
        pass
    try:
        assets = await get_itunes_assets_via_search(bundle_id)
        if assets:
            art = assets.get("icon_512") or assets.get("icon_100") or assets.get("icon_60") or ""
            if art:
                raw = await _download_artwork_bytes(art)
                if raw:
                    suf = ".jpg" if art.lower().endswith(".jpg") or "jpg" in art else ".png"
                    fd, path = tempfile.mkstemp(suffix=suf, prefix="itunes_")
                    os.close(fd)
                    with open(path, "wb") as f:
                        f.write(raw)
                    return path, None
    except Exception:
        pass
    try:
        assets = await get_itunes_assets_via_appstore_web(bundle_id)
        if assets:
            art = assets.get("icon_512") or assets.get("icon_100") or assets.get("icon_60") or ""
            if art:
                raw = await _download_artwork_bytes(art)
                if raw:
                    suf = ".jpg" if art.lower().endswith(".jpg") or "jpg" in art else ".png"
                    fd, path = tempfile.mkstemp(suffix=suf, prefix="itunes_")
                    os.close(fd)
                    with open(path, "wb") as f:
                        f.write(raw)
                    return path, None
    except Exception:
        pass
    try:
        loop = asyncio.get_event_loop()
        raw = await loop.run_in_executor(None, _fetch_icon_bytes_requests_sync, bundle_id)
        if raw:
            suf = ".png"
            fd, path = tempfile.mkstemp(suffix=suf, prefix="itunes_")
            os.close(fd)
            with open(path, "wb") as f:
                f.write(raw)
            return path, None
    except Exception:
        pass
    try:
        with open(BOTLOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{datetime.datetime.now().isoformat()} - iTunes artwork NOT FOUND | bundle_id={bundle_id}\n")
    except Exception:
        pass
    return None, "Không tìm thấy trên iTunes."


async def fetch_itunes_artwork_and_inject_ipa(bundle_id, ipa_path):
    icon_bytes = await fetch_icon_from_bundle(bundle_id)
    if not icon_bytes:
        return None, None, "Không lấy được icon từ iTunes."
    artwork_bytes = create_itunes_artwork(icon_bytes, size=1024)
    modified_ipa = inject_itunes_artwork_into_ipa(ipa_path, artwork_bytes)
    if not modified_ipa:
        return None, None, "Không chèn được iTunesArtwork vào IPA."
    fd, thumb_path = tempfile.mkstemp(suffix=".png", prefix="itunes_thumb_")
    os.close(fd)
    try:
        with open(thumb_path, "wb") as f:
            f.write(artwork_bytes)
        return modified_ipa, thumb_path, None
    except Exception:
        try:
            os.unlink(thumb_path)
        except Exception:
            pass
        return modified_ipa, None, None


# ThanhDora | DoraTeam | @DoraTeamMods
