import os
from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "SyDownloader Ultra-Engine Active! 🇸🇾🔥"})

@app.route('/extract', methods=['POST'])
def extract():
    try:
        data = request.get_json(force=True)
        url = data.get('url', '').strip()
        if not url:
            return jsonify({'success': False, 'error': 'الرابط مطلوب'}), 400

        # إعدادات قوية جداً لجلب روابط الفيديو المباشرة بجميع الجودات
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'format': 'best', # سيبحث عن أفضل جودة مدمجة تلقائياً
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            
            extracted_formats = []
            seen_heights = set()

            # 1. جلب الجودات المدمجة (فيديو + صوت) - يوتيوب يوفر 720p مدمجة غالباً
            for f in formats:
                if not f.get('url'): continue
                
                # التأكد أن الرابط يحتوي على فيديو وصوت معاً ليعمل فوراً عند المستخدم
                if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                    height = f.get('height')
                    if height:
                        quality_label = f"{height}p"
                        if quality_label not in seen_heights:
                            extracted_formats.append({
                                'quality': quality_label,
                                'height': height,
                                'ext': f.get('ext', 'mp4'),
                                'url': f.get('url'),
                                'has_audio': True,
                                'size': f.get('filesize') or f.get('filesize_approx') or 0
                            })
                            seen_heights.add(quality_label)

            # 2. جلب رابط الصوت MP3 بأعلى جودة
            audio_url = ""
            for f in reversed(formats):
                if f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                    audio_url = f.get('url')
                    break

            # ترتيب الجودات من الأعلى (720p) إلى الأقل (144p)
            extracted_formats.sort(key=lambda x: x['height'], reverse=True)

            return jsonify({
                'success': True,
                'title': info.get('title', 'Video'),
                'thumbnail': info.get('thumbnail', ''),
                'audio_url': audio_url,
                'formats': extracted_formats
            })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
