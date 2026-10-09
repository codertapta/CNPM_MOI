
import asyncio
import csv
import json
import os
import time
import edge_tts

VOICES = [
    ("vi", "vi-VN-NamMinhNeural"),
    ("en", "en-US-AriaNeural"),
    ("zh", "zh-CN-XiaoxiaoNeural"),
    ("ja", "ja-JP-NanamiNeural"),
    ("ko", "ko-KR-SunHiNeural"),
]

# Văn bản dự phòng chỉ dùng khi bản dịch chưa có.
FALLBACK_TEXTS = {
    "vi": "Xin chào các bạn. Chào mừng đến với ứng dụng.",
    "en": "Hello everyone. Welcome to the application.",
    "zh": "大家好，欢迎使用这个应用程序。",
    "ja": "皆さん、こんにちは。このアプリへようこそ。",
    "ko": "여러분, 안녕하세요. 이 애플리케이션에 오신 것을 환영합니다.",
}

os.makedirs("out", exist_ok=True)

with open("translations.json", encoding="utf-8") as f:
    texts = json.load(f)

rows = []


async def run():
    for lang, voice in VOICES:
        text = texts.get(lang)
        source = "translation"

        if not text:
            text = FALLBACK_TEXTS[lang]
            source = "fallback_sample"

        path = f"out/{voice}.mp3"
        t0 = time.perf_counter()

        try:
            await edge_tts.Communicate(
                text=text,
                voice=voice
            ).save(path)

            dt = time.perf_counter() - t0
            size = os.path.getsize(path) / 1024

            if size <= 0:
                raise RuntimeError("MP3 rỗng")

            status = "OK"

            print(
                f"[OK ] {voice}: {dt:.2f}s | "
                f"{len(text)} ký tự | {size:.1f} KB | "
                f"{source}"
            )

        except Exception as e:
            dt = time.perf_counter() - t0
            size = 0
            status = f"ERR {type(e).__name__}"

            print(
                f"[ERR] {voice}: {dt:.2f}s | "
                f"{type(e).__name__}: {e}"
            )

        rows.append([
            voice,
            lang,
            len(text),
            f"{dt:.2f}",
            f"{size:.1f}",
            status,
            source,
        ])

        # Cho phép các yêu cầu cách nhau một khoảng thời gian.
        await asyncio.sleep(2)

    with open(
        "tts_results.csv",
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as f:
        w = csv.writer(f)
        w.writerow([
            "voice", "lang", "chars", "seconds",
            "size_kb", "status", "text_source"
        ])
        w.writerows(rows)

    print("\nĐã lưu tts_results.csv")


if __name__ == "__main__":
    asyncio.run(run())