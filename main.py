import os
import re
import json
import time
import requests
import subprocess
import feedparser
import google.generativeai as genai
from pathlib import Path
from datetime import datetime

# ── 환경변수 ───────────────────────────────────────────
GEMINI_API_KEY   = os.environ.get("GEMINI_API_KEY", "")
TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# EBS Easy English 채널 ID (고정)
CHANNEL_ID = "UCZFcNlpKXzs2b5ROtjLnB9A"
RSS_URL    = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"

LAST_DATE_FILE   = "last_date.json"
MAX_AUDIO_MINUTES = 10  # 오디오 앞 몇 분만 분석할지

# ── 날짜 파싱 ─────────────────────────────────────────
def extract_date_from_title(title: str):
    """
    8자리 날짜로 시작하고 'Easy English' 포함할 때만 날짜 반환
    예: '20260421 Ebs Easy English' → datetime(2026, 4, 21)
    다른 8자리 숫자 시작 영상은 None → 스킵
    """
    if "easy english" not in title.lower():
        return None
    match = re.match(r"^(\d{8})", title.strip())
    if match:
        try:
            return datetime.strptime(match.group(1), "%Y%m%d")
        except ValueError:
            return None
    return None

# ── 마지막 처리 날짜 관리 ──────────────────────────────
def load_last_date():
    if Path(LAST_DATE_FILE).exists():
        with open(LAST_DATE_FILE, "r") as f:
            data = json.load(f)
            return datetime.strptime(data["last_date"], "%Y%m%d")
    return None

def save_last_date(dt: datetime):
    with open(LAST_DATE_FILE, "w") as f:
        json.dump({"last_date": dt.strftime("%Y%m%d")}, f)

# ── RSS에서 새 영상 가져오기 ───────────────────────────
def get_new_videos(last_date):
    """RSS에서 last_date 이후의 새 영상만 반환"""
    feed = feedparser.parse(RSS_URL)
    new_videos = []

    for entry in feed.entries:
        title = entry.title
        video_date = extract_date_from_title(title)

        if video_date is None:
            continue  # 날짜 없는 영상은 스킵

        if last_date is None or video_date > last_date:
            new_videos.append({
                "id":    entry.yt_videoid,
                "title": title,
                "url":   f"https://www.youtube.com/watch?v={entry.yt_videoid}",
                "date":  video_date,
            })

    # 날짜 오름차순 정렬 (오래된 것부터 처리)
    new_videos.sort(key=lambda x: x["date"])
    return new_videos

# ── 오디오 다운로드 ────────────────────────────────────
def download_audio(video_url: str, output_path: str) -> str:
    cmd = [
        "yt-dlp",
        "-x", "--audio-format", "mp3",
        "--audio-quality", "5",
        "--postprocessor-args", f"ffmpeg:-t {MAX_AUDIO_MINUTES * 60}",
        "-o", output_path,
        "--no-playlist",
        video_url
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if result.returncode != 0:
        raise RuntimeError(f"yt-dlp 실패: {result.stderr}")
    return output_path

# ── Gemini 분석 ────────────────────────────────────────
ANALYSIS_PROMPT = """You are an English learning assistant for Korean learners.

Listen carefully to this EBS Easy English audio. There are two speakers (a male and a female host) having a conversation in English.

Extract the key English dialogue and format your response EXACTLY as below. Use real sentences from the audio only.

---
📝 *English Dialogue*

A: (남자 호스트 대사)
B: (여자 호스트 대사)
A: ...
B: ...
(핵심 대화 10~15 exchanges)

---

🇰🇷 *한글 해석*

A: (위 대사 한글 번역)
B: (위 대사 한글 번역)
...

---

📚 *단어 & 숙어*

• 단어/표현 — 의미 (예문)
• 단어/표현 — 의미 (예문)
(유용하고 중요한 것 5~7개)

---

🔍 *문법 포인트*

• 문법 항목 — 설명 + 대화에서 예시
• 문법 항목 — 설명 + 대화에서 예시
(2~3개)

---

Rules:
- ONLY use sentences actually spoken in the audio
- Korean translation must be natural, conversational Korean
- Grammar points should reference actual lines from the dialogue above
- Do NOT add any preamble or explanation outside this format
"""

def analyze_with_gemini(audio_path: str, video_title: str) -> str:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")

    with open(audio_path, "rb") as f:
        audio_data = f.read()

    audio_part = {"mime_type": "audio/mp3", "data": audio_data}
    response = model.generate_content([audio_part, ANALYSIS_PROMPT])
    return response.text

# ── Telegram 발송 ──────────────────────────────────────
def send_telegram(text: str, video_title: str, video_url: str, video_date: datetime):
    date_str = video_date.strftime("%Y년 %m월 %d일")
    header = f"🎬 *EBS Easy English* — {date_str}\n\n"
    footer = f"\n\n🔗 [영상 보기]({video_url})"

    full_text = header + text + footer

    # Telegram 4096자 제한 처리
    max_len = 4000
    if len(full_text) <= max_len:
        chunks = [full_text]
    else:
        # 헤더는 첫 청크에만, 푸터는 마지막 청크에만
        body_chunks = [text[i:i+max_len] for i in range(0, len(text), max_len)]
        chunks = []
        for i, chunk in enumerate(body_chunks):
            if i == 0:
                chunk = header + chunk
            if i == len(body_chunks) - 1:
                chunk = chunk + footer
            chunks.append(chunk)

    for chunk in chunks:
        payload = {
            "chat_id":    TELEGRAM_CHAT_ID,
            "text":       chunk,
            "parse_mode": "Markdown",
            "disable_web_page_preview": False,
        }
        resp = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json=payload,
            timeout=30
        )
        resp.raise_for_status()
        time.sleep(0.5)

# ── 메인 ──────────────────────────────────────────────
def main():
    print(f"🔍 EBS Easy English 새 영상 확인 중... ({datetime.now().strftime('%Y-%m-%d %H:%M')})")

    last_date = load_last_date()
    print(f"   마지막 처리 날짜: {last_date.strftime('%Y-%m-%d') if last_date else '없음 (첫 실행)'}")

    new_videos = get_new_videos(last_date)

    if not new_videos:
        print("✅ 새 영상 없음.")
        return

    print(f"📹 새 영상 {len(new_videos)}개 발견!")

    for video in new_videos:
        print(f"\n  처리 중: {video['title']}")
        audio_path = f"audio_{video['id']}.mp3"

        try:
            print("  ⬇️  오디오 다운로드...")
            download_audio(video["url"], audio_path)

            print("  🤖 Gemini 분석 중...")
            analysis = analyze_with_gemini(audio_path, video["title"])

            print("  📨 텔레그램 발송...")
            send_telegram(analysis, video["title"], video["url"], video["date"])

            # 성공하면 날짜 업데이트
            save_last_date(video["date"])
            print(f"  ✅ 완료: {video['title']}")

        except Exception as e:
            print(f"  ❌ 오류 ({video['title']}): {e}")
            # 오류가 나도 다음 영상은 계속 처리

        finally:
            if Path(audio_path).exists():
                Path(audio_path).unlink()

        time.sleep(2)

if __name__ == "__main__":
    main()
