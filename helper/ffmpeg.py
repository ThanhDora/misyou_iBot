import json
import logging
import os
import subprocess

from helper.utils import metadata_text

_log = logging.getLogger(__name__)

# Audio/video containers ffmpeg can reasonably remux. Archives, apps, and docs are excluded.
MEDIA_EXTENSIONS = frozenset({
    "mp4", "mkv", "webm", "avi", "mov", "m4v", "flv", "wmv", "mpeg", "mpg", "mpe",
    "3gp", "3g2", "ts", "m2ts", "mts", "vob", "ogv", "asf", "f4v", "rm", "rmvb",
    "divx", "mxf", "m1v", "m2v", "ogm", "dv", "mpv", "m2t",
    "mp3", "m4a", "aac", "flac", "wav", "ogg", "opus", "wma", "aiff", "aif", "aifc",
    "amr", "ac3", "eac3", "dts", "mp2", "mpga", "oga", "weba", "mka", "ra", "alac",
})


def is_media_file(path, mime_type=None):
    """True only for real audio/video files (by extension and/or MIME type)."""
    name = os.path.basename(path or "")
    ext = os.path.splitext(name)[1].lower().lstrip(".")
    if ext in MEDIA_EXTENSIONS:
        return True
    if mime_type:
        mt = str(mime_type).lower().split(";", 1)[0].strip()
        if mt.startswith("video/") or mt.startswith("audio/"):
            return True
    return False


def _safe_media_path(path):
    """Absolute path that ffmpeg/ffprobe will not treat as an option (e.g. '- file.mp4')."""
    if not path:
        return path
    path = os.path.abspath(path)
    if path.startswith("-"):
        path = os.path.join(os.curdir, path)
    return path


def _remove_if_exists(path):
    if path and os.path.lexists(path):
        try:
            os.remove(path)
        except OSError:
            pass


async def change_metadata(input_file, output_file, metadata):
    """Write metadata into an audio/video file.

    Returns True only when a usable output file was written. Any probe/ffmpeg
    failure, non-media input, or unexpected error returns False and must not raise.
    """
    if not input_file or not os.path.isfile(input_file):
        return False
    if not is_media_file(input_file):
        return False

    in_path = _safe_media_path(input_file)
    out_path = _safe_media_path(output_file)
    if not in_path or not out_path:
        return False

    out_dir = os.path.dirname(out_path)
    if out_dir:
        try:
            os.makedirs(out_dir, exist_ok=True)
        except OSError:
            _log.warning("Cannot create metadata output dir %s", out_dir, exc_info=True)
            return False

    try:
        author, title, video_title, audio_title, subtitle_title = await metadata_text(metadata)

        probe = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-show_streams",
                "-print_format", "json",
                "-i", in_path,
            ],
            check=False,
            capture_output=True,
            timeout=60,
        )
        if probe.returncode != 0:
            _log.info(
                "ffprobe skipped/failed for %s (code %s): %s",
                in_path,
                probe.returncode,
                (probe.stderr or b"")[:400],
            )
            return False

        try:
            data = json.loads(probe.stdout or b"{}")
        except (TypeError, ValueError, json.JSONDecodeError):
            _log.info("ffprobe returned invalid JSON for %s", in_path)
            return False

        streams = data.get("streams") or []
        if not any(isinstance(s, dict) and s.get("codec_type") in ("video", "audio") for s in streams):
            return False

        cmd = [
            "ffmpeg",
            "-y",
            "-i", in_path,
            "-map", "0",
            "-c:v", "copy",
            "-c:a", "copy",
            "-c:s", "copy",
            "-metadata", f"title={title}",
            "-metadata", f"author={author}",
        ]
        for stream in streams:
            if not isinstance(stream, dict):
                continue
            idx = stream.get("index")
            if idx is None:
                continue
            codec_type = stream.get("codec_type")
            if codec_type == "video" and video_title:
                cmd.extend([f"-metadata:s:{idx}", f"title={video_title}"])
            elif codec_type == "audio" and audio_title:
                cmd.extend([f"-metadata:s:{idx}", f"title={audio_title}"])
            elif codec_type == "subtitle" and subtitle_title:
                cmd.extend([f"-metadata:s:{idx}", f"title={subtitle_title}"])

        cmd.extend(["-metadata", "comment=Added by @DoraTeamMods"])
        cmd.extend(["-f", "matroska"])
        cmd.append(out_path)

        result = subprocess.run(cmd, check=False, capture_output=True, timeout=600)
        if result.returncode != 0:
            _log.info(
                "ffmpeg metadata failed for %s (code %s): %s",
                in_path,
                result.returncode,
                (result.stderr or b"")[:400],
            )
            _remove_if_exists(out_path)
            if out_path != output_file:
                _remove_if_exists(output_file)
            return False

        if not os.path.isfile(out_path) or os.path.getsize(out_path) == 0:
            _remove_if_exists(out_path)
            if out_path != output_file:
                _remove_if_exists(output_file)
            return False
        return True
    except Exception:
        _log.warning("change_metadata failed for %s", input_file, exc_info=True)
        _remove_if_exists(out_path)
        if output_file and output_file != out_path:
            _remove_if_exists(output_file)
        return False
