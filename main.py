import os
import re
import feedparser
import google.generativeai as genai
import requests
from datetime import datetime

# 1. 설정 (Secrets에서 가져옴)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
# EBS Easy English 채널 RSS 주소
RSS_URL = "https://www.youtube.com/feeds/videos.xml?channel_id=UC6P7_696H784Y93H8E_UqgA"

genai.configure(api_key=GEMINI_API_KEY)

def get_latest_video():
    print(f"🔍 RSS 피드 분석 중... ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
    feed = feedparser.parse(RSS_URL)
    
    for entry in feed.entries:
        title = entry.title
        link = entry.link
        print(f"📺 발견된 제목: {title}") # 로그 확인용
        
        # 필터: "Easy English"가 포함되어 있고 제목에 숫자가 있는지 확인
        if "easy english" in title.lower():
            # 제목에서 숫자 8자리 추출 (예: 20260421)
            date_match = re.search(r"(\d{8})", title)
            if date_match:
                return {"title": title, "link": link, "date": date_match.group(1)}
    return None

def analyze_video(video_url):
    model = genai.GenerativeModel('gemini-1.5-flash')
    # 제미나이에게 유튜브 링크를 직접 주고 분석 요청
    prompt = f"""
    이 유튜브 영상({video_url})은 EBS Easy English 방송이야.
    1. 대화 내용을 A:, B: 형태의 영어 다이어로그로 추출해줘.
    2. 각 문장에 대한 한글 해석을 달아줘.
    3. 중요 단어, 숙어, 문법 포인트를 정리해줘.
    
    출력 형식:
    🎬 **오늘의 방송: [제목]**
    
    📝 **English Dialogue**
    A: ...
    B: ...
    
    🇰🇷 **한글 해석**
    ...
    
    📚 **단어 & 문법 포인트**
    - ...
    """
    response = model.generate_content(prompt)
    return response.text

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def main():
    video = get_latest_video()
    
    if video:
        print(f"✅ 대상 영상 발견: {video['title']}")
        # 테스트를 위해 '오늘 날짜' 체크를 일단 풀고 무조건 최신꺼 하나 처리
        try:
            analysis = analyze_video(video['link'])
            send_telegram(analysis)
            print("🚀 텔레그램 전송 완료!")
        except Exception as e:
            print(f"❌ 에러 발생: {e}")
    else:
        print("❌ 조건을 만족하는 최신 영상을 찾지 못했습니다.")

if __name__ == "__main__":
    main()
