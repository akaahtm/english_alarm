import os
import feedparser
import google.generativeai as genai
import requests

# 1. 설정
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
# 사용자님의 채널 ID
RSS_URL = "https://www.youtube.com/feeds/videos.xml?channel_id=UC6P7_696H784Y93H8E_UqgA"

genai.configure(api_key=GEMINI_API_KEY)

def main():
    print("🚀 [System] 분석 프로세스 강제 시작")
    feed = feedparser.parse(RSS_URL)
    
    # RSS에서 가장 최신 영상 무조건 선택 (날짜 필터 제거)
    video = feed.entries[0]
    print(f"✅ 타겟 영상 발견: {video.title}")

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        # 영상의 오디오/내용을 분석하도록 요청
        prompt = f"유튜브 영상({video.link})은 EBS 영어 방송이야. 대화문(A: B:), 해석, 단어를 마크다운으로 정리해줘."
        
        response = model.generate_content(prompt)
        
        # 텔레그램 전송
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      json={"chat_id": TELEGRAM_CHAT_ID, "text": response.text, "parse_mode": "Markdown"})
        print("✨ 전송 완료!")
        
    except Exception as e:
        print(f"❌ 에러: {e}")

if __name__ == "__main__":
    main()
