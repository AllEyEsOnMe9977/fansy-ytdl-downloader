import os
import re
from pytubefix import YouTube
from pytubefix.cli import on_progress

# Try to import Playlist (it may be available at the top level or via a contrib package)
try:
    from pytubefix import Playlist
except ImportError:
    from pytubefix.contrib.playlist import Playlist

# --- Helper Functions ---

def safe_name(name, max_length=255):
    """
    Sanitize a string to be safe as a filename or folder name.
    """
    safe = re.sub(r'[\\/*?:"<>|]', "", name)
    safe = safe.strip().replace(" ", "_")
    return safe[:max_length]

def merge_video_audio(video_path, audio_path, output_path):
    """
    Merge video and audio files using FFmpeg.
    This version re-encodes the audio to AAC at 128kbps and 48000Hz.
    """
    command = (
        f'ffmpeg -y -i "{video_path}" -i "{audio_path}" '
        f'-c:v copy -c:a aac -b:a 128k -ar 48000 "{output_path}"'
    )
    print("Running FFmpeg command:")
    print(command)
    ret = os.system(command)
    if ret != 0:
        print("FFmpeg merging failed!")
    else:
        print("Merging complete!")
    return output_path

def res_to_int(res):
    """
    Convert a resolution string like '720p' to an integer (e.g. 720).
    """
    if res is None:
        return 0
    try:
        return int(res.rstrip("p"))
    except Exception:
        return 0

def choose_best_video_combo(yt):
    """
    For a given YouTube object, select the best video+audio combination stream
    with a resolution up to 1080p.
    
    - It collects all video streams (progressive and video-only) that have a resolution ≤ 1080p.
    - It finds the maximum available resolution.
    - Among streams at that resolution:
        * If one or more are progressive (include audio), it chooses the one with the highest audio bitrate.
        * Otherwise, it selects the best video-only stream and pairs it with the best audio-only stream
          (based on highest bitrate) for merging.
    
    Returns a tuple: (mode, video_stream, audio_stream)
      - mode is "progressive" if a combined stream is chosen,
      - or "merge" if separate streams need to be downloaded and merged.
      - When mode is "merge", audio_stream is not None.
    """
    # Get all video streams (both progressive and video-only)
    video_streams = [s for s in yt.streams if s.mime_type.startswith("video")]
    # Filter streams with a defined resolution that are ≤ 1080p
    filtered = [s for s in video_streams if s.resolution and res_to_int(s.resolution) <= 1080]
    if not filtered:
        return None, None, None

    # Sort descending by resolution
    filtered.sort(key=lambda s: res_to_int(s.resolution), reverse=True)
    best_res = res_to_int(filtered[0].resolution)
    # Group streams that have the best available resolution
    best_group = [s for s in filtered if res_to_int(s.resolution) == best_res]

    # If any in best_group are progressive (include audio), choose the one with highest audio bitrate.
    progressive_streams = [s for s in best_group if getattr(s, "includes_audio_track", False)]
    if progressive_streams:
        def audio_bitrate(s):
            try:
                return int(s.abr.rstrip("kbps")) if s.abr and s.abr.rstrip("kbps").isdigit() else 0
            except Exception:
                return 0
        progressive_streams.sort(key=audio_bitrate, reverse=True)
        return "progressive", progressive_streams[0], None
    else:
        # Otherwise, use the best video-only stream from best_group.
        best_video = best_group[0]
        # Then choose the best audio-only stream by bitrate.
        audio_streams = list(yt.streams.filter(only_audio=True))
        if audio_streams:
            def audio_bitrate(s):
                try:
                    return int(s.abr.rstrip("kbps")) if s.abr and s.abr.rstrip("kbps").isdigit() else 0
                except Exception:
                    return 0
            audio_streams.sort(key=audio_bitrate, reverse=True)
            best_audio = audio_streams[0]
        else:
            best_audio = None
        return "merge", best_video, best_audio

# --- Download Functions ---

def download_single_video_manual(yt, base_folder):
    """
    For a single video, display all available streams for manual selection.
    """
    video_folder = os.path.join(base_folder, safe_name(yt.title))
    os.makedirs(video_folder, exist_ok=True)
    
    print("\nAvailable Streams:")
    streams = list(yt.streams)
    for idx, stream in enumerate(streams):
        resolution = getattr(stream, "resolution", "N/A")
        abr = getattr(stream, "abr", "N/A")
        print(f"Index: {idx} | Itag: {stream.itag} | Type: {stream.mime_type} | "
              f"Resolution: {resolution} | Bitrate: {abr}")
    
    choice = input("\nSelect a stream (enter index): ").strip()
    try:
        idx = int(choice)
        chosen_stream = streams[idx]
    except (ValueError, IndexError):
        print("Invalid selection!")
        return
    
    print(f"\nDownloading selected stream (Itag {chosen_stream.itag})...")
    try:
        chosen_stream.download(output_path=video_folder)
        print("Download complete!")
    except Exception as e:
        print("Error during download:", e)

def download_single_video_auto(yt, mode, base_folder):
    """
    Automatic download for a single video.
    
    If mode is "audio": downloads the best audio-only stream.
    If mode is "video": automatically selects the best video+audio combination using choose_best_video_combo.
    """
    video_folder = os.path.join(base_folder, safe_name(yt.title))
    os.makedirs(video_folder, exist_ok=True)
    
    if mode == "audio":
        stream = yt.streams.get_audio_only()
        if stream is None:
            print("No audio stream found!")
            return
        filename = f"{safe_name(yt.title)}_audio.mp4"
        try:
            stream.download(output_path=video_folder, filename=filename)
            print(f"Audio downloaded for: {yt.title}")
        except Exception as e:
            print("Error downloading audio:", e)
    elif mode == "video":
        decision, video_stream, audio_stream = choose_best_video_combo(yt)
        if decision is None:
            print("Could not determine a valid stream for video download.")
            return
        
        base = safe_name(yt.title)
        if decision == "progressive":
            filename = f"{base}.mp4"
            try:
                video_stream.download(output_path=video_folder, filename=filename)
                print(f"Video downloaded (progressive) for: {yt.title}")
            except Exception as e:
                print("Error downloading progressive video:", e)
        elif decision == "merge":
            video_filename = f"{base}_video.mp4"
            audio_filename = f"{base}_audio.mp4"
            merged_filename = f"{base}.mp4"
            video_path = os.path.join(video_folder, video_filename)
            audio_path = os.path.join(video_folder, audio_filename)
            merged_path = os.path.join(video_folder, merged_filename)
            try:
                print(f"Downloading video-only stream for: {yt.title}")
                video_stream.download(output_path=video_folder, filename=video_filename)
                print(f"Downloading audio stream for: {yt.title}")
                audio_stream.download(output_path=video_folder, filename=audio_filename)
            except Exception as e:
                print("Error downloading streams:", e)
                return
            print(f"Merging video and audio for: {yt.title}")
            merge_video_audio(video_path, audio_path, merged_path)
            # Remove temporary files
            try:
                os.remove(video_path)
                os.remove(audio_path)
                print("Temporary files removed.")
            except Exception as e:
                print("Error cleaning up temporary files:", e)
    else:
        print("Invalid mode for auto download.")

def download_playlist(playlist_url, mode, base_folder):
    """
    Download an entire playlist.
    
    For mode "audio": downloads the best audio-only stream for each video.
    For mode "video": for each video it automatically selects the best video+audio combination
    (using our logic that considers maximum resolution up to 1080p and then highest bitrate)
    and merges separate streams if needed.
    
    Files are stored under:
      base_folder / <Safe_Playlist_Title> / <mode> / <Safe_Video_Title>/
    """
    try:
        pl = Playlist(playlist_url)
    except Exception as e:
        print("Error initializing Playlist:", e)
        return
    
    pl_title = pl.title if pl.title else "Untitled_Playlist"
    pl_folder = os.path.join(base_folder, safe_name(pl_title), mode)
    os.makedirs(pl_folder, exist_ok=True)
    
    print(f"\nPlaylist Title: {pl.title}")
    print(f"Total Videos: {len(pl.video_urls)}")
    
    for idx, video_url in enumerate(pl.video_urls, start=1):
        print(f"\n--- Video {idx}/{len(pl.video_urls)} ---")
        try:
            yt = YouTube(
                video_url,
                use_oauth=True,
                allow_oauth_cache=True,
                on_progress_callback=on_progress
            )
        except Exception as e:
            print(f"Error initializing video {video_url}: {e}")
            continue
        
        print("Title:", yt.title)
        if mode == "audio":
            download_single_video_auto(yt, "audio", pl_folder)
        elif mode == "video":
            download_single_video_auto(yt, "video", pl_folder)
        else:
            print("Unknown mode for playlist download.")

# --- Main Function ---

def main():
    base_downloads = os.path.join(os.getcwd(), "downloads")
    os.makedirs(base_downloads, exist_ok=True)
    
    print("Select download type:")
    print("  1 - Single Video")
    print("  2 - Playlist")
    download_type = input("Your choice (1 or 2): ").strip()
    
    if download_type == "1":
        video_url = input("Enter the YouTube URL: ").strip()
        if not video_url:
            print("No URL provided, exiting.")
            return
        try:
            yt = YouTube(
                video_url,
                use_oauth=True,
                allow_oauth_cache=True,
                on_progress_callback=on_progress
            )
        except Exception as e:
            print("Error initializing YouTube object:", e)
            return
        
        print("\nVideo Details:")
        print("Title:", yt.title)
        author = yt.vid_info.get("videoDetails", {}).get("author", "unknown")
        print("Author:", author)
        print("Length (seconds):", yt.length)
        view_count = yt.vid_info.get("videoDetails", {}).get("viewCount")
        if view_count is None:
            print("Views: N/A")
        else:
            try:
                print("Views:", int(view_count))
            except Exception as e:
                print("Views: (error converting view count)", e)
        
        print("\nSelect mode for Single Video Download:")
        print("  - Enter 'm' for manual stream selection")
        print("  - Enter 'va' for automatic video+audio combo (best quality up to 1080p)")
        print("  - Enter 'aa' for automatic audio-only download")
        mode_choice = input("Your choice (m/va/aa): ").strip().lower()
        if mode_choice == "m":
            download_single_video_manual(yt, base_downloads)
        elif mode_choice == "va":
            download_single_video_auto(yt, "video", base_downloads)
        elif mode_choice == "aa":
            download_single_video_auto(yt, "audio", base_downloads)
        else:
            print("Invalid selection for single video.")
    
    elif download_type == "2":
        playlist_url = input("Enter the Playlist URL: ").strip()
        if not playlist_url:
            print("No URL provided, exiting.")
            return
        print("\nSelect mode for Playlist Download:")
        print("  - Enter 'a' for audio-only (best quality)")
        print("  - Enter 'v' for video with audio (automatic best combo up to 1080p)")
        mode_choice = input("Your choice (a/v): ").strip().lower()
        if mode_choice == "a":
            mode = "audio"
        elif mode_choice == "v":
            mode = "video"
        else:
            print("Invalid selection.")
            return
        download_playlist(playlist_url, mode, base_downloads)
    
    else:
        print("Invalid download type selection.")

if __name__ == '__main__':
    main()
