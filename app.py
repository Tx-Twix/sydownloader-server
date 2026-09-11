import os
from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "Server is Online! 🇸🇾"})

@app.route('/extract', methods=['POST'])
def extract():
    try:
        data = request.get_json(force=True)
        url = data.get('url', '').strip()
        if not url:
            return jsonify({'success': False, 'error': 'الرابط مطلوب'})

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'format': 'best',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # جلب كافة الجودات المتاحة
            formats = info.get('formats', [])
            extracted_formats = []
            seen_heights = set()

            for f in formats:
                height = f.get('height')
                if height and height not in seen_heights:
                    extracted_formats.append({
                        'quality': f"{height}p",
                        'url': f.get('url'),
                        'ext': f.get('ext', 'mp4'),
                        'has_video': f.get('vcodec') != 'none',
                        'has_audio': f.get('acodec') != 'none',
                    })
                    seen_heights.add(height)

            # ترتيب تنازلي
            extracted_formats.sort(key=lambda x: int(x['quality'].replace('p','')), reverse=True)

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
