import os
from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "SyDownloader Ultra Server Active! 🇸🇾🔥"})

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
            'format': 'all', # جلب كل الصيغ بدون استثناء
            'get_urls': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            
            extracted_formats = []
            seen_qualities = set()

            for f in formats:
                # تصفية الروابط التي تعمل مباشرة فقط
                if not f.get('url') or 'manifest' in f.get('url'): continue
                
                height = f.get('height')
                if not height: continue
                
                # نحن نريد الجودات الأساسية: 144, 240, 360, 480, 720, 1080
                quality_label = f"{height}p"
                
                # منع التكرار لنفس الجودة
                if quality_label not in seen_qualities:
                    extracted_formats.append({
                        'quality': quality_label,
                        'height': height,
                        'ext': f.get('ext', 'mp4'),
                        'url': f.get('url'),
                        'has_audio': f.get('acodec') != 'none',
                        'has_video': f.get('vcodec') != 'none',
                    })
                    seen_qualities.add(quality_label)

            # إضافة خيار الصوت MP3 بأعلى جودة
            audio_url = ""
            for f in reversed(formats):
                if f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                    audio_url = f.get('url')
                    break

            # ترتيب الجودات من الأعلى (1080) إلى الأقل (144)
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
