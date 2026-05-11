import os
import shutil
import tempfile
from pathlib import Path

import streamlit as st
import yt_dlp

try:
    from yt_dlp.version import __version__ as YTDLP_VERSION
except Exception:
    YTDLP_VERSION = "unknown"


# -----------------------------
# Add Deno installed by pip to PATH
# -----------------------------
def add_deno_to_path():
    try:
        import deno

        deno_bin = deno.find_deno_bin()
        deno_dir = os.path.dirname(deno_bin)

        current_path = os.environ.get("PATH", "")
        if deno_dir not in current_path:
            os.environ["PATH"] = deno_dir + os.pathsep + current_path

        return deno_bin

    except Exception:
        return shutil.which("deno")


DENO_BIN = add_deno_to_path()


# -----------------------------
# Streamlit Page Setup
# -----------------------------
st.set_page_config(
    page_title="YouTube Downloader",
    page_icon="🎬",
    layout="centered"
)

st.title("🎬 YouTube Video & MP3 Downloader")
st.caption("Download only videos you own or have permission to download.")

url = st.text_input("Enter YouTube Video URL")

download_type = st.radio(
    "Choose Download Type",
    ["Video (MP4)", "Audio (MP3)"]
)


# -----------------------------
# Status Helpers
# -----------------------------
def ffmpeg_available():
    return shutil.which("ffmpeg") is not None


def deno_available():
    return shutil.which("deno") is not None or DENO_BIN is not None


def curl_cffi_available():
    try:
        import curl_cffi
        return True
    except Exception:
        return False


def get_latest_file(folder_path, allowed_suffixes=None):
    folder = Path(folder_path)

    if not folder.exists():
        return None

    files = [file for file in folder.iterdir() if file.is_file()]

    if allowed_suffixes:
        filtered_files = [
            file for file in files
            if file.suffix.lower() in allowed_suffixes
        ]

        if filtered_files:
            files = filtered_files

    if not files:
        return None

    return max(files, key=lambda file: file.stat().st_mtime)


# -----------------------------
# Sidebar Debug Info
# -----------------------------
with st.sidebar:
    st.subheader("System Status")

    st.write(f"yt-dlp: `{YTDLP_VERSION}`")

    if ffmpeg_available():
        st.success("FFmpeg found")
    else:
        st.error("FFmpeg missing")

    if deno_available():
        st.success("Deno found")
    else:
        st.warning("Deno missing")

    if curl_cffi_available():
        st.success("Browser impersonation available")
    else:
        st.warning("Browser impersonation missing")


# -----------------------------
# yt-dlp Options
# -----------------------------
def base_ydl_options(temp_dir):
    options = {
        "outtmpl": os.path.join(temp_dir, "%(title).80s-%(id)s.%(ext)s"),
        "noplaylist": True,
        "restrictfilenames": True,
        "quiet": True,
        "no_warnings": True,
        "retries": 10,
        "fragment_retries": 10,
        "socket_timeout": 30,
        "ignoreerrors": False,
        "check_formats": True,
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Referer": "https://www.youtube.com/",
            "Accept-Language": "en-US,en;q=0.9",
        },
    }

    if curl_cffi_available():
        options["impersonate"] = "chrome"

    return options


# -----------------------------
# Download Video
# -----------------------------
def download_video(video_url):
    last_error = None

    formats_to_try = []

    if ffmpeg_available():
        formats_to_try.append(
            "bv*[ext=mp4][height<=720]+ba[ext=m4a]/"
            "b[ext=mp4][height<=720]/"
            "b[height<=720]"
        )

    formats_to_try.append(
        "b[ext=mp4][height<=720]/"
        "b[height<=720]/"
        "b"
    )

    for selected_format in formats_to_try:
        temp_dir = tempfile.mkdtemp()

        ydl_opts = base_ydl_options(temp_dir)
        ydl_opts["format"] = selected_format

        if ffmpeg_available():
            ydl_opts["merge_output_format"] = "mp4"

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])

            downloaded_file = get_latest_file(
                temp_dir,
                allowed_suffixes={".mp4", ".webm", ".mkv"}
            )

            if downloaded_file:
                return downloaded_file

        except Exception as error:
            last_error = error

    raise RuntimeError(last_error)


# -----------------------------
# Download Audio
# -----------------------------
def download_audio(video_url):
    if not ffmpeg_available():
        raise RuntimeError(
            "FFmpeg is missing. Make sure packages.txt contains: ffmpeg"
        )

    temp_dir = tempfile.mkdtemp()

    ydl_opts = base_ydl_options(temp_dir)
    ydl_opts.update({
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    })

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])

    downloaded_file = get_latest_file(
        temp_dir,
        allowed_suffixes={".mp3"}
    )

    if not downloaded_file:
        raise RuntimeError("Audio download failed. No MP3 file was created.")

    return downloaded_file


# -----------------------------
# Session State
# -----------------------------
if "download_data" not in st.session_state:
    st.session_state.download_data = None

if "download_name" not in st.session_state:
    st.session_state.download_name = None

if "download_mime" not in st.session_state:
    st.session_state.download_mime = None


# -----------------------------
# Main Download Button
# -----------------------------
if st.button("Download"):
    st.session_state.download_data = None
    st.session_state.download_name = None
    st.session_state.download_mime = None

    if not url.strip():
        st.error("❌ Please enter a valid YouTube URL")

    else:
        try:
            with st.spinner("Downloading... please wait."):
                if download_type == "Video (MP4)":
                    file_path = download_video(url.strip())

                    st.session_state.download_data = file_path.read_bytes()
                    st.session_state.download_name = file_path.name
                    st.session_state.download_mime = "video/mp4"

                    st.success("✅ Video downloaded successfully!")

                else:
                    file_path = download_audio(url.strip())

                    st.session_state.download_data = file_path.read_bytes()
                    st.session_state.download_name = file_path.name
                    st.session_state.download_mime = "audio/mpeg"

                    st.success("✅ MP3 downloaded successfully!")

        except Exception as e:
            st.error(f"❌ Error: {e}")

            st.warning(
                "If this is still a 403 Forbidden error, YouTube may be blocking "
                "downloads from Streamlit Cloud for this video or this cloud IP."
            )


# -----------------------------
# Download File Button
# -----------------------------
if st.session_state.download_data:
    st.download_button(
        label="⬇️ Save File",
        data=st.session_state.download_data,
        file_name=st.session_state.download_name,
        mime=st.session_state.download_mime
    )


st.markdown("---")
st.caption("⚠️ Respect copyright laws and platform terms.")
