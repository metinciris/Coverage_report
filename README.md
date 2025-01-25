# Coverage_Report - Toplu NGS Kalite Değerlendirme Aracı

Bu proje, `.pdf` formatında üretilen hedef bölge kapsama (coverage) raporlarını (örneğin Illumina Ampliseq Coverage Analysis gibi) otomatik olarak analiz eder ve her rapor için özet bir “NGS Kalite Raporu” oluşturur. Rapor, ortalama ve medyan kapsama değerlerinden düşük kapsamalı bölge oranına kadar pek çok metriği dikkate alarak örneklerin kalitesini değerlendirir.

![screen.png](screen.png)

## Özellikler
- Birden fazla PDF dosyası için toplu rapor oluşturma
- Ortalama ve medyan kapsama, düşük kapsamalı bölge sayısı, medyan/ortalama oranı gibi kritik metriklerin hesaplanması
- Otomatik puanlama ve kalite seviyesinin belirlenmesi (MÜKEMMEL, ÇOK İYİ, İYİ, İNCELEME GEREKLİ, TEKRAR EDİLMELİ)
- Bulunan sorunlara göre iyileştirme önerileri sunma
- Toplu sonuç özetini ve örnek bazında detaylı sonuçları aynı arayüzde gösterme
- Tek tıkla tüm sonuçların kopyalanması

## Kurulum

1. Projeyi klonlayın veya indirin:

   ```bash
   git clone https://github.com/kullaniciadi/NGSQualityReport.git
   cd NGSQualityReport
   ```

2. Gerekli Python paketlerini yükleyin (tercihen bir sanal ortam içinde):

   ```bash
   pip install PyPDF2 matplotlib
   ```

> **Not:** `tkinter` Python ile birlikte gelir. Ek bir kurulum gerektirmez.

## Kullanım

1. `NGSQualityReport.py` dosyasını çalıştırın:

   ```bash
   python NGSQualityReport.py
   ```

2. Açılan arayüz üzerinden **“PDF Dosyaları Seç”** butonuna basarak istediğiniz sayıda `.pdf` dosyasını seçin.

3. **“Rapor Oluştur”** butonuna basarak analiz sürecini başlatın. Her dosya için:
   - Ortalama kapsama (mean coverage)
   - Medyan kapsama (median coverage)
   - Düşük kapsamalı bölge oranı
   - Medyan/Ortalama oranı
   - vb. metrikler hesaplanır ve puanlanır.

4. **“Tümünü Kopyala”** butonu ile oluşturulan raporları pano (clipboard) belleğine kopyalayabilir, herhangi bir metin düzenleyiciye yapıştırabilirsiniz.

5. İsterseniz, analiz işlemi sürerken **“İptal”** butonuna basarak kalan rapor oluşturma işlemlerini iptal edebilirsiniz.


## Örnek Çıktı

Aşağıdaki örnekte, 15 adet PDF raporu işlendiğini varsayıyoruz. Çıktıda “VAKA1”, “VAKA2” gibi kimlikler örnek amaçlı kullanılmıştır. Kod, gerçek veride raporun oluşturulduğu PDF dosyalarının ismine göre hasta/örnek kimliklerini otomatik tespit edecektir.

```text
================================================================================

!!! UYARI: Bu rapordaki sonuçlar ve öneriler tavsiye niteliğindedir. 
    Nihai değerlendirme için laboratuvar sorumlusu ile görüşülmelidir. !!!

TOPLU SONUC OZETI (15 örnek):
--------------------------------------------------------------------------------
VAKA1: Ort=227.5x, Med=175.0x, M/O=0.77, Düşük=56.3%, Kalite=TEKRAR EDILMELI (50/100)
VAKA2: Ort=2199.1x, Med=1889.0x, M/O=0.86, Düşük=0.8%, Kalite=MUKEMMEL (100/100)
VAKA3: Ort=2094.6x, Med=1832.0x, M/O=0.87, Düşük=0.8%, Kalite=MUKEMMEL (100/100)
VAKA4: Ort=737.3x, Med=571.0x, M/O=0.77, Düşük=2.5%, Kalite=COK IYI (80/100)
VAKA5: Ort=595.5x, Med=472.0x, M/O=0.79, Düşük=5.5%, Kalite=COK IYI (80/100)
VAKA6: Ort=1495.3x, Med=1244.0x, M/O=0.83, Düşük=0.9%, Kalite=MUKEMMEL (100/100)
VAKA7: Ort=151.0x, Med=106.0x, M/O=0.70, Düşük=81.9%, Kalite=TEKRAR EDILMELI (0/100)
VAKA8: Ort=386.4x, Med=279.0x, M/O=0.72, Düşük=19.9%, Kalite=TEKRAR EDILMELI (50/100)
VAKA9: Ort=94.0x, Med=63.0x, M/O=0.67, Düşük=94.0%, Kalite=TEKRAR EDILMELI (0/100)
VAKA10: Ort=843.1x, Med=758.0x, M/O=0.90, Düşük=0.9%, Kalite=MUKEMMEL (100/100)
VAKA11: Ort=170.2x, Med=125.0x, M/O=0.73, Düşük=81.9%, Kalite=TEKRAR EDILMELI (0/100)
VAKA12: Ort=979.5x, Med=819.0x, M/O=0.84, Düşük=1.1%, Kalite=MUKEMMEL (100/100)
VAKA13: Ort=175.2x, Med=123.0x, M/O=0.70, Düşük=84.0%, Kalite=TEKRAR EDILMELI (0/100)
VAKA14: Ort=374.7x, Med=292.0x, M/O=0.78, Düşük=40.1%, Kalite=TEKRAR EDILMELI (50/100)
VAKA15: Ort=1038.0x, Med=907.0x, M/O=0.87, Düşük=0.9%, Kalite=MUKEMMEL (100/100)

KALITE DAGILIMI:
• MUKEMMEL: 6 örnek (%40.0)
• COK IYI: 2 örnek (%13.3)
• TEKRAR EDILMELI: 7 örnek (%46.7)

GENEL BASARI ORANI: %53.3
ORTALAMA KALITE PUANI: 60.7/100


================================================================================
NGS KALITE RAPORU - VAKA1
================================================================================

GENEL KALITE DEGERLENDIRMESI:
Kalite Seviyesi: TEKRAR EDILMELI (50/100)

TEMEL METRIKLER:
• Ortalama Kapsama: 227.5x (Min: 200x)
• Medyan Kapsama: 175.0x (Min: 150x)
• Medyan/Ortalama Oranı: 0.77 (Min: 0.8)
• 50x Üzeri Kapsama: %92.9
• Spesifiklik: %90.0

KAPSAMA DAGILIMI:
Kapsama dağılımı verisi bulunamadı

HEDEF BOLGE ISTATISTIKLERI:
• Toplam Hedef Bölge Sayısı: 856
• Toplam Hedef Uzunluk: 165 bp
• Düşük Kapsamalı Bölge Sayısı: 482 (%56.3)

TESPIT EDILEN SORUNLAR:
• Yüksek oranda düşük kapsamalı bölge: %56.3 (Max: %10)
• Düşük Medyan/Ortalama oranı: 0.77 (Min: 0.8)

IYILESTIRME ONERILERI:
• DNA miktarını kontrol edin (olası düşük DNA miktarı)
• Kütüphane hazırlama sürecini kontrol edin

================================================================================

...
```

(Örnek çıktının devamı, her bir vaka için benzer detaylı raporlar üretir.)

## Katkıda Bulunma

- Hataları veya iyileştirmeleri [Issues](https://github.com/kullaniciadi/NGSQualityReport/issues) sekmesi üzerinden bildirebilirsiniz.
- Pull request’ler memnuniyetle karşılanır.

## Lisans

Bu proje MIT Lisansı ile lisanslanmıştır. Daha fazla bilgi için [LICENSE](LICENSE) dosyasına bakabilirsiniz.

---

**Not:** Bu kod, laboratuvar çalışmalarınızı kolaylaştırmak amacıyla örnek bir “kapsama analizi raporu” oluşturmaktadır. Nihai kararlar için mutlaka laboratuvar sorumlusuyla birlikte değerlendirme yapınız.

---

