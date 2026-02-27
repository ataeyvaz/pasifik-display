# Pasifik Display — Proje Durum Takibi

> Amaç: Profesyonel, SEO uyumlu, ölçeklenebilir TV panel katalog sistemi.
> Stack: Astro + Tailwind + TypeScript + Offline Python Data Pipeline

---

# 📍 CURRENT STAGE

Altyapı ve veri hattı kuruldu.  
Brand listeleme çalışıyor.  
Model detay ve panel sistemi sıradaki kritik adım.

---

## 🧱 PHASE 0 — Altyapı & Veri Hattı

### Core Setup
- [x] Astro proje oluşturuldu
- [x] Tailwind entegre edildi
- [x] TypeScript aktif
- [x] BaseLayout / Header / Footer oluşturuldu
- [x] UTF-8 (BOM'suz) encoding temizlendi
- [x] GitHub repo aktif
- [x] İlk stabil commit yapıldı

### Offline Data Pipeline
- [x] data/raw/ klasör yapısı kuruldu
- [x] Zeroteknik ham veri alındı
- [x] Solobu ham veri alındı
- [x] Normalize script yazıldı
- [x] data/normalized/brands.json üretiliyor
- [x] data/normalized/models-by-brand.json üretiliyor
- [x] modelCount hesaplanıyor
- [x] isFeatured alanı normalize aşamasında set ediliyor
- [x] Runtime'da dış site bağımlılığı YOK

### Veri Politikaları
- [x] TV-only kuralı
- [x] Monitor verileri sistemden çıkarılacak
- [x] Kaynak önceliği tanımlandı
- [x] Slug yapısı sabitlendi (SEO kritik)

### Experimental
- [⚠] NUKS scraping denendi
- [⚠] Cloudflare / JS gate nedeniyle sürdürülebilir değil
- [⚠] Core mimarinin parçası değil

---

## 🎨 PHASE 1 — Design System

- [x] Renk sistemi
- [x] Typography
- [x] Button
- [x] Badge
- [x] Card
- [x] SpecTable
- [ ] Responsive final kontrol
- [ ] Accessibility kontrolü

---

## 🧭 PHASE 2 — Sayfa Yapısı

### Çalışan
- [x] Ana sayfa (demo)
- [x] Demo model sayfası
- [x] Marka listeleme sayfası (/markalar)
- [x] Marka detay sayfası (/markalar/[brand]/)

### Eksik (SEO Kritik)
- [ ] Model detay sayfası (/markalar/[brand]/[model]/)
- [ ] Panel detay sayfası
- [ ] Arama sayfası

---

## 📊 PHASE 3 — Veri Katmanı (Aktif Aşama)

### Brand Model
- [x] Brand type normalize edildi
- [x] modelCount alanı aktif
- [x] isFeatured mantığı çalışıyor

### Model Model
- [x] models-by-brand normalize çalışıyor
- [ ] Strict TS tip uyumu tamamlanacak
- [ ] getStaticPaths model seviyesinde eklenecek

### Panel Model
- [ ] model-panel-map.json yapısı oluşturuldu
- [ ] Başlangıçta boş olabilir
- [ ] Panel DB manuel büyütülecek (vendor bağımsız strateji)

---

## 🔎 PHASE 4 — SEO Motoru

- [ ] Title template
- [ ] Meta description template
- [ ] Canonical
- [ ] Breadcrumb schema
- [ ] Product schema
- [ ] Sitemap
- [ ] robots.txt

---

## ⚡ PHASE 5 — Performans

- [ ] Pagefind
- [ ] Pagination
- [ ] Image optimization
- [ ] Core Web Vitals test

---

## 📷 GELECEK ÖZELLİKLER

### Seri / Model Tanıma
- [ ] Marka bazlı regex kuralları
- [ ] Model format doğrulama
- [ ] Hatalı format uyarısı

### Kamera ile Okuma
- [ ] Barcode scan
- [ ] OCR ile model okuma
- [ ] Otomatik form doldurma
- [ ] Kullanıcı onayı

---

# 📌 STRATEJİK KARARLAR

- Sistem sadece TV üzerine kuruludur.
- Slug yapısı değiştirilmeyecek.
- Runtime'da dış site isteği yapılmayacak.
- Panel DB zamanla doğrulanmış veri ile büyütülecek.
- Model sayfası SEO motorudur.
- NUKS scraping çekirdek planın parçası değildir.

---

# 🎯 NEXT STEP

1. Model detay route’unu oluştur.
2. getStaticPaths model seviyesinde aktif et.
3. Panel alanını UI’da hazırla (veri olmasa bile alan yerleşsin).
4. SEO template sistemine başla.

---

# 🗓 Son Güncelleme

Tarih: 2026-02-27  
Durum: Data + Brand sistemi stabil  
Bir sonraki adım: Model detay sayfası


## CURRENT STATUS (Güncel Durum)

### ✅ Tamamlananlar
- Astro proje çalışır durumda (`npm run dev` OK).
- UTF-8 / bozuk karakter sorunu temizlendi.
- GitHub repo kuruldu, commit/push akışı oturdu.
- Offline veri hattı çalışıyor:
  - `data/normalized/brands.json` (modelCount + isFeatured + sources)
  - `data/normalized/models-by-brand.json`
  - `data/normalized/solobu-product-urls-by-brand.json`
- /markalar sayfası çalışıyor (featured + A-Z liste).
- /markalar/[brand]/ sayfası çalışıyor (brand bazlı model listeleme).
- TV-only policy aktif (monitör verisi çıkarılacak).
- Runtime'da dış site bağımlılığı YOK (solobu/zeroteknik/nuks sadece offline normalize için).

### ⚠️ Bilinen Sorunlar / Notlar
- Git uyarıları: LF/CRLF dönüşümü görünüyor (Windows line endings). Şimdilik kritik değil.
- NUKS scraping: Cloudflare / JS gate nedeniyle otomatik scrape sürdürülebilir değil (items.json boş kalabiliyor).

### 🎯 Sıradaki Hedef (Next)
1. Model detay route’unu ekle: `/markalar/[brand]/[model]/` (Phase 1 kritik SEO sayfası).
2. `Brand` ve `Model` tiplerini normalized JSON ile %100 uyumlu hale getir (TypeScript strict).
3. Panel DB stratejisi:
   - Başlangıç: `data/normalized/model-panel-map.json` boş olabilir
   - UI: panel yoksa "seri no ile doğrulayın / WhatsApp" callout göster
   - Sonradan: doğrulanmış panel kodları manuel/operasyonel olarak eklenecek (vendor bağımsız).
4. Arama (Phase 3): Pagefind planı — şimdilik ertelendi.

### ✅ Kararlar (Decision Log)
- Proje adı: Pasifik Display
- Sadece TV (monitorler çıkarılacak)
- Featured brand listesi sabit tutulur (ekleme olabilir, çıkarma yok gibi)
- Slug kuralları sabit; yayın sonrası değişirse 301 gerekir
- Offline normalize → runtime local JSON (dış link/istek yok)
- NUKS: otomatik scraping "experimental", core planın parçası değil

NUKS scraping’in “core değil / experimental” olduğu kararı

Model detay sayfasının henüz yok/404 olduğu (Phase 1’in ana işi)