# your_download_functions.py

import glob
import re
import os
import spotipy
import yt_dlp
import instaloader
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
from spotify_dl.spotify import fetch_tracks as spotify_dl_fetch_tracks
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB
import requests
import shutil

def download_youtube_backend(url, format, quality, save_path):
    base_output_template = os.path.join(save_path, '%(title)s.%(ext)s')
    ydl_opts = {
        'outtmpl': base_output_template,
        'quiet': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
    }

    is_mp3 = format == "mp3"

    if is_mp3:
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    else:
        format_map = {
            "Highest": "bestvideo+bestaudio/best",
            "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
            "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
            "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
            "Audio Only": "bestaudio/best"
        }
        ydl_opts['format'] = format_map.get(quality, "bestvideo+bestaudio/best")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            if info_dict and 'entries' in info_dict:
                info_dict = info_dict['entries'][0]

            # Original downloaded file name (may be .webm, .mp4, etc.)
            original_filename = ydl.prepare_filename(info_dict)
            base_name = os.path.splitext(os.path.basename(original_filename))[0]

            # If format is mp3, the actual file has .mp3 extension
            if is_mp3:
                mp3_filename = os.path.join(save_path, base_name + ".mp3")
                return mp3_filename
            else:
                return original_filename

    except Exception as e:
        raise Exception(f"YouTube Download Error: {str(e)}")

def download_instagram_backend(url, save_path):
    try:
        # Define the output template and options
        ydl_opts = {
            'outtmpl': os.path.join(save_path, '%(id)s.%(ext)s'),  # Naming the file based on post ID
            'quiet': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'format': 'bestvideo+bestaudio/best',  # Best video + audio quality for Instagram posts
            'forcejson': True,  # Force JSON output, ensures clean data extraction
            'writethumbnail': True,  # Write the thumbnail if it's available (useful for some posts)
            'noplaylist': True,  # Avoid downloading entire playlists
            'extractor_args': [
                '--no-posts'  # Avoid downloading comment threads or other unnecessary metadata
            ]
        }

        # Download content using yt-dlp
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)

        # Extract the downloaded filename from the output template
        file_path = os.path.join(save_path, f"{info_dict['id']}.{info_dict['ext']}")

        # Return the downloaded file path
        if os.path.exists(file_path):
            return file_path
        else:
            raise Exception("Media file not found after download.")

    except Exception as e:
        raise Exception(f"Instagram Download Error: {str(e)}")
    
def download_tiktok_backend(url, save_path):
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            video_ext = info_dict.get('ext', 'mp4')
            filename = f"tiktok_video.{video_ext}"
            full_path = os.path.join(save_path, filename)

            ydl_opts = {
                'outtmpl': full_path,
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
                'quiet': True,
                'nocheckcertificate': True,
                'ignoreerrors': False,
            }

        # Download using final options
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            return full_path
    except Exception as e:
        raise Exception(f"TikTok Download Error: {str(e)}")

def download_twitter_backend(url, save_path):
    ydl_opts = {
        'outtmpl': os.path.join(save_path, '%(title)s.%(ext)s'),
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
        'quiet': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            return os.path.join(save_path, ydl.prepare_filename(info_dict))
    except Exception as e:
        raise Exception(f"Twitter Download Error: {str(e)}")

def extract_spotify_id_from_url(url):
    match = re.search(r'(track|playlist)/([a-zA-Z0-9]+)', url)
    if match:
        return match.group(2), match.group(1)
    return None, None

def fetch_spotify_tracks_backend(sp, url):
    item_id, item_type = extract_spotify_id_from_url(url)
    if not item_id:
        raise ValueError("Invalid Spotify URL.")
    try:
        if item_type == 'track':
            track = sp.track(item_id)
            return [track]
        elif item_type == 'playlist':
            results = sp.playlist_tracks(item_id)
            tracks = [item['track'] for item in results['items'] if item['track']]
            return tracks
        else:
            return []
    except Exception as e:
        raise Exception(f"Error fetching Spotify tracks: {str(e)}")

def download_spotify_backend(url, save_path, spotify_client_id, spotify_client_secret):
    sp = Spotify(auth_manager=SpotifyClientCredentials(client_id=spotify_client_id, client_secret=spotify_client_secret))
    tracks = fetch_spotify_tracks_backend(sp, url)
    os.makedirs(os.path.join(save_path, "music"), exist_ok=True)
    downloaded_files = []
    for track in tracks:
        if not track:
            continue
        track_name = track['name']
        artists = track['artists']
        artist_name = artists[0]['name'] if artists else None
        album = track['album']
        album_name = album['name']
        images = album['images']
        cover_url = images[0]['url'] if images else None

        if track_name and artist_name:
            safe_track_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in track_name)
            safe_artist_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in artist_name)
            search_query = f"{track_name} {artist_name} audio"
            filename = os.path.join(save_path, "music", f"{safe_artist_name} - {safe_track_name}.mp3")

            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': filename,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '320',
                }],
                'quiet': True,
                'nocheckcertificate': True,
                'ignoreerrors': True, # Allow continuing if one track fails
            }
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([f"ytsearch:{search_query}"])
                downloaded_files.append(filename)

                if cover_url and os.path.exists(filename):
                    try:
                        response = requests.get(cover_url)
                        response.raise_for_status()
                        cover_path = os.path.join(save_path, "music", "temp_cover.jpg")
                        with open(cover_path, 'wb') as f:
                            f.write(response.content)
                        audio = MP3(filename, ID3=ID3)
                        audio.add_tags()
                        audio.tags.add(APIC(encoding=3, mime='image/jpeg', type=3, desc='Cover', data=open(cover_path, 'rb').read()))
                        audio.tags.add(TIT2(encoding=3, text=track_name))
                        audio.tags.add(TPE1(encoding=3, text=artist_name))
                        audio.tags.add(TALB(encoding=3, text=album_name))
                        audio.save()
                        os.remove(cover_path)
                    except Exception as e:
                        print(f"Error embedding metadata for {track_name}: {e}")
            except Exception as e:
                print(f"Error downloading {track_name}: {e}")
    return downloaded_files

