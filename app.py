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

        # إعدادات قوية جداً لجلب كافة الجودات المدمجة (صوت + صورة)
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            # البحث عن أفضل جودة مدمجة (فيديو+صوت) أو أفضل فيديو متاح
            'format': 'best[ext=mp4]/best', 
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            
            extracted_formats = []
            seen_heights = set()

            # ترتيب الصيغ لنبحث عن المدمج أولاً
            for f in formats:
                # شرط أساسي: لازم يكون فيديو وصوت مع بعض (مشان يشتغل عندك بدون تعليق)
                if f.get('vcodec') != 'none' and f.get('acodec') != 'none' and f.get('url'):
                    height = f.get('height')
                    if height:
                        quality_label = f"{height}p"
                        if quality_label not in seen_heights:
                            extracted_formats.append({
                                'quality': quality_label,
                                'height': height,
                                'ext': 'mp4',
                                'url': f.get('url'),
                                'size': f.get('filesize') or f.get('filesize_approx') or 0
                            })
                            seen_heights.add(quality_label)

            # ترتيب الجودات من الأعلى للأقل (مثلاً 720p ثم 360p)
            extracted_formats.sort(key=lambda x: x['height'], reverse=True)

            return jsonify({
                'success': True,
                'title': info.get('title', 'فيديو جديد'),
                'thumbnail': info.get('thumbnail', ''),
                'formats': extracted_formats
            })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
