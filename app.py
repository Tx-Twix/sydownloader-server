import os
import time
import glob
from flask import Flask, request, jsonify, send_from_directory
import static_ffmpeg
import yt_dlp

# إضافة أداة الدمج FFmpeg للسيرفر تلقائياً
try:
    static_ffmpeg.add_paths()
except Exception as e:
    print(f"FFmpeg Setup Error: {e}")

app = Flask(__name__)
DOWNLOAD_FOLDER = '/tmp/downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "SyDownloader Ultra-Engine 1080p Active! 🇸🇾🔥"})

@app.route('/extract', methods=['POST'])
def extract():
    try:
        data = request.get_json(force=True)
        url = data.get('url', '').strip()
        if not url:
            return jsonify({'success': False, 'error': 'الرابط مطلوب'}), 400

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'فيديو')
            thumbnail = info.get('thumbnail', '')
            formats = info.get('formats', [])

            available_qualities = []
            seen = set()

            # جلب كل الجودات المتاحة (1080p, 720p, 480p, 360p)
            for f in formats:
                height = f.get('height')
                if height and height >= 144 and height not in seen:
                    available_qualities.append({
                        'quality': f"{height}p",
                        'height': height,
                    })
                    seen.add(height)

            # ترتيب من الأعلى للأسفل
            available_qualities.sort(key=lambda x: x['height'], reverse=True)

            return jsonify({
                'success': True,
                'title': title,
                'thumbnail': thumbnail,
                'qualities': available_qualities
            })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/convert', methods=['POST'])
def convert():
    try:
        data = request.get_json(force=True)
        url = data.get('url', '').strip()
        quality_str = data.get('quality', '720p').replace('p', '')

        # تنظيف الملفات القديمة
        for f in glob.glob(f"{DOWNLOAD_FOLDER}/*"):
            if time.time() - os.path.getmtime(f) > 300:
                try: os.remove(f)
                except: pass

        filename_base = f"vid_{int(time.time())}"
        output_template = os.path.join(DOWNLOAD_FOLDER, f"{filename_base}.%(ext)s")

        if quality_str == 'audio':
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': output_template,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }
            expected_ext = 'mp3'
        else:
            # دمج الفيديو والصوت للجودات العالية 1080p و 720p
            ydl_opts = {
                'format': f'bestvideo[height<={quality_str}]+bestaudio/best[height<={quality_str}]/best',
                'outtmpl': output_template,
                'merge_output_format': 'mp4',
            }
            expected_ext = 'mp4'

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        final_filename = f"{filename_base}.{expected_ext}"
        download_link = request.host_url + f"file/{final_filename}"

        return jsonify({
            'success': True,
            'download_url': download_link
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/file/<filename>')
def get_file(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
