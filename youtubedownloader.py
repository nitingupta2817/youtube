import os
import glob
import streamlit as st
import yt_dlp

st.set_page_config(page_title="YouTube Downloader", page_icon="🎬")

st.title("🎬 YouTube Video & MP3 Downloader")

url = st.text_input("Enter YouTube Video URL")

download_type = st.radio(
    "Choose Download Type",
    ["Video (MP4)", "Audio (MP3)"]
)

def get_latest_file(folder):
    files = glob.glob(f"{folder}/*")
    if not files:
        return None
    return max(files, key=os.path.getctime)

if st.button("Download"):
    if not url:
        st.error("❌ Please enter a valid YouTube URL")
    else:
        try:
            if download_type == "Video (MP4)":
                os.makedirs("videos", exist_ok=True)

                ydl_opts = {
                    "format": "bestvideo+bestaudio/best",
                    "outtmpl": "videos/%(title).80s.%(ext)s",
                    "merge_output_format": "mp4",
                    "noplaylist": True,
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                latest_file = get_latest_file("videos")

                st.success("✅ Video downloaded successfully!")

                if latest_file:
                    with open(latest_file, "rb") as file:
                        st.download_button(
                            label="⬇️ Download MP4",
                            data=file,
                            file_name=os.path.basename(latest_file),
                            mime="video/mp4"
                        )

            else:
                os.makedirs("audio", exist_ok=True)

                ydl_opts = {
                    "format": "bestaudio/best",
                    "outtmpl": "audio/%(title).80s.%(ext)s",
                    "noplaylist": True,
                    "postprocessors": [{
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }],
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                latest_file = get_latest_file("audio")

                st.success("✅ MP3 downloaded successfully!")

                if latest_file:
                    with open(latest_file, "rb") as file:
                        st.download_button(
                            label="⬇️ Download MP3",
                            data=file,
                            file_name=os.path.basename(latest_file),
                            mime="audio/mpeg"
                        )

        except Exception as e:
            st.error(f"❌ Error: {e}")

st.markdown("---")
st.caption("⚠️ Download videos only for personal use and respect copyright laws.")
