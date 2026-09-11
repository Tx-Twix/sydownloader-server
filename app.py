import os
import static_ffmpeg
from flask import Flask, request, jsonify
import yt_dlp

# إضافة أداة الدمج السحابية
try:
    static_ffmpeg.add_paths()
except Exception as e:
    print(f"FFmpeg notice: {e}")

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "SyDownloader Ultra Engine Active! 🇸🇾🔥"})

@app.route('/extract', methods=['POST'])
def extract():
    try:
        data = request.get_json(force=True)
        url = data.get('url', '').strip()
        if not url:
            return jsonify({'success': False, 'error': 'الرابط مطلوب'}), 400

        # إعدادات جلب كافّة الجودات المتاحة
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'format': 'all',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            
            extracted_formats = []
            seen_qualities = set()

            for f in formats:
                download_url = f.get('url')
                if not download_url:
                    continue

                height = f.get('height')
                if not height or height < 144:
                    continue

                quality_label = f"{height}p"
                
                # إعطاء الأولوية للجودات المدمجة أو العالية
                if quality_label not in seen_qualities:
                    extracted_formats.append({
                        'quality': quality_label,
                        'height': height,
                        'ext': f.get('ext', 'mp4'),
                        'url': download_url,
                        'has_audio': f.get('acodec') != 'none',
                        'has_video': f.get('vcodec') != 'none',
                    })
                    seen_qualities.add(quality_label)

            # فرز الجودات من الأعلى (1080p) إلى الأدنى (144p)
            extracted_formats.sort(key=lambda x: x['height'], reverse=True)

            # جلب رابط الصوت المنفصل MP3
            audio_url = ""
            for f in reversed(formats):
                if f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                    audio_url = f.get('url')
                    break

            return jsonify({
                'success': True,
                'title': info.get('title', 'فيديو'),
                'thumbnail': info.get('thumbnail', ''),
                'audio_url': audio_url,
                'formats': extracted_formats
            })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
