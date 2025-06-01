import streamlit as st
import yt_dlp
import os
import tempfile
import time
import threading
from io import BytesIO
import base64


st.set_page_config(
    page_title="Multi-Platform Video Downloader",
    page_icon="",
    layout="wide",  
    initial_sidebar_state="auto"  
)

st.markdown("""
<style>
    /* Base styles */
    .main-header {
        text-align: center;
        padding: .5rem 1rem; 
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 1.5rem;
    }
    
    .platform-badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        margin: 0.25rem;
        border-radius: 20px;
        font-size: 0.875rem;
        font-weight: bold;
    }
    
    .youtube { background-color: #ff0000; color: white; }
    .facebook { background-color: #1877f2; color: white; }
    .linkedin { background-color: #0077b5; color: white; }
    .unknown { background-color: #6c757d; color: white; }
    
    .stButton > button {
        width: 100%;
        border-radius: 20px;
        height: 3rem;
        font-weight: bold;
        font-size: 1rem; /* Increased font size for readability */
        margin-bottom: 0.5rem; /* Added spacing for touch */
    }
    
    .download-section {
        background-color: #6c757d;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #28a745;
    }
    
    .info-section {
        background-color: #6c757d;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #2196f3;
    }
    
    # .error-section {
    #     background-color: #6c757d;
    #     padding: 1rem;
    #     border-radius: 10px;
    #     border-left: 4px solid #f44336;
    # }
    
    .video-container {
        background-color: #6c757d;
        padding: 1rem;
        border-radius: 10px;
        border: 2px solid #6c757d;
        margin-bottom: 1rem;
        width: 100%;
        box-sizing: border-box;
    }
    
    .video-container iframe {
        width: 100% !important;
        height: 40vw !important; 
        max-height: 315px !important;
        border-radius: 8px;
    }
    
    .thumbnail-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border: 2px solid #dee2e6;
        margin-bottom: 1rem;
        text-align: center;
        width: 100%;
        box-sizing: border-box;
    }
    
    .thumbnail-container img {
        max-width: 100% !important; 
        height: auto !important;
        max-height: 250px !important;
        border-radius: 8px;
    }
    
   
    @media (max-width: 768px) {
        .main-header {
            padding: 1rem 0.5rem;
            font-size: 0.9rem; 
        }
        
        .main-header h1 {
            font-size: 1.5rem;
        }
        
        .stButton > button {
            height: 2.5rem; 
            font-size: 0.9rem;
        }
        
        .video-container iframe {
            height: 50vw !important; 
            max-height: 200px !important;
        }
        
        .thumbnail-container img {
            max-height: 200px !important; 
        }
        
        .download-section, .info-section, .error-section {
            padding: 0.75rem; 
        }
        
      
        .stColumn {
            flex-direction: column !important;
        }
    }
    
    
    @media (max-width: 480px) {
        .main-header h1 {
            font-size: 1.2rem;
        }
        
        .platform-badge {
            font-size: 0.75rem;
            padding: 0.3rem 0.6rem;
        }
        
        .stButton > button {
            font-size: 0.8rem;
            height: 2.2rem;
        }
        
        .video-container iframe {
            height: 60vw !important;
            max-height: 180px !important;
        }
    }
</style>
""", unsafe_allow_html=True)

class StreamlitVideoDownloader:
    def __init__(self):
        self.supported_platforms = {
            'youtube': ['youtube.com', 'youtu.be'],
            'facebook': ['facebook.com', 'fb.com', 'fb.watch'],
            'linkedin': ['linkedin.com']
        }
        
    def detect_platform(self, url):
        """Detect which platform the URL belongs to"""
        if not url:
            return 'unknown'
            
        url_lower = url.lower()
        for platform, domains in self.supported_platforms.items():
            for domain in domains:
                if domain in url_lower:
                    return platform
        return 'unknown'
    
    def get_platform_badge(self, platform):
        """Get HTML badge for platform"""
        platform_info = {
            'youtube': ('YouTube', 'youtube'),
            'facebook': ('Facebook', 'facebook'),
            'linkedin': ('LinkedIn', 'linkedin'),
            'unknown': ('Unknown', 'unknown')
        }
        
        label, css_class = platform_info.get(platform, ('Unknown', 'unknown'))
        return f'<span class="platform-badge {css_class}">{label}</span>'
    
    def get_platform_specific_options(self, platform):
        """Get platform-specific yt-dlp options"""
        base_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        
        if platform == 'facebook':
            base_opts.update({
                'extractor_args': {
                    'facebook': {
                        'skip_dash_manifest': True,
                    }
                }
            })
        elif platform == 'linkedin':
            base_opts.update({
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            })
        
        return base_opts
    
    def format_duration(self, seconds):
        """Format duration from seconds to readable format"""
        if not seconds:
            return "Unknown"
        
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    def get_video_info(self, url, platform):
        """Get video information"""
        try:
            ydl_opts = self.get_platform_specific_options(platform)
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info, None
        except Exception as e:
            return None, str(e)
    
    def download_video(self, url, platform, quality, format_type, temp_dir):
        """Download video and return file path"""
        try:
            # Get platform-specific options
            ydl_opts = self.get_platform_specific_options(platform)
            ydl_opts['outtmpl'] = os.path.join(temp_dir, '%(title)s.%(ext)s')
            
            if format_type == 'mp3':
                ydl_opts.update({
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                })
            else:
                # Video format selection
                if platform == 'youtube':
                    if quality == 'best':
                        format_selector = 'best[ext=mp4]/best'
                    else:
                        format_selector = f'best[height<={quality}][ext=mp4]/best[height<={quality}]/best[ext=mp4]/best'
                elif platform == 'facebook':
                    if quality == 'best':
                        format_selector = 'best'
                    else:
                        format_selector = f'best[height<={quality}]/best'
                elif platform == 'linkedin':
                    format_selector = 'best'
                
                ydl_opts.update({
                    'format': format_selector,
                })
            
            # Download
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                # Find downloaded file
                for file in os.listdir(temp_dir):
                    if file.endswith(('.mp4', '.mp3', '.webm', '.mkv', '.avi', '.mov')):
                        return os.path.join(temp_dir, file), info, None
                
                return None, info, "No file found after download"
        
        except Exception as e:
            return None, None, str(e)

def main():
    # Initialize downloader
    downloader = StreamlitVideoDownloader()
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>Multi-Platform Video Downloader</h1>
        <p>Download videos from YouTube, Facebook, and LinkedIn</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'video_info' not in st.session_state:
        st.session_state.video_info = None
    if 'download_ready' not in st.session_state:
        st.session_state.download_ready = False
    
    # Sidebar
    with st.sidebar:
        st.header("🎛️ Settings")
        
        # Quality selection
        quality = st.selectbox(
            "📊 Video Quality",
            options=['best', '1080', '720', '480', '360', '240', '144'],
            format_func=lambda x: 'Best Available' if x == 'best' else f'{x}p',
            index=2  # Default to 720p
        )
        
        # Format selection
        format_type = st.selectbox(
            "📦 Format",
            options=['mp4', 'mp3'],
            format_func=lambda x: 'MP4 (Video)' if x == 'mp4' else 'MP3 (Audio Only)'
        )
        
        st.markdown("---")
        
  
    
    # Main content
    # Use container to ensure proper stacking on mobile
    with st.container():
        col1, col2 = st.columns([1, 1], gap="medium")
        
        with col1:
            # URL input
            st.markdown("### 🔗 Enter Video URL")
            url = st.text_input(
                "Paste your video URL here:",
                placeholder="https://www.youtube.com/watch?v=...",
                label_visibility="collapsed"
            )
            
            # Platform detection
            if url:
                platform = downloader.detect_platform(url)
                badge_html = downloader.get_platform_badge(platform)
                st.markdown(f"**Detected Platform:** {badge_html}", unsafe_allow_html=True)
                
                if platform == 'unknown':
                    st.error("❌ Unsupported platform. Please use YouTube, Facebook, or LinkedIn URLs.")
            
            # Action buttons
            col_info, col_download = st.columns(2)
            
            with col_info:
                if st.button("🔍 Get Video Info", disabled=not url or downloader.detect_platform(url) == 'unknown'):
                    platform = downloader.detect_platform(url)
                    
                    with st.spinner(f"🔍 Fetching video information from {platform.title()}..."):
                        info, error = downloader.get_video_info(url, platform)
                        
                        if error:
                            st.error(f"❌ Error: {error}")
                            st.session_state.video_info = None
                        else:
                            st.session_state.video_info = info
                            st.success("✅ Video information loaded!")
            
            with col_download:
                download_disabled = not url or downloader.detect_platform(url) == 'unknown'
                if st.button("⬇️ Download Video", disabled=download_disabled):
                    platform = downloader.detect_platform(url)
                    
                    # Create temporary directory
                    temp_dir = tempfile.mkdtemp()
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    try:
                        status_text.text(f"🚀 Starting download from {platform.title()}...")
                        progress_bar.progress(25)
                        
                        file_path, info, error = downloader.download_video(
                            url, platform, quality, format_type, temp_dir
                        )
                        
                        if error:
                            st.error(f"❌ Download failed: {error}")
                        elif file_path:
                            progress_bar.progress(100)
                            status_text.text("✅ Download completed!")
                            
                            # Prepare file for download
                            with open(file_path, 'rb') as file:
                                file_data = file.read()
                            
                            filename = os.path.basename(file_path)
                            file_size = len(file_data) / (1024 * 1024)  # MB
                            
                            st.success(f"🎉 Download ready! File size: {file_size:.2f} MB")
                            
                            # Download button
                            st.download_button(
                                label="💾 Download in Device",
                                data=file_data,
                                file_name=filename,
                                mime="application/octet-stream"
                            )
                        
                    except Exception as e:
                        st.error(f"❌ Unexpected error: {str(e)}")
                    finally:
                        # Cleanup
                        import shutil
                        try:
                            shutil.rmtree(temp_dir)
                        except:
                            pass
        
        with col2:
           
            if url and st.session_state.video_info:
                info = st.session_state.video_info
                platform = downloader.detect_platform(url)
                
               
                st.markdown("### 🎬 Video Preview")
                
                try:
                    
                    if platform == 'youtube':
                        
                        video_id = None
                        if 'youtube.com/watch?v=' in url:
                            video_id = url.split('watch?v=')[1].split('&')[0]
                        elif 'youtu.be/' in url:
                            video_id = url.split('youtu.be/')[1].split('?')[0]
                        
                        if video_id:
                            # Embed YouTube video in a fixed-size container
                            st.markdown("""
                            <div class="video-container">
                            """, unsafe_allow_html=True)
                            st.video(f"https://www.youtube.com/watch?v={video_id}")
                            st.markdown("""
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.info("📺 YouTube video detected but unable to preview")
                    
                    # For Facebook videos, show thumbnail if available
                    elif platform == 'facebook':
                        thumbnail_url = info.get('thumbnail')
                        if thumbnail_url:
                            st.markdown("""
                            <div class="thumbnail-container">
                            """, unsafe_allow_html=True)
                            st.image(thumbnail_url, caption="📘 Facebook Video Thumbnail")
                            st.markdown("""
                            </div>
                            """, unsafe_allow_html=True)
                            st.markdown(f"[🔗 Open in Facebook]({url})")
                        else:
                            st.info("📘 Facebook video detected. Click link to view on Facebook.")
                            st.markdown(f"[🔗 View on Facebook]({url})")
                    
                    # For LinkedIn videos, show thumbnail if available
                    elif platform == 'linkedin':
                        thumbnail_url = info.get('thumbnail')
                        if thumbnail_url:
                            st.markdown("""
                            <div class="thumbnail-container">
                            """, unsafe_allow_html=True)
                            st.image(thumbnail_url, caption="💼 LinkedIn Video Thumbnail")
                            st.markdown("""
                            </div>
                            """, unsafe_allow_html=True)
                            st.markdown(f"[🔗 Open in LinkedIn]({url})")
                        else:
                            st.info("💼 LinkedIn video detected. Click link to view on LinkedIn.")
                            st.markdown(f"[🔗 View on LinkedIn]({url})")
                    
                except Exception as e:
                    st.warning("⚠️ Unable to load video preview")
                
                st.markdown("---")
                
                # Video Information Section
                st.markdown("""
                <div class="info-section">
                    <h3>📹 Video Information</h3>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"** Title:** {info.get('title', 'N/A')}")
                
                # Platform-specific info
                if platform == 'youtube':
                    st.markdown(f"** Channel:** {info.get('uploader', 'N/A')}")
                    views = info.get('view_count', 0)
                    if views:
                        st.markdown(f"** Views:** {views:,}")
                else:
                    st.markdown(f"** Uploader:** {info.get('uploader', 'N/A')}")
                
                duration = downloader.format_duration(info.get('duration', 0))
                st.markdown(f"**⏱ Duration:** {duration}")
                
                upload_date = info.get('upload_date', 'N/A')
                if upload_date != 'N/A' and len(upload_date) == 8:
                    formatted_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"
                    st.markdown(f"**📅 Upload Date:** {formatted_date}")
                
                # Available formats
                formats = info.get('formats', [])
                if formats:
                    video_formats = set()
                    for f in formats:
                        if f.get('vcodec') != 'none' and f.get('height'):
                            video_formats.add(f.get('height'))
                    
                    if video_formats:
                        sorted_formats = sorted(video_formats, reverse=True)
                        format_text = ", ".join([f"{h}p" for h in sorted_formats])
                        st.markdown(f"** Available:** {format_text}")
            else:
                st.markdown("""
                <div class="info-section">
                    <h3>💡 How to Use</h3>
                    <ol>
                        <li>Paste a video URL above</li>
                        <li>Select quality and format in sidebar</li>
                        <li>Click "Get Video Info" to preview</li>
                        <li>Click "Download Video" to start</li>
                    </ol>
                </div>
                """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #6c757d; padding: 1rem 0;">
        <p>Multi-Platform Video Downloader | Made by Md Al Amin Tokder</p>
        <p><small>Supports YouTube, Facebook, and LinkedIn</small></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
