
import asyncio
import csv
import os
import time
import edge_tts

INPUT_CSV = "mymemory_results.csv"
OUTPUT_DIR = "out_translated"

# Một giọng cho mỗi ngôn ngữ
VOICES = {
    "vi": ("vi-VN-NamMinhNeural", "vi"),
    "en": ("en-US-AriaNeural", "en"),
    "zh": ("zh-CN-XiaoxiaoNeural", "zh"),
    "ja": ("ja-JP-NanamiNeural", "ja"),
    "ko": ("ko-KR-SunHiNeural", "ko"),
}

SOURCE_TEXT = (
    "Xin chào các bạn. Hôm nay chúng ta sẽ tìm hiểu cách xây dựng "
    "một ứng dụng dịch thuật và đọc văn bản thành giọng nói."
)

os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_translations():
    translations = {"vi": SOURCE_TEXT}

    with open(INPUT_CSV, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            lang = row["target_language"].strip()
            status = row["status"].strip().upper()
            translated = row["translation"].strip()

            if lang in VOICES and status == "OK" and translated:
                translations[lang] = translated

    return translations


async def main():
    translations = load_translations()
    results = []

    for lang, (voice, _) in VOICES.items():
        text = translations.get(lang)

        if not text:
            print(f"[SKIP] {lang}: Không có bản dịch hợp lệ")
            results.append([
                lang, voice, 0, "", "", "SKIP: no translation"
            ])
            continue

        path = os.path.join(OUTPUT_DIR, f"{lang}_{voice}.mp3")
        start = time.perf_counter()

        try:
            await edge_tts.Communicate(text, voice).save(path)

            elapsed = time.perf_counter() - start
            size_kb = os.path.getsize(path) / 1024

            print(f"\n[OK] {lang} - {voice}")
            print(f"Thời gian: {elapsed:.2f} giây")
            print(f"Ký tự: {len(text)}")
            print(f"Dung lượng: {size_kb:.1f} KB")
            print(f"File: {path}")
            print(f"Nội dung: {text}")

            results.append([
                lang, voice, len(text),
                f"{elapsed:.2f}", f"{size_kb:.1f}", "OK"
            ])

        except Exception as e:
            elapsed = time.perf_counter() - start

            print(f"\n[ERR] {lang} - {type(e).__name__}: {e}")

            results.append([
                lang, voice, len(text),
                f"{elapsed:.2f}", "0", f"ERR: {type(e).__name__}"
            ])

        await asyncio.sleep(1)

    with open(
        "tts_translated_results.csv",
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as f:
        writer = csv.writer(f)
        writer.writerow([
            "language", "voice", "chars",
            "seconds", "size_kb", "status"
        ])
        writer.writerows(results)

    print("\nĐã lưu kết quả: tts_translated_results.csv")


if __name__ == "__main__":
    asyncio.run(main())