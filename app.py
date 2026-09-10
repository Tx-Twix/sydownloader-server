import os
from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "SyDownloader Super Server Active! 🇸🇾🔥"})

@app.route('/extract', methods=['POST'])
def extract():
    try:
        data = request.get_json(force=True)
        url = data.get('url', '').strip()
        if not url:
            return jsonify({'success': False, 'error': 'الرابط مطلوب'}), 400

        # إعدادات قوية جداً لجلب كافة الجودات المخفية
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'format': 'bestvideo+bestaudio/best',
            'youtube_include_dash_manifest': True,
            'youtube_include_hls_manifest': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            
            extracted_formats = []
            seen = set()

            for f in formats:
                if not f.get('url'): continue
                
                # جلب الجودة (مثلاً 1080, 720, 480)
                height = f.get('height')
                if not height: continue
                
                quality_label = f"{height}p"
                ext = f.get('ext', 'mp4')
                vcodec = f.get('vcodec', 'none')
                acodec = f.get('acodec', 'none')
                
                # تصنيف الجودة
                has_video = vcodec != 'none'
                has_audio = acodec != 'none'
                
                # مفتاح لمنع التكرار
                key = f"{quality_label}_{has_audio}"
                
                if key not in seen:
                    extracted_formats.append({
                        'quality': quality_label,
                        'ext': ext,
                        'url': f.get('url'),
                        'has_audio': has_audio,
                        'has_video': has_video,
                        'size': f.get('filesize') or f.get('filesize_approx') or 0
                    })
                    seen.add(key)

            # ترتيب من الأعلى للأقل
            extracted_formats.sort(key=lambda x: int(x['quality'].replace('p','')), reverse=True)

            return jsonify({
                'success': True,
                'title': info.get('title', 'فيديو'),
                'thumbnail': info.get('thumbnail', ''),
                'formats': extracted_formats
            })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
