# app.py (Flask script)
from flask import Flask, request, render_template, send_from_directory, redirect, url_for
import os
from your_download_functions import (
    download_youtube_backend,
    download_instagram_backend,
    download_tiktok_backend,
    download_twitter_backend,
    download_spotify_backend
)

app = Flask(__name__)
app.config['DOWNLOAD_FOLDER'] = 'server_downloads'
os.makedirs(app.config['DOWNLOAD_FOLDER'], exist_ok=True)
app.config['SPOTIFY_CLIENT_ID'] = os.environ.get('SPOTIFY_CLIENT_ID')
app.config['SPOTIFY_CLIENT_SECRET'] = os.environ.get('SPOTIFY_CLIENT_SECRET')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/youtube')
def youtube_download_page():
    return render_template('youtube_download.html')

@app.route('/instagram')
def instagram_download_page():
    return render_template('instagram_download.html')

@app.route('/tiktok')
def tiktok_download_page():
    return render_template('tiktok_download.html')

@app.route('/twitter')
def twitter_download_page():
    return render_template('twitter_download.html')

@app.route('/spotify')
def spotify_download_page():
    return render_template('spotify_download.html')

@app.route('/download', methods=['POST'])
def download():
    platform = request.form['platform']
    url = request.form['url']
    save_path = app.config['DOWNLOAD_FOLDER']
    

    try:
        if platform == 'youtube':
            format = request.form.get('format', 'mp4')
            quality = request.form.get('quality', 'highest')
            filename = download_youtube_backend(url, format, quality, save_path)
            print(f"Filename for download link: {os.path.basename(filename)}")
            return render_template('download_success.html', filename=os.path.basename(filename))
        elif platform == 'instagram':
            filename = download_instagram_backend(url, save_path)
            print(f"Filename for download link: {os.path.basename(filename)}")
            return render_template('download_success.html', filename=os.path.basename(filename))
        elif platform == 'tiktok':
            filename = download_tiktok_backend(url, save_path)
            return render_template('download_success.html', filename=os.path.basename(filename))
        elif platform == 'twitter':
            filename = download_twitter_backend(url, save_path)
            return render_template('download_success.html', filename=os.path.basename(filename))
        elif platform == 'spotify':
            if not app.config['SPOTIFY_CLIENT_ID'] or not app.config['SPOTIFY_CLIENT_SECRET']:
                return render_template('download_error.html', error="Spotify API credentials not configured.")
            downloaded_files = download_spotify_backend(
                url, save_path, app.config['SPOTIFY_CLIENT_ID'], app.config['SPOTIFY_CLIENT_SECRET']
            )
            if downloaded_files:
                return render_template('spotify_download_success.html', files=[os.path.basename(f) for f in downloaded_files])
            else:
                return render_template('download_error.html', error="No Spotify tracks were downloaded.")
        else:
            return render_template('error.html', message="Invalid platform selected.")
    except Exception as e:
        return render_template('download_error.html', error=str(e))

@app.route('/downloads/<filename>')
def serve_download(filename):
    return send_from_directory(app.config['DOWNLOAD_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))  # Use Azure's PORT env var, or fallback to 8080
    app.run(host="0.0.0.0", port=port, debug=True)
