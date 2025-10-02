# Patset Yükleyici

## Genel Bakış
Patset Yükleyici, NetScaler / Citrix ADC üzerinde `policypatset_pattern_binding` kaynaklarına toplu domain/pattern eklemeyi kolaylaştıran hafif bir Flask uygulamasıdır. Arayüz, cihaz adresi, patset adı ve Basic Auth bilgilerini girerek formdan girilen veya isteğe bağlı `PATSET_DEFAULT_PATTERNS` ortam değişkeniyle gelen domainleri tek seferde göndermeye imkân tanır. Uygulama Python 3.11 tabanlı bir Docker imajı içinde paketlenebilir veya doğrudan betik olarak çalıştırılabilir.

## Temel Özellikler
- **Modern UI**: FF671D rengini baz alan koyu tema ve grid tabanlı form (app.py).
- **Dinamik Kimlik Doğrulama**: Kullanıcı adı/parola girildiğinde Basic Auth başlığı otomatik üretilir (app.py).
- **Toplu İşleme**: Her pattern için `curl --location --request PUT` çağrısı yapılır ve sonuç satır bazında tabloya işlenir (app.py).
- **Merkezi Loglama**: Her işlem stdout'a INFO/WARNING/ERROR seviyelerinde yazılır, Docker logları üzerinden takip edilebilir (app.py).
- **Çevresel Varsayılanlar**: Cihaz, patset, auth ve kullanıcı bilgileri isteğe bağlı olarak ortam değişkenlerinden yüklenebilir (app.py).

## Gereksinimler
- Python 3.11 (yerel çalıştırma için)
- Docker 20.10+ (konteyner çalıştırma için)
- NetScaler/Citrix ADC REST endpoint erişimi

## Yerel Geliştirme
```bash
pip install -r requirements.txt
python app.py
```
Uygulama varsayılan olarak `http://localhost:8082` adresinde çalışır. `FLASK_PORT` ortam değişkeni ile portu değiştirebilirsiniz.

## Docker Kullanımı
### İnşa Etme
```bash
docker build -t patset-app .
```
### Çalıştırma
```bash
docker run -d --name patset-app -p 8082:8082 patset-app
```
### Log Takibi
```bash
docker logs -f patset-app
```
Her pattern için “Gönderim başlıyor / Gönderim başarılı / Gönderim hatalı” satırlarını göreceksiniz.

## Alternatif: Bash Betiği
`patset.sh` dosyası aynı işlemleri komut satırından yapmak için örnek sağlar. Ortam değişkenleri aracılığıyla cihaz adresini, patset adını, kimlik doğrulamasını ve giriş/çıkış dosyalarını belirtin.
```bash
export PATSET_ENDPOINT="http://example-adc.local/nitro/v1/config/policypatset_pattern_binding/"
export PATSET_AUTH_HEADER="Basic REPLACE_ME"
export PATSET_NAME="example_patset_name"
./patset.sh
```

## Yapılandırma Seçenekleri
| Ortam Değişkeni | Açıklama | Varsayılan |
| --- | --- | --- |
| `PATSET_DEVICE` | Formdaki cihaz alanı için başlangıç değeri | boş |
| `PATSET_NAME` | Patset adı varsayılanı | boş |
| `PATSET_AUTH_HEADER` | Başlangıç Authorization header | boş |
| `PATSET_USERNAME` | Varsayılan kullanıcı adı | boş |
| `PATSET_PASSWORD` | Varsayılan parola (auth üretimi için) | boş |
| `PATSET_DEFAULT_PATTERNS` | Uygulama açılışında metin alanına eklenecek liste | boş |
| `FLASK_PORT` | Sunucu portu | 8082 |

## Güvenlik Notları
- Basic Auth bilgileri formda plaintext olarak taşınır; HTTPS üzerinden kullanılması önerilir.
- Uygulama kimlik bilgilerini disk üzerinde saklamaz; tüm loglar stdout’a gider.
- `DEBUG=True` sadece geliştirme amaçlıdır. Üretimde `flask run` veya bir WSGI sunucusu ile `debug=False` önerilir.

## Sorun Giderme
- **HTTP 405**: Form gönderiminde `/` endpoint’ine POST atılmadığında görülebilir; tarayıcı önbelleğini temizleyip deneyin.
- **Bağlantı Hataları**: `status=599` gibi durumlar NetScaler erişim sorunu veya ağ bağlantı problemini gösterir; loglar `stderr` alanında detay içerir.
- **Varsayılan Liste**: Başlangıç listesi gerekiyorsa `PATSET_DEFAULT_PATTERNS` ortam değişkenini satır başına bir domain olacak şekilde tanımlayın.

## Değişiklik Özeti
- Flask arayüzü modern temayla güncellendi.
- Dinamik Basic Auth üretimi ve doğrulama merkezi hâle getirildi.
- `curl` tabanlı NetScaler istekleri Python tarafından yönetiliyor, sonuçlar tabloda görselleştiriliyor.
- Geliştirici logları INFO/WARNING/ERROR seviyelerinde stdout’a yazılıyor.
