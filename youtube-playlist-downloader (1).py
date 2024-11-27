from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import yt_dlp

def clean_youtube_url(url):
    """Clean YouTube URL by removing playlist parameters"""
    video_id_start = url.find('watch?v=')
    if video_id_start != -1:
        video_id_start += 8
        video_id_end = url.find('&', video_id_start)
        if video_id_end == -1:
            video_id_end = len(url)
        return f"https://www.youtube.com/watch?v={url[video_id_start:video_id_end]}"
    return url

def get_mix_videos(mix_url, num_videos=25):
    """Extract video URLs from YouTube Mix"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--mute-audio")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    video_urls = []
    
    try:
        print("Loading playlist page...")
        driver.get(mix_url)
        time.sleep(3)
        
        while len(video_urls) < num_videos:
            driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
            time.sleep(2)
            
            items = driver.find_elements(By.CSS_SELECTOR, 
                "a.yt-simple-endpoint.style-scope.ytd-playlist-panel-video-renderer")
            
            for item in items:
                href = item.get_attribute("href")
                if href and "watch?v=" in href:
                    clean_url = clean_youtube_url(href)
                    if clean_url not in video_urls:
                        video_urls.append(clean_url)
            
            video_urls = list(dict.fromkeys(video_urls))
            print(f"\rFound {len(video_urls)} videos...", end="")
            
            if len(video_urls) >= num_videos:
                break
                
    finally:
        driver.quit()
    
    return video_urls[:num_videos]

def download_video(url, output_path="downloads"):
    """Download a single video using yt-dlp"""
    try:
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        # Configure yt-dlp options
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'merge_output_format': 'mp4',  # This ensures audio and video are merged
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'ignoreerrors': True,
            'no_warnings': False,
            'quiet': False,
            'progress': True,
            'extract_flat': False,
            'writethumbnail': False,
            'postprocessors': [{  # Ensure we're using the proper postprocessor
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
            'progress_hooks': [lambda d: print(f"\rDownloading: {d['_percent_str']} of {d['_total_bytes_str']}", end="") 
                             if d['status'] == 'downloading' else None],
        }

        # Download the video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            if info:
                print(f"\nSuccessfully downloaded: {info.get('title', 'Unknown title')}")
                return True
            return False

    except Exception as e:
        print(f"Error downloading video: {str(e)}")
        return False

def download_mix(mix_url, num_videos=25, output_path="downloads"):
    """Download videos from a YouTube Mix playlist"""
    print(f"Starting YouTube Mix downloader...")
    video_urls = get_mix_videos(mix_url, num_videos)
    
    print(f"\nFound {len(video_urls)} videos to download")
    successful_downloads = 0
    
    for index, video_url in enumerate(video_urls, 1):
        print(f"\n[{index}/{len(video_urls)}] Processing video...")
        if download_video(video_url, output_path):
            successful_downloads += 1
        time.sleep(1)  # Small delay between downloads
    
    print(f"\nDownload complete! Successfully downloaded {successful_downloads} videos.")

if __name__ == "__main__":
    try:
        mix_url = input("Enter YouTube Mix URL: ").strip()
        
        try:
            num_videos = int(input("Enter number of videos to download (default 25): "))
        except:
            num_videos = 25
        
        output_dir = input("Enter output directory (press Enter for 'downloads'): ").strip()
        if not output_dir:
            output_dir = "downloads"
        
        download_mix(mix_url, num_videos, output_dir)
        
    except KeyboardInterrupt:
        print("\n\nDownload interrupted by user")
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")