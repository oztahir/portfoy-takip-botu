"""
Portföy Tetikleyici Botu
-------------------------
Belirlenen enstrümanları kontrol eder, eşik/eşik-üstü hareket veya
önemli bir gelişme varsa Telegram kanalına mesaj gönderir.

Ortam değişkenleri (GitHub Actions Secrets üzerinden gelir):
  TELEGRAM_BOT_TOKEN
  TELEGRAM_CHAT_ID

Çalıştırma: python check_triggers.py
"""

import os
import sys
import requests
import yfinance as yf

# ---------------------------------------------------------------------------
# AYARLAR - kendi eşiklerine göre değiştirebilirsin
# ---------------------------------------------------------------------------

# Hisse senetleri: ticker -> günlük % değişim eşiği (bu değeri aşan hareket bildirilir)
STOCKS = {
    "U": 5.0,      # Unity Software
    "RIVN": 5.0,   # Rivian
}

# Kripto paralar (CoinGecko id'leri) -> günlük % değişim eşiği
CRYPTO = {
    "ethereum": 5.0,
    "ripple": 5.0,
}

# Altın için ons/USD günlük % değişim eşiği
GOLD_THRESHOLD = 2.0

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


# ---------------------------------------------------------------------------
# YARDIMCI FONKSİYONLAR
# ---------------------------------------------------------------------------

def send_telegram_message(text: str) -> None:
    """Telegram kanalına mesaj gönderir."""
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


def check_stocks() -> list[str]:
    """Hisse senetlerinin günlük % değişimini kontrol eder."""
    alerts = []
    for ticker, threshold in STOCKS.items():
        try:
            info = yf.Ticker(ticker).fast_info
            last_price = info["last_price"]
            prev_close = info["previous_close"]
            change_pct = (last_price - prev_close) / prev_close * 100

            if abs(change_pct) >= threshold:
                direction = "🟢 YÜKSELİŞ" if change_pct > 0 else "🔴 DÜŞÜŞ"
                alerts.append(
                    f"{direction} <b>{ticker}</b>: {change_pct:+.2f}% "
                    f"(${prev_close:.2f} → ${last_price:.2f})"
                )
        except Exception as e:
            print(f"{ticker} kontrol edilemedi: {e}")
    return alerts


def check_crypto() -> list[str]:
    """CoinGecko üzerinden kripto paraların 24 saatlik % değişimini kontrol eder."""
    alerts = []
    ids = ",".join(CRYPTO.keys())
    url = (
        f"https://api.coingecko.com/api/v3/simple/price"
        f"?ids={ids}&vs_currencies=usd&include_24hr_change=true"
    )
    try:
        data = requests.get(url, timeout=15).json()
        for coin_id, threshold in CRYPTO.items():
            price = data[coin_id]["usd"]
            change_pct = data[coin_id]["usd_24h_change"]
            if abs(change_pct) >= threshold:
                direction = "🟢 YÜKSELİŞ" if change_pct > 0 else "🔴 DÜŞÜŞ"
                name = "Ethereum" if coin_id == "ethereum" else "XRP"
                alerts.append(
                    f"{direction} <b>{name}</b>: {change_pct:+.2f}% (${price:,.2f})"
                )
    except Exception as e:
        print(f"Kripto verisi alınamadı: {e}")
    return alerts


def check_gold() -> list[str]:
    """Altın (XAU/USD) fiyatını kontrol eder (yfinance üzerinden GC=F vadeli kontratı)."""
    alerts = []
    try:
        info = yf.Ticker("GC=F").fast_info
        last_price = info["last_price"]
        prev_close = info["previous_close"]
        change_pct = (last_price - prev_close) / prev_close * 100

        if abs(change_pct) >= GOLD_THRESHOLD:
            direction = "🟢 YÜKSELİŞ" if change_pct > 0 else "🔴 DÜŞÜŞ"
            alerts.append(
                f"{direction} <b>Altın (Ons/USD)</b>: {change_pct:+.2f}% "
                f"(${prev_close:.2f} → ${last_price:.2f})"
            )
    except Exception as e:
        print(f"Altın verisi alınamadı: {e}")
    return alerts


# ---------------------------------------------------------------------------
# ANA AKIŞ
# ---------------------------------------------------------------------------

def main(): 
    all_alerts = []
    all_alerts += check_stocks()
    all_alerts += check_crypto()
    all_alerts += check_gold()

    if all_alerts:
        message = "<b>📊 Portföy Tetikleyici Uyarısı</b>\n\n" + "\n".join(all_alerts)
        send_telegram_message(message)
        print("Uyarı gönderildi.")
    else:
        print("Eşik aşımı yok, mesaj gönderilmedi.")


if __name__ == "__main__":
    main()
