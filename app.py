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

        # خيارات ذكية لجلب كل شيء متاح
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'format': 'all',  # اطلب كل الجودات
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            title = info.get('title', 'فيديو بدون عنوان')
            thumbnail = info.get('thumbnail', '')
            
            formats_output = []
            seen_qualities = set()

            # ترتيب الجودات من الأفضل للأسوأ
            formats = info.get('formats', [])
            
            for f in formats:
                # تصفية الروابط التي تحتوي على فيديو وصوت معاً (للسهولة)
                # أو جودات عالية جداً (720p, 1080p) حتى لو كانت فيديو فقط
                download_url = f.get('url')
                if not download_url or 'googlevideo.com' not in download_url:
                    if 'youtube.com' in url: continue # تخطي الروابط غير المباشرة ليوتيوب

                height = f.get('height')
                if not height: continue

                quality_label = f"{height}p"
                
                # منع التكرار (نأخذ أفضل رابط لكل جودة)
                if quality_label not in seen_qualities:
                    formats_output.append({
                        'quality': quality_label,
                        'ext': f.get('ext', 'mp4'),
                        'url': download_url,
                        'has_video': f.get('vcodec') != 'none',
                        'has_audio': f.get('acodec') != 'none',
                    })
                    seen_qualities.add(quality_label)

            # إضافة خيار الصوت MP3 دائماً
            audio_f = info.get('url') # الرابط الافتراضي
            
            return jsonify({
                'success': True,
                'title': title,
                'thumbnail': thumbnail,
                'formats': sorted(formats_output, key=lambda x: int(x['quality'].replace('p','')), reverse=True)
            })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
