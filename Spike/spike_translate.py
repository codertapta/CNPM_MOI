
import json
import time
from deep_translator import GoogleTranslator

TEXT = (
    "Xin chào các bạn. Hôm nay chúng ta sẽ tìm hiểu cách xây dựng "
    "một ứng dụng dịch thuật và đọc văn bản thành giọng nói."
)

TARGETS = {
    "en": "en",
    "zh": "zh-CN",
    "ja": "ja",
    "ko": "ko",
}

results = {"vi": TEXT}

print(f"Ký tự nguồn: {len(TEXT)}\n")

for key, code in TARGETS.items():
    t0 = time.perf_counter()

    try:
        out = GoogleTranslator(
            source="vi",
            target=code
        ).translate(TEXT)

        dt = time.perf_counter() - t0
        results[key] = out

        print(
            f"[OK ] vi->{key}: {dt:.2f}s | "
            f"{len(out)} ký tự\n      {out}\n"
        )

    except Exception as e:
        dt = time.perf_counter() - t0

        print(
            f"[ERR] vi->{key}: {dt:.2f}s | "
            f"{type(e).__name__}: {e}\n"
        )

    # Giãn cách các yêu cầu, tránh gửi liên tiếp quá nhanh.
    time.sleep(3)

with open("translations.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("Đã lưu translations.json")
print("Ngôn ngữ dịch thành công:", list(results.keys()))