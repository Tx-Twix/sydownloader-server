import os
from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "SyDownloader Server is Ready! 🇸🇾"})

@app.route('/extract', methods=['POST'])
def extract():
    try:
        data = request.get_json(force=True)
        url = data.get('url', '').strip()
        if not url:
            return jsonify({'success': False, 'error': 'الرابط مطلوب'})

        # إعدادات ذكية لجلب الروابط المباشرة دون تحميلها على السيرفر
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'format': 'best',
            'extract_flat': False,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            
            extracted_formats = []
            seen_heights = set()

            for f in formats:
                # تصفية الروابط الشغالة والمباشرة فقط
                if not f.get('url') or 'manifest' in f.get('url'): continue
                
                height = f.get('height')
                if not height or height < 144: continue
                
                quality_label = f"{height}p"
                
                # نحن نريد الروابط التي تحتوي على فيديو (سواء بصوت أو بدون)
                if quality_label not in seen_heights:
                    extracted_formats.append({
                        'quality': quality_label,
                        'url': f.get('url'),
                        'ext': 'mp4',
                        'has_audio': f.get('acodec') != 'none',
                        'height': height
                    })
                    seen_heights.add(quality_label)

            # ترتيب الجودات من الأعلى للأقل
            extracted_formats.sort(key=lambda x: x['height'], reverse=True)

            # جلب رابط الصوت فقط MP3
            audio_url = info.get('url') # رابط احتياطي

            return jsonify({
                'success': True,
                'title': info.get('title', 'Video'),
                'thumbnail': info.get('thumbnail', ''),
                'formats': extracted_formats
            })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
