import os
import feedparser
import google.generativeai as genai
import requests

# 1. 설정 (Secrets)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
# 알려주신 채널 RSS
RSS_URL = "https://www.youtube.com/feeds/videos.xml?channel_id=UC6P7_696H784Y93H8E_UqgA"

genai.configure(api_key=GEMINI_API_KEY)

def main():
    print("🛠 [DEBUG] 시스템 가동 시작")
    feed = feedparser.parse(RSS_URL)
    
    if not feed.entries:
        print("❌ [ERROR] RSS 데이터를 읽지 못했습니다.")
        return

    # 필터링 다 빼고, 가장 최신 영상 1개 강제 선택
    video = feed.entries[0]
    print(f"📺 [FOUND] 분석 대상: {video.title}")

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"유튜브 영상({video.link}) 내용을 분석해서 영어 대화(A: B:), 한글 해석, 핵심 단어를 정리해줘."
        
        print("🤖 [AI] 제미나이 분석 중...")
        response = model.generate_content(prompt)
        
        print("📤 [TG] 텔레그램 전송 중...")
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      json={"chat_id": TELEGRAM_CHAT_ID, "text": response.text})
        print("✨ [SUCCESS] 모든 작업 완료!")
        
    except Exception as e:
        print(f"❌ [ERROR] 에러 발생: {e}")

if __name__ == "__main__":
    main()
