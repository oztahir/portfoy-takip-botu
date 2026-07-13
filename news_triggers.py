"""
Haber Tetikleyici Botu
-----------------------
Global ve Türk haber kaynaklarından RSS akışlarını tarar, portföydeki
enstrümanlarla ilgili anahtar kelime eşleşmesi bulursa Telegram'a gönderir.
Aynı haberi tekrar göndermemek için görülen haber ID'lerini seen.json
dosyasında tutar (workflow bu dosyayı her çalıştırmada repoya geri yazar).

Ortam değişkenleri:
  TELEGRAM_BOT_TOKEN
  TELEGRAM_CHAT_ID
"""

import os
import sys
import json
import hashlib
import feedparser
import requests

STATE_FILE = "seen.json"
MAX_SEEN_IDS = 2000  # dosyanın sonsuza kadar büyümesini önlemek için

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# ---------------------------------------------------------------------------
# KAYNAKLAR - istediğin gibi ekleyip çıkarabilirsin
# ---------------------------------------------------------------------------

FEEDS = {
    # --- Global ---
    "Yahoo Finance (Genel)": "https://finance.yahoo.com/news/rssindex",
    "Yahoo Finance (Unity)": "https://feeds.finance.yahoo.com/rss/2.0/headline?s=U&region=US&lang=en-US",
    "Yahoo Finance (Rivian)": "https://feeds.finance.yahoo.com/rss/2.0/headline?s=RIVN&region=US&lang=en-US",
    "Nasdaq": "https://www.nasdaq.com/feed/nasdaq-original/rss.xml",
    "Investing.com (Genel)": "https://www.investing.com/rss/news.rss",

    # --- Türkiye ---
    "Bloomberg HT": "https://www.bloomberght.com/rss",
    "Bigpara": "https://bigpara.hurriyet.com.tr/rss/",
    "Investing.com TR (Genel)": "https://tr.investing.com/rss/news.rss",
    "Investing.com TR (Hisse)": "https://tr.investing.com/rss/stock.rss",
    "Investing.com TR (Emtia)": "https://tr.investing.com/rss/commodities.rss",
    "Investing.com TR (Kripto)": "https://tr.investing.com/rss/302.rss",
    "NTV Para": "https://www.ntv.com.tr/ntvpara.rss",
}

# Enstrüman -> haber başlığı/özetinde aranacak anahtar kelimeler (küçük harfe
# çevrilerek karşılaştırılır, Türkçe karakter duyarlılığı önemli değil)
KEYWORDS = {
    "📌 PHE / Pusula Portföy": ["phe", "pusula portföy", "pusula portfoy"],
    "🥇 Altın": ["altın", "ons altın", "gram altın", "gold", "xau"],
    "🎮 Unity": ["unity software", "unity (u)", " unity "],
    "🚗 Rivian": ["rivian", "rivn"],
    "Ξ Ethereum": ["ethereum", "eth "],
    "💧 Ripple / XRP": ["xrp", "ripple"],
    "🏦 TCMB / Enflasyon (TL varlıklar)": ["tcmb", "enflasyon", "tüfe", "politika faizi", "faiz kararı"],
}


def load_seen() -> set:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_seen(seen: set) -> None:
    # sadece en son N kaydı tut
    trimmed = list(seen)[-MAX_SEEN_IDS:]
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(trimmed, f)


def entry_id(entry) -> str:
    raw = entry.get("id") or entry.get("link") or entry.get("title", "")
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def send_telegram_message(text: str) -> None:
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("HATA: TELEGRAM_BOT_TOKEN veya TELEGRAM_CHAT_ID tanımlı değil.")
        sys.exit(1)
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    resp = requests.post(url, data=payload, timeout=15)
    if not resp.ok:
        print(f"Telegram gönderim hatası: {resp.status_code} {resp.text}")


def main():
    seen = load_seen()
    new_seen = set(seen)
    found_any = False

    for source_name, feed_url in FEEDS.items():
        try:
            feed = feedparser.parse(feed_url, request_headers={"User-Agent": "Mozilla/5.0"})
        except Exception as e:
            print(f"{source_name} okunamadı: {e}")
            continue

        for entry in feed.entries[:20]:  # her kaynaktan en yeni 20 haberi kontrol et
            eid = entry_id(entry)
            if eid in seen:
                continue

            title = entry.get("title", "")
            summary = entry.get("summary", "")
            text_to_search = f"{title} {summary}".lower()

            matched_instruments = [
                label for label, keywords in KEYWORDS.items()
                if any(kw in text_to_search for kw in keywords)
            ]

            if matched_instruments:
                link = entry.get("link", "")
                message = (
                    f"📰 <b>{source_name}</b>\n"
                    f"{', '.join(matched_instruments)}\n\n"
                    f"<b>{title}</b>\n"
                    f"{link}"
                )
                send_telegram_message(message)
                found_any = True

            new_seen.add(eid)  # eşleşsin eşleşmesin, bir daha kontrol etmemek için işaretle

    save_seen(new_seen)

    if not found_any:
        print("Eşleşen yeni haber yok.")
    else:
        print("Bir veya daha fazla haber gönderildi.")


if __name__ == "__main__":
    main()
