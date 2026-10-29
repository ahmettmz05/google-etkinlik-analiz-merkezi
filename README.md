# Google Etkinlik Analiz Merkezi

Türkçe arayüzlü, yerel çalışmaya yönelik güvenli MVP. Google OAuth ile kimlik doğrular; Google hesabındaki tüm geçmişe otomatik eriştiğini iddia etmez. Google'ın genel web OAuth API'leri tüm My Activity / arama / YouTube / konum geçmişini tek bir kapsamla sunmaz. Bu sürüm, kullanıcının açıkça seçip yüklediği Google Takeout JSON/CSV dosyalarını yerel olarak analiz eder. OAuth yalnızca oturum kimliğini doğrular (`openid email profile`).

## Özellikler
- Google OAuth 2.0 giriş/çıkış
- Açıkça yüklenen JSON veya CSV dosyalarını yerel bellekte analiz
- Örnek veri modu
- Başlat düğmesi
- Özet istatistikler ve kayıt tablosu
- HTML ve CSV raporu indirme
- Dosyalar yükleme sonrasında kalıcı diske yazılmaz
- Basit testler

## Kurulum
Python 3.10+ önerilir.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Google OAuth kurulumu:
1. Google Cloud Console'da bir proje oluştur.
2. OAuth consent screen / Google Auth Platform ayarlarını tamamla.
3. OAuth client ID oluştur: **Web application**.
4. Authorized redirect URI olarak `http://localhost:5000/auth/callback` ekle.
5. `.env` içine `GOOGLE_CLIENT_ID` ve `GOOGLE_CLIENT_SECRET` yaz.
6. `python app.py` çalıştırıp `http://localhost:5000` aç.

OAuth'u kurmadan da örnek veri moduyla analiz ve rapor üretimi test edilebilir. Uygulama internete açık sunucuda yayınlanacaksa HTTPS, güvenli secret yönetimi, CSRF koruması, daha güçlü oturum ayarları ve dağıtım incelemesi gerekir.

## Google Takeout verisi
Google Takeout üzerinden istediğin ürün verilerini kendin dışa aktar ve yalnızca analiz etmek istediğin JSON/CSV dosyasını seç. Arşivin tamamını yüklemek zorunda değilsin. Desteklenen genel JSON yapıları ve CSV başlıkları olabildiğince esnek okunur; dışa aktarma biçimleri değişebileceğinden her ürün dosyası tam olarak normalize edilemeyebilir.

## Güvenlik sınırları
- Google şifreni uygulamaya girme.
- OAuth erişim/yenileme token'ları saklanmaz.
- OAuth yalnızca `openid email profile` ister; Gmail, Drive veya diğer API'lere erişim istemez.
- Yüklenen dosya sunucuda kalıcı olarak saklanmaz; analiz isteği süresince bellekte işlenir.
- Raporlar indirildiğinde senin cihazına kaydedilir; hassas dosyaları paylaşmadan önce kontrol et.
- Bu MVP tüm Google geçmişini otomatik çekmez. Google'ın sağladığı dışa aktarma dosyalarıyla sınırlıdır.

## Test
```bash
pytest -q
```
