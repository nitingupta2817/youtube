import streamlit as st
import yt_dlp
import os

st.set_page_config(page_title="YouTube Downloader", page_icon="🎬")

st.title("🎬 YouTube Video & MP3 Downloader")

# Input URL
url = st.text_input("Enter YouTube Video URL")

# Download type
download_type = st.radio(
    "Choose Download Type",
    ["Video (MP4)", "Audio (MP3)"]
)

# Download button
if st.button("Download"):
    if not url:
        st.error("Please enter a valid YouTube URL")
    else:
        try:
            if download_type == "Video (MP4)":
                os.makedirs("videos", exist_ok=True)

                ydl_opts = {
                    'format': 'bestvideo+bestaudio/best',
                    'outtmpl': 'videos/%(title)s.%(ext)s',
                    'merge_output_format': 'mp4'
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                st.success("✅ Video downloaded successfully!")
                st.info("Check the `videos` folder")

            else:
                os.makedirs("audio", exist_ok=True)

                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': 'audio/%(title)s.%(ext)s',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                st.success("✅ MP3 downloaded successfully!")
                st.info("Check the `audio` folder")

        except Exception as e:
            st.error(f"❌ Error: {e}")

st.markdown("---")
st.caption("⚠️ Download videos only for personal use and respect copyright laws.")
