
import csv
import time
from deep_translator import MyMemoryTranslator

TEXT = (
    "Xin chào các bạn. Hôm nay chúng ta sẽ tìm hiểu cách xây dựng "
    "một ứng dụng dịch thuật và đọc văn bản thành giọng nói."
)

TARGETS = {
    "en": "english",
    "zh": "chinese simplified",
    "ja": "japanese",
    "ko": "korean",
}

rows = []

for code, language in TARGETS.items():
    start = time.perf_counter()

    try:
        translated = MyMemoryTranslator(
            source="vietnamese",
            target=language
        ).translate(TEXT)

        elapsed = time.perf_counter() - start

        print(f"\n[OK] vi -> {code}: {elapsed:.2f}s")
        print(f"Bản dịch: {translated}")

        rows.append([
            code, len(TEXT), len(translated),
            f"{elapsed:.2f}", "OK", translated
        ])

    except Exception as e:
        elapsed = time.perf_counter() - start

        print(f"\n[ERR] vi -> {code}: {type(e).__name__}: {e}")

        rows.append([
            code, len(TEXT), 0,
            f"{elapsed:.2f}", f"ERR: {type(e).__name__}", ""
        ])

    time.sleep(2)

with open("mymemory_results.csv", "w",
          newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow([
        "target_language", "source_chars",
        "translated_chars", "seconds", "status", "translation"
    ])
    writer.writerows(rows)

print("\nĐã lưu kết quả vào mymemory_results.csv")