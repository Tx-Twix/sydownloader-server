import os
from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "SyDownloader Server Active! 🇸🇾🔥"})

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
            'format': 'best',
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            title = info.get('title', 'فيديو بدون عنوان')
            thumbnail = info.get('thumbnail', '')
            duration = info.get('duration', 0)
            
            formats_output = []
            
            # استخراج الجودات المتاحة لكل المنصات
            for f in info.get('formats', []):
                download_url = f.get('url')
                if not download_url:
                    continue
                
                ext = f.get('ext', 'mp4')
                format_note = f.get('format_note') or f.get('resolution') or 'MP4'
                height = f.get('height')
                quality_label = f"{height}p" if height else format_note

                # الفلترة لتصفية الروابط الشغالة
                if f.get('vcodec') != 'none' or f.get('acodec') != 'none':
                    formats_output.append({
                        'quality': quality_label,
                        'ext': ext,
                        'url': download_url,
                        'has_audio': f.get('acodec') != 'none',
                        'has_video': f.get('vcodec') != 'none',
                    })

            # حيلة لترتيب الجودات من الأعلى للأقل بدون تكرار
            unique_formats = {}
            for fmt in formats_output:
                key = f"{fmt['quality']}_{fmt['ext']}"
                if key not in unique_formats:
                    unique_formats[key] = fmt

            return jsonify({
                'success': True,
                'title': title,
                'thumbnail': thumbnail,
                'duration': duration,
                'formats': list(unique_formats.values())[::-1]
            })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
