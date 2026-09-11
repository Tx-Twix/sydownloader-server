import os
from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "SyDownloader Pro Server Active! 🇸🇾🔥"})

@app.route('/extract', methods=['POST'])
def extract():
    try:
        data = request.get_json(force=True)
        url = data.get('url', '').strip()
        if not url:
            return jsonify({'success': False, 'error': 'الرابط مطلوب'}), 400

        # إعدادات احترافية لجلب الروابط المدمجة (صوت + صورة) حصراً بكافة الجودات
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'format': 'best[ext=mp4]/best', # ابحث عن أفضل ملف مدمج جاهز
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            
            extracted_formats = []
            seen_heights = set()

            # 1. جلب الجودات المدمجة (صوت + صورة مع بعض) - هاد اللي بدك ياه!
            for f in formats:
                # التأكد أن الرابط مباشر ويحتوي فيديو وصوت معاً
                if f.get('vcodec') != 'none' and f.get('acodec') != 'none' and f.get('url'):
                    height = f.get('height')
                    if height and height not in seen_heights:
                        extracted_formats.append({
                            'quality': f"{height}p",
                            'height': height,
                            'ext': 'mp4',
                            'url': f.get('url'),
                            'has_audio': True,
                            'has_video': True
                        })
                        seen_heights.add(height)

            # 2. جلب رابط الصوت فقط (MP3/M4A)
            audio_url = ""
            for f in formats:
                if f.get('vcodec') == 'none' and f.get('acodec') != 'none':
                    audio_url = f.get('url')
                    break

            # ترتيب الجودات من الأكبر (720p أو 1080p) للأصغر
            extracted_formats.sort(key=lambda x: x['height'], reverse=True)

            return jsonify({
                'success': True,
                'title': info.get('title', 'فيديو جديد'),
                'thumbnail': info.get('thumbnail', ''),
                'audio_url': audio_url,
                'formats': extracted_formats
            })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
