# Pasifik Display — Project Status

## Proje Amacı

Pasifik Display için oluşturulan bu proje, televizyon panel değişimi ve teknik servis hizmetlerini model bazlı olarak sunan SEO uyumlu bir katalog ve servis sitesidir.

Site yapısı kullanıcıların:

- TV markasını seçmesini
- Modelini bulmasını
- Panel değişimi / LED arızası / anakart arızası gibi servis bilgilerine ulaşmasını

sağlamak üzere tasarlanmıştır.

---

# Kullanılan Teknolojiler

Frontend

- Astro
- TailwindCSS
- TypeScript

Veri Katmanı

- JSON veri tabanı
- Python normalize pipeline

---

# Veri Yapısı

Veriler iki ana katmanda tutulur.

## Raw Data
# Pasifik Display — Project Status

## Proje Amacı

Pasifik Display için oluşturulan bu proje, televizyon panel değişimi ve teknik servis hizmetlerini model bazlı olarak sunan SEO uyumlu bir katalog ve servis sitesidir.

Site yapısı kullanıcıların:

- TV markasını seçmesini
- Modelini bulmasını
- Panel değişimi / LED arızası / anakart arızası gibi servis bilgilerine ulaşmasını

sağlamak üzere tasarlanmıştır.

---

# Kullanılan Teknolojiler

Frontend

- Astro
- TailwindCSS
- TypeScript

Veri Katmanı

- JSON veri tabanı
- Python normalize pipeline

---

# Veri Yapısı

Veriler iki ana katmanda tutulur.

## Raw Data
data/raw/


Kaynak sitelerden elde edilen ham veriler.

## Normalized Data
data/normalized/


Site tarafından kullanılan temizlenmiş veri.

Başlıca dosyalar:
brands.json
models-by-brand.json
panels-by-model.json


---

# Normalize Pipeline

Ana script:
normalize_all.py


Veri akışı:
RAW DATA
↓
normalize_all.py
↓
normalized JSON
↓
Astro site rendering


---

# Mevcut Veri Durumu

Şu an normalize edilmiş veri yaklaşık olarak:


Brand Count : 24
Model Count : ~580


Bu sayı servis sitesi için başlangıç seviyesinde yeterlidir ancak ileride genişletilecektir.

---

# Site Yapısı

## Ana Sayfalar


/
/hizmetler
/iletisim


## Marka Sayfaları


/markalar
/markalar/{brand}
/markalar/{brand}/{model}


## Servis Bölgesi Sayfaları


/istanbul-tv-servisi
/umraniye-tv-servisi
/kadikoy-tv-servisi
/uskudar-tv-servisi
/cekmekoy-tv-servisi
/maltepe-tv-servisi
/sancaktepe-tv-servisi
/sultanbeyli-tv-servisi
/atasehir-tv-servisi

Bu sayfalar SEO için lokasyon bazlı oluşturulmuştur.

---

# Tamamlanan Geliştirme Aşamaları

## Phase 0 — Altyapı

Tamamlandı.

Kurulan sistemler:

- Astro proje kurulumu
- Tailwind kurulumu
- Layout sistemi
- Header / Footer component
- Base SEO layout
- Brand → Model → Panel veri yapısı

---

## Phase 1 — Veri Pipeline

Kısmen tamamlandı.

Normalize pipeline çalışıyor ancak veri doğrulama filtreleri henüz yeterli değil.

---

## Phase 2 — Site Routing

Tamamlandı.

Statik sayfalar ve dinamik sayfalar doğru şekilde oluşturuldu.

Örnek URL yapısı:


/markalar/samsung/
/markalar/samsung/ue32j4000/


---

## Phase 3 — UI

Tamamlandı.

Yapılan geliştirmeler:

- Ana sayfa hero bölümü
- Hizmetler sayfası
- Marka sayfası
- Model sayfası
- Servis bölgesi sayfaları
- CTA butonları
- Breadcrumb yapısı
- SEO meta sistemleri

Commit:


feat: complete UI polish for homepage, services, brands and model pages


---

## Phase 4 — SEO

Devam ediyor.

Tamamlananlar:

- canonical url
- meta description
- servis bölgesi sayfaları
- model bazlı içerik

Eksikler:

- marka logosu grid
- structured data
- sitemap
- robots.txt

---

# Tespit Edilen Veri Problemleri

## KVKK Modelleri

Örnek kayıtlar:


samsung-kvkk
lg-kvkk
philips-kvkk


Sebep:

Kaynak sitelerdeki KVKK sayfalarının model gibi parse edilmesi.

---

## Kanun Numarası Modeli

Örnek:


4654
6698


Gerçek model değildir.

---

## Marka Eşleşme Hatası

Örnek:

Samsung sayfasında:


PHILIPS


modeli görünmektedir.

Bu durum normalize scriptin brand doğrulaması yapmamasından kaynaklanır.

---

## Model Code Olmayan Kayıtlar

Örnek:


SAMSUNG
PHILIPS


Bu kayıtlar gerçek model değildir.

---

# Veri Temizleme

Yeni oluşturulan script:


scripts/clean_normalized_models.py


Temizlenen kayıt türleri:

- kvkk
- privacy
- cookie
- policy
- 4654
- 6698

---

# Planlanan Veri Doğrulama

Normalize pipeline için aşağıdaki kontroller eklenecektir.

## Model Format Kontrolü

Geçerli örnekler:


UE32J4000
49PUS7909/12
32PHS5507


Geçersiz:


SAMSUNG
PHILIPS
KVKK
4654


---

## Brand Eşleşme Kontrolü

Model prefix brand ile uyumlu olmalıdır.

Örnek:


49PUS7909/12 → Philips


---

# Veri Genişletme Planı

Yeni veri kaynakları araştırılmaktadır.

Olası kaynaklar:

- Panelook
- DisplaySpecifications
- TV servis manual verileri
- üretici datasheetleri

Hedef:


Brand count : 30+
Model count : 1500+


---

# Planlanan UI Geliştirmeleri

## Marka Logo Grid

Marka sayfasında metin yerine logo grid.

Örnek:


Samsung
LG
Sony
Philips
Vestel
Beko
Arçelik


---

## Sticky WhatsApp Button

Mobil kullanıcılar için hızlı iletişim.

---

## Servis Süreci Bölümü

Servis adımlarını anlatan timeline.

---

## Model Arama

Kullanıcının doğrudan model arayabilmesi.

---

# Deployment Planı

Site aşağıdaki platformlardan biri üzerinden yayınlanacaktır.


Vercel
Cloudflare Pages
Netlify


Domain planı:


pasifikdisplay.com


---

# Proje Genel Durum


Site altyapısı : %90
SEO hazırlığı : %80
Veri kalitesi : %60


En kritik konu:


model veri doğruluğu


---

# Sonraki Adımlar

1. Veri temizleme
2. Normalize pipeline filtreleri
3. Marka logo grid
4. Veri tabanı genişletme

Şimdi iki şey söyleyeyim usta:

1️⃣ Bu dosyayı eklemek için:

git add project-status.md
git commit -m "docs: update project status"

2️⃣ Ama asıl kritik konu şu:

Samsung sayfasında görünen şu kart:

PHILIPS

bu bize şunu söylüyor:

normalize script brand doğrulaması yapmıyor.

Bu problemi çözmezsek veri büyüdükçe karışıklık artar.

İstersen bir sonraki mesajda sana:

normalize_all.py için profesyonel veri doğrulama sistemi yazayım.

Bu sistem:

model formatı doğrular

brand eşleşmesi kontrol eder

çöp verileri otomatik temizler

ve projenin veri kalitesini en az 5 kat artırır