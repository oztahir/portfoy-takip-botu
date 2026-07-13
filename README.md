# Portföy Tetikleyici Botu

Belirlediğin hisse/kripto/altın için günlük yüzde değişim eşiği aşıldığında
Telegram kanalına otomatik mesaj gönderir. GitHub Actions üzerinde,
tamamen bulutta çalışır — bilgisayarının açık olmasına gerek yok.

## Kurulum

1. **Bu klasörü bir GitHub reposuna yükle**
   - GitHub'da yeni bir repo oluştur (public veya private, ikisi de olur).
   - Bu klasördeki dosyaları o reponun içine kopyala/push'la.

2. **Telegram bilgilerini "Secret" olarak ekle**
   - Repo sayfasında: `Settings` → `Secrets and variables` → `Actions` → `New repository secret`
   - `TELEGRAM_BOT_TOKEN` adıyla BotFather'dan aldığın token'ı ekle
   - `TELEGRAM_CHAT_ID` adıyla kanalının chat_id'sini (veya `@kanaladi` formatını) ekle

3. **Workflow'u etkinleştir**
   - Repo'da `Actions` sekmesine git, workflow'u onayla/etkinleştir.
   - `Actions` → `Portfoy Tetikleyici Kontrolu` → `Run workflow` ile elle bir kez
     test edebilirsin.

4. **Zamanlamayı istersen değiştir**
   - `.github/workflows/triggers.yml` içindeki `cron` satırını düzenle.
   - GitHub Actions cron ifadeleri **UTC** zaman dilimindedir, Türkiye saatinden
     3 saat geridir (örn. TRT 10:00 = UTC 07:00).

## Eşikleri özelleştirme

`check_triggers.py` dosyasının en üstündeki `STOCKS`, `CRYPTO` ve
`GOLD_THRESHOLD` değerlerini kendi risk toleransına göre değiştirebilirsin.

## Notlar

- PHE gibi TEFAS fonları için ücretsiz/güvenilir bir API bulunmadığından bu
  script şu an sadece hisse/kripto/altını kapsıyor. TEFAS verisini eklemek
  istersen ayrıca konuşabiliriz (web scraping gerektirir, TEFAS'ın kullanım
  şartlarına dikkat etmek gerekir).
- TCMB PPK ve TÜİK enflasyon takvimleri sabit tarihli olduğundan, bunları
  script yerine takvim hatırlatıcısı olarak ayrı tutmak daha pratik olabilir.
