# Pasifik Display — Proje Durum Takibi

> Amaç: Profesyonel, SEO uyumlu, ölçeklenebilir panel katalog sistemi.
> Stack: Astro + Tailwind + TypeScript

---

## 🧱 PHASE 0 — Altyapı Kurulumu

- [x] Astro proje oluşturuldu
- [x] Tailwind entegrasyonu yapıldı
- [x] TypeScript aktif
- [x] BaseLayout oluşturuldu
- [x] Header component oluşturuldu
- [x] Footer component oluşturuldu
- [x] Global CSS bağlandı
- [x] Encoding sorunları temizlendi
- [x] UTF-8 (BOM'suz) normalize edildi
- [ ] ESLint kurulumu
- [ ] Prettier kurulumu
- [ ] Strict TS kontrolü (astro check)
 DATA-0.1: data/raw/ klasöründe kaynak bazlı ham JSON çıktıları tutulacak:

data/raw/zeroteknik/brands.json

data/raw/zeroteknik/models-by-brand.json

data/raw/solobu/brands-led-tv.json

data/raw/solobu/products-by-brand.json

 DATA-0.2: TV-only kuralı data pipeline’da uygulanacak (monitör hiçbir aşamada içeri girmeyecek).

 DATA-0.3: Normalize script: data/normalized/brands.json, data/normalized/models/*.json, data/normalized/panels/*.json

 DATA-0.4: Kaynak önceliği (senin yazdığın “kaynak öncelikleri” satırına bağlanır):

Solobu = “panel ürünleri / SKU / stok gibi e-ticaret sinyali”

Zeroteknik = “marka slug / model listesi (uyumluluk/servis referansı)”

 DATA-0.5: Tek komutla çalıştırma:

python tools/scrape/run_all.py → raw üretir

python tools/normalize/run.py → normalized üretir
---

## 🎨 PHASE 1 — Design System

- [x] Renk paleti belirlendi (Trust & Service bazlı)
- [x] Typography (Inter + Mono) entegre edildi
- [x] Container component
- [x] Button component
- [x] Badge component
- [x] Card component
- [x] SpecTable component
- [ ] Responsive test (mobil-first kontrol)
- [ ] Accessibility kontrolü (aria, semantic tags)

---

## 🧭 PHASE 2 — Sayfa Yapısı

### Genel
- [x] Ana sayfa (UI demo)
- [x] Demo model sayfası
- [ ] Marka listeleme sayfası
- [ ] Marka detay sayfası
- [ ] Model detay sayfası (SEO kritik)
- [ ] Panel detay sayfası
- [ ] Arama sayfası (noindex)
### Marka Listeleme Geliştirmeleri

- [ ] Sadece TV modelleri (monitor desteği tamamen kaldırıldı)
- [ ] "Öne Çıkan Markalar" bölümü eklendi
- [ ] Öne çıkan marka listesi config dosyasından yönetiliyor
- [ ] A–Z marka listesi featured markalardan bağımsız çalışıyor
- [ ] Mobilde featured markalar yatay scroll
- [ ] Featured marka listesi genişletilebilir (3–5 marka eklenebilir yapı)


---

## 📊 PHASE 3 — Veri Katmanı

- [ ] Brand veri modeli
- [ ] Model veri modeli
- [ ] Panel veri modeli
- [ ] JSON klasör yapısı
- [ ] getStaticPaths implementasyonu
- [ ] Sitemap oluşturma
- [ ] robots.txt endpoint

### TV-Only Veri Politikası

- [ ] screenType alanı kaldırıldı veya sabitlendi (tv only)
- [ ] Monitor verileri sistemden çıkarıldı
- [ ] Veri import aşamasında monitor filtreleme eklendi
- [ ] URL yapısı sadece TV mantığına göre güncellendi

### Featured Brand Config

- [ ] featuredBrands.ts oluşturuldu
- [ ] Featured marka sırası manuel yönetilebilir
- [ ] Featured marka sistemi veri modelinden bağımsız çalışıyor
 SERIAL-3.1: “Kamera ile seri/model okuma” (OCR/Barkod) → web’de client-side kütüphane ile (ör: Barcode + OCR). Bu Phase 3 çünkü UI/SEO çekirdek oturmadan bunu eklemek projeyi dağıtır.


---

## 🔎 PHASE 4 — SEO Motoru

- [ ] Title template sistemi
- [ ] Meta description template
- [ ] Canonical tag
- [ ] Breadcrumb schema
- [ ] Product schema (panel sayfası)
- [ ] Internal linking stratejisi
- [ ] Lighthouse SEO ≥ 90

---

## ⚡ PHASE 5 — Performans & Ölçek

- [ ] Image optimization
- [ ] Core Web Vitals test
- [ ] Pagination sistemi
- [ ] Pagefind arama entegrasyonu
- [ ] JSON → API abstraction layer

### Seri / Model Tanıma Sistemi

- [ ] Marka bazlı model format kuralları tanımlandı
- [ ] Regex tabanlı format doğrulama sistemi
- [ ] Model numarası örnek gösterim UI
- [ ] Hatalı format için kullanıcı uyarı sistemi
- [ ] Manuel giriş fallback mekanizması

### Kamera ile Okuma (Gelecek Özellik)

- [ ] Barcode scan (mobil uyumlu)
- [ ] OCR ile model/seri okuma (deneysel)
- [ ] Okunan verinin otomatik form doldurması
- [ ] Kullanıcı onay mekanizması

---

## 🛠 Teknik Stabilizasyon

- [ ] GitHub repository oluşturuldu
- [ ] İlk temiz commit
- [ ] Branch stratejisi (main / dev)
- [ ] .gitignore kontrolü
- [ ] README yazıldı

---

## 🚀 Uzun Vadeli

- [ ] Admin panel (ileride)
- [ ] Çoklu dil desteği
- [ ] Teklif formu entegrasyonu
- [ ] WhatsApp otomasyon
- [ ] Stok API entegrasyonu

---

# 📌 Notlar

- Slug yapısı değiştirilemez (SEO kritik).
- Model sayfası SEO motorudur.
- Encoding hataları tekrar yaşanmamalı.
- Commit atmadan önce test zorunlu.
- Sistem sadece TV panelleri üzerine kuruludur.
- Featured marka listesi stratejik olarak üstte sabitlenmiştir.
- Seri/model tanıma sistemi çekirdek mimariye entegre edilmeden modüler olarak geliştirilmelidir.

---

# 🎯 Son Güncelleme

Tarih: _________
Durum: _________
Bir sonraki adım: _________
