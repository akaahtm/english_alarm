import os
import feedparser
import google.generativeai as genai
import requests

# 1. 설정
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
RSS_URL = "https://www.youtube.com/feeds/videos.xml?channel_id=UC6P7_696H784Y93H8E_UqgA"

genai.configure(api_key=GEMINI_API_KEY)

def main():
    print("🚀 강제 테스트 시작: RSS 최상단 영상을 무조건 분석합니다.")
    feed = feedparser.parse(RSS_URL)
    
    if not feed.entries:
        print("❌ RSS 피드를 읽을 수 없습니다.")
        return

    # 리스트 맨 위 영상 선택
    video = feed.entries[0]
    print(f"✅ 타겟 영상: {video.title}")

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"이 유튜브 영상({video.link})은 영어 교육 영상이야. 대화 내용(A: B:), 해석, 중요 단어를 정리해줘."
        
        print("🤖 제미나이 분석 중...")
        response = model.generate_content(prompt)
        
        print("📤 텔레그램 전송 중...")
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      json={"chat_id": TELEGRAM_CHAT_ID, "text": response.text})
        print("✨ 전송 완료!")
        
    except Exception as e:
        print(f"❌ 에러: {e}")

if __name__ == "__main__":
    main()
