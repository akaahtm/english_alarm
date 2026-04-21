# 📺 EBS Easy English → Telegram Bot

EBS Easy English 채널에 새 영상이 올라오면 자동으로:
1. 제목에서 날짜(YYYYMMDD) 감지 → 새 영상 여부 확인
2. yt-dlp로 오디오 추출
3. Gemini AI로 영어 다이얼로그 분석
4. Telegram으로 발송

---

## ⚙️ GitHub Secrets 설정

`Settings → Secrets and variables → Actions → New repository secret`

| Secret 이름 | 값 |
|---|---|
| `GEMINI_API_KEY` | Google AI Studio 무료 키 |
| `TELEGRAM_TOKEN` | @BotFather 봇 토큰 |
| `TELEGRAM_CHAT_ID` | 메시지 받을 채팅 ID |

> **채널 URL은 Secrets 불필요** — EBS Easy English 채널 ID가 코드에 고정되어 있음

---

## 🕐 실행 스케줄

매일 **한국시간 오전 7시 30분** 자동 실행
(EBS Easy English는 매일 아침 7시 20분 방송 → 유튜브 업로드 직후 체크)

수동 실행: GitHub → Actions → "EBS Easy English Bot" → "Run workflow"

---

## 📱 텔레그램 출력 예시

```
🎬 EBS Easy English — 2026년 04월 21일

📝 English Dialogue

A: Hey, have you heard about the new café downtown?
B: No, I haven't. What's it like?
A: It's really cozy. They serve amazing lattes.
B: Oh, I'd love to check it out sometime.

🇰🇷 한글 해석

A: 야, 시내에 새로 생긴 카페 들었어?
B: 아니, 못 들었는데. 어때?
A: 진짜 아늑해. 라떼가 엄청 맛있어.
B: 오, 언제 한번 가봐야겠다.

📚 단어 & 숙어

• cozy — 아늑한, 편안한 (The room feels cozy.)
• check out — 확인하다, 가보다 (Let's check it out.)
• downtown — 시내, 도심 (The café is downtown.)

🔍 문법 포인트

• Have you heard about ~? — 현재완료 경험 (~에 대해 들어봤어?)
  예: "Have you heard about the new café?"
• I'd love to ~ — ~하고 싶다 (정중한 희망 표현)
  예: "I'd love to check it out."

🔗 영상 보기
```

---

## 📂 파일 구조

```
├── main.py                        # 핵심 로직
├── requirements.txt
├── last_date.json                 # 자동 생성 (마지막 처리 날짜)
└── .github/
    └── workflows/
        └── run.yml                # GitHub Actions 스케줄러
```
