import os
import re
import feedparser
import google.generativeai as genai
import requests
from datetime import datetime

# 1. 설정
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
# 알려주신 채널의 RSS 주소
RSS_URL = "https://www.youtube.com/feeds/videos.xml?channel_id=UC6P7_696H784Y93H8E_UqgA"

genai.configure(api_key=GEMINI_API_KEY)

def main():
    print(f"🔍 [EBS 학습 봇] 영상 스캔 시작...")
    feed = feedparser.parse(RSS_URL)
    
    if not feed.entries:
        print("❌ RSS 데이터를 가져오지 못했습니다.")
        return

    # 1. 오늘 날짜 생성 (YYYYMMDD)
    today_str = datetime.now().strftime("%Y%m%d")
    print(f"📅 오늘 기준 날짜: {today_str}")

    target_video = None

    # 2. 영상 목록을 돌면서 오늘 날짜가 포함된 영상 찾기
    for entry in feed.entries:
        print(f"📺 후보: {entry.title}")
        # 제목에서 8자리 숫자 추출 시도
        found_date = re.search(r"(\d{8})", entry.title)
        
        if found_date:
            date_in_title = found_date.group(1)
            # 오늘 날짜와 일치하거나, 혹은 오늘 영상이 아직 없으면 가장 최신꺼 하나 선택
            if date_in_title == today_str:
                target_video = entry
                print(f"🎯 오늘 영상 매칭 성공!")
                break

    # 3. 만약 오늘 날짜 영상을 못 찾았다면, 리스트 맨 위의 영상을 강제로 선택 (테스트용)
    if not target_video:
        target_video = feed.entries[0]
        print(f"⚠️ 오늘 날짜 영상이 아직 없어 최신 영상({target_video.title})으로 진행합니다.")

    # 4. Gemini 분석 및 텔레그램 발송
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        이 유튜브 영상({target_video.link})은 EBS 영어 교육 영상이야.
        1. 메인 영어 대화문을 A:, B: 형식으로 추출해줘.
        2. 대화문의 한글 해석을 달아줘.
        3. 주요 단어와 숙어, 문법 포인트를 정리해줘.
        텔레그램에서 읽기 좋게 깔끔한 마크다운 형식으로 작성해줘.
        """
        
        print("🤖 제미나이 분석 중...")
        response = model.generate_content(prompt)
        
        print("📤 텔레그램 발송 중...")
        msg = f"🎬 **학습 리포트: {target_video.title}**\n\n{response.text}"
        
        # 텔레그램 메시지 길이가 너무 길면 잘릴 수 있으므로 주의
        tg_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        res = requests.post(tg_url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": msg,
            "parse_mode": "Markdown"
        })
        
        if res.status_code == 200:
            print("✨ 성공적으로 발송되었습니다!")
        else:
            print(f"❌ 발송 실패: {res.text}")

    except Exception as e:
        print(f"❌ 실행 중 에러 발생: {e}")

if __name__ == "__main__":
    main()
