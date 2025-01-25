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

## Kod

```python
import os
import re
import time
import threading
import PyPDF2
from tkinter import Tk, Frame, Label, Button, Text, Scrollbar, filedialog, WORD, END, LEFT, RIGHT, Y, BOTH, X
from tkinter import ttk
import matplotlib.pyplot as plt
from io import BytesIO

# Kalite değerlendirme sabitleri
MIN_MEAN_COVERAGE = 200  # Minimum ortalama kapsama
MIN_MEDIAN_COVERAGE = 150  # Minimum medyan kapsama
MIN_MED_MEAN_RATIO = 0.80  # Minimum medyan/ortalama oranı
MAX_LOW_COVERAGE_PERCENT = 10  # Maksimum düşük kapsamalı bölge yüzdesi

class NGSQualityReport:
    def __init__(self):
        self.root = Tk()
        self.root.title("NGS Kalite Rapor v4.4")
        self.selected_files = []
        self.cancel_requested = False
        self.setup_gui()

    def setup_gui(self):
        self.root.geometry("1200x800")
        
        # Ana çerçeve
        main_frame = Frame(self.root, padx=20, pady=20)
        main_frame.pack(expand=True, fill=BOTH)
        
        # Kontrol butonları
        control_frame = Frame(main_frame)
        control_frame.pack(fill=X, pady=10)
        
        select_button = Button(control_frame, text="PDF Dosyaları Seç",
                             command=self.select_files, font=('Arial', 12))
        select_button.pack(side=LEFT, padx=5)
        
        self.files_label = Label(control_frame, text="Seçili: 0",
                               font=('Arial', 12))
        self.files_label.pack(side=LEFT, padx=5)
        
        report_button = Button(control_frame, text="Rapor Oluştur",
                             command=self.on_generate_click,
                             font=('Arial', 12))
        report_button.pack(side=LEFT, padx=5)
        
        self.cancel_button = Button(control_frame, text="İptal",
                                  command=self.cancel_reports,
                                  font=('Arial', 12), state='disabled')
        self.cancel_button.pack(side=LEFT, padx=5)
        
        copy_button = Button(control_frame, text="Tümünü Kopyala",
                           command=self.copy_all, font=('Arial', 12))
        copy_button.pack(side=RIGHT, padx=5)
        
        # İlerleme çubuğu
        self.progress = ttk.Progressbar(control_frame, orient="horizontal",
                                      length=200, mode="determinate")
        self.progress.pack(side=RIGHT, padx=5)
        
        # Sonuç metin alanı
        text_frame = Frame(main_frame)
        text_frame.pack(expand=True, fill=BOTH)
        
        scrollbar = Scrollbar(text_frame)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        self.result_text = Text(text_frame, wrap=WORD, font=('Consolas', 12),
                              yscrollcommand=scrollbar.set)
        self.result_text.pack(side=LEFT, expand=True, fill=BOTH)
        scrollbar.config(command=self.result_text.yview)

    def select_files(self):
        self.selected_files = filedialog.askopenfilenames(
            filetypes=[("PDF files", "*.pdf")],
            title="Coverage Raporlarını Seçin"
        )
        self.files_label.config(text=f"Seçili: {len(self.selected_files)}")

    def parse_coverage_data(self, file_path):
        try:
            with open(file_path, 'rb') as file:
                pdf = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf.pages:
                    text += page.extract_text()

                # Temel metrikleri çıkar
                target_regions = int(self.extract_value(text, r"Number target regions\s+(\d+)") or 856)
                total_length = int(self.extract_value(text, r"Total length of targeted regions\s+(\d+)") or 165127)
                mean_coverage = float(self.extract_value(text, r"Average coverage\s+(\d+\.?\d*)") or 0)
                median_coverage = float(self.extract_value(text, r"Median coverage\s+(\d+\.?\d*)") or 0)
                
                # Coverage dağılımı için yeni pattern
                coverage_pattern = r"≥(\d+)% of the targeted region has\s+coverage at least 50\s+\d+\s+(\d+\.?\d*)"
                coverage_matches = re.findall(coverage_pattern, text)
                coverage_values = [(int(percent), float(value)) for percent, value in coverage_matches]
                
                # 100% coverage değeri
                target_50x = next((value for percent, value in coverage_values if percent == 100), 0)
                
                # Düşük kapsamalı bölgeler
                low_coverage_pattern = r"Number of target regions with coverage < 50\s+(\d+)"
                low_coverage = int(self.extract_value(text, low_coverage_pattern) or 0)
                
                # Spesifiklik (varsayılan değer)
                specificity = 90.0

                return {
                    'mean_coverage': mean_coverage,
                    'median_coverage': median_coverage,
                    'target_50x': target_50x,
                    'coverage_distribution': coverage_values,
                    'target_regions': target_regions,
                    'total_length': total_length,
                    'low_coverage_regions': low_coverage,
                    'specificity': specificity,
                    'low_coverage_percentage': (low_coverage / target_regions) * 100 if target_regions else 0,
                    'med_mean_ratio': (median_coverage / mean_coverage) if mean_coverage else 0
                }
        except Exception as e:
            print(f"PDF parse hatası ({file_path}): {str(e)}")
            return self.get_default_values()

    def extract_value(self, text, pattern):
        match = re.search(pattern, text)
        return match.group(1) if match else None

    def evaluate_quality(self, data):
        score = 100
        issues = []
        recommendations = []
        
        # Düşük kapsamalı bölge kontrolü (30 puan)
        if data['low_coverage_percentage'] > MAX_LOW_COVERAGE_PERCENT:
            score -= 30
            issues.append(f"Yüksek oranda düşük kapsamalı bölge: %{data['low_coverage_percentage']:.1f} (Max: %{MAX_LOW_COVERAGE_PERCENT})")
            if data['low_coverage_percentage'] > 80:
                recommendations.append("Örnek kalitesini kontrol edin (olası doku otolizi/nekrozu)")
            elif data['low_coverage_percentage'] > 50:
                recommendations.append("DNA miktarı ve kalitesini kontrol edin (olası doku azlığı/degradasyonu)")
            else:
                recommendations.append("Hedef bölge kapsamasını kontrol edin (olası teknik sorun)")

        # Ortalama kapsama kontrolü (30 puan)
        if data['mean_coverage'] < MIN_MEAN_COVERAGE:
            score -= 30
            issues.append(f"Düşük ortalama kapsama: {data['mean_coverage']:.1f}x (Min: {MIN_MEAN_COVERAGE}x)")
            if data['mean_coverage'] < 100:
                recommendations.append("DNA kalitesini ve miktarını kontrol edin (olası düşük DNA konsantrasyonu)")
            else:
                recommendations.append("Sekanslama derinliğini kontrol edin")

        # Medyan/Ortalama oranı kontrolü (20 puan)
        if data['med_mean_ratio'] < MIN_MED_MEAN_RATIO:
            score -= 20
            issues.append(f"Düşük Medyan/Ortalama oranı: {data['med_mean_ratio']:.2f} (Min: {MIN_MED_MEAN_RATIO})")
            if data['med_mean_ratio'] < 0.7:
                recommendations.append("DNA fragmentasyon seviyesini kontrol edin (olası DNA degradasyonu)")
            else:
                recommendations.append("Kütüphane hazırlama sürecini kontrol edin")

        # Medyan kapsama kontrolü (20 puan)
        if data['median_coverage'] < MIN_MEDIAN_COVERAGE:
            score -= 20
            issues.append(f"Düşük medyan kapsama: {data['median_coverage']:.1f}x (Min: {MIN_MEDIAN_COVERAGE}x)")
            recommendations.append("Sekanslama kalitesini kontrol edin")

        # Kalite seviyesi belirleme
        if score >= 90:
            quality = "MUKEMMEL"
            color = "darkgreen"
        elif score >= 80:
            quality = "COK IYI"
            color = "green"
        elif score >= 70:
            quality = "IYI"
            color = "orange"
        elif score >= 60:
            quality = "INCELEME GEREKLI"
            color = "orangered"
        else:
            quality = "TEKRAR EDILMELI"
            color = "red"

        return {
            'score': score,
            'quality': quality,
            'color': color,
            'issues': issues,
            'recommendations': recommendations
        }

    def format_report(self, patient_id, data, quality_result):
        # Kapsama dağılımı formatı
        coverage_dist = "\n".join([
            f"≥{percent}% bölge kapsaması: %{value:.1f}"
            for percent, value in data['coverage_distribution']
        ]) if data['coverage_distribution'] else "Kapsama dağılımı verisi bulunamadı"
        
        # Sorunlar ve öneriler formatı
        issues = "\n".join(['• ' + issue for issue in quality_result['issues']]) \
                if quality_result['issues'] else 'Önemli bir sorun tespit edilmedi.'
        
        recommendations = "\n".join(['• ' + rec for rec in quality_result['recommendations']]) \
                         if quality_result['recommendations'] else 'İyileştirme önerisi bulunmuyor.'

        report = f"""
{'='*80}
NGS KALITE RAPORU - {patient_id}
{'='*80}

GENEL KALITE DEGERLENDIRMESI:
Kalite Seviyesi: {quality_result['quality']} ({quality_result['score']}/100)

TEMEL METRIKLER:
• Ortalama Kapsama: {data['mean_coverage']:.1f}x (Min: {MIN_MEAN_COVERAGE}x)
• Medyan Kapsama: {data['median_coverage']:.1f}x (Min: {MIN_MEDIAN_COVERAGE}x)
• Medyan/Ortalama Oranı: {data['med_mean_ratio']:.2f} (Min: {MIN_MED_MEAN_RATIO})
• 50x Üzeri Kapsama: %{data['target_50x']:.1f}
• Spesifiklik: %{data['specificity']:.1f}

KAPSAMA DAGILIMI:
{coverage_dist}

HEDEF BOLGE ISTATISTIKLERI:
• Toplam Hedef Bölge Sayısı: {data['target_regions']}
• Toplam Hedef Uzunluk: {data['total_length']} bp
• Düşük Kapsamalı Bölge Sayısı: {data['low_coverage_regions']} (%{data['low_coverage_percentage']:.1f})

TESPIT EDILEN SORUNLAR:
{issues}

IYILESTIRME ONERILERI:
{recommendations}

{'='*80}
"""
        return report

    def get_default_values(self):
        return {
            'mean_coverage': 0,
            'median_coverage': 0,
            'target_50x': 0,
            'coverage_distribution': [],
            'target_regions': 856,
            'total_length': 165127,
            'low_coverage_regions': 0,
            'specificity': 90.0,
            'low_coverage_percentage': 0,
            'med_mean_ratio': 0
        }

    def generate_reports(self):
        self.result_text.delete('1.0', END)
        warning = """
!!! UYARI: Bu rapordaki sonuçlar ve öneriler tavsiye niteliğindedir. 
    Nihai değerlendirme için laboratuvar sorumlusu ile görüşülmelidir. !!!"""
        
        summary = f"""{'='*80}
{warning}

TOPLU SONUC OZETI ({len(self.selected_files)} örnek):
{'-'*80}
"""
        successful_samples = 0
        total_score = 0
        quality_counts = {'MUKEMMEL': 0, 'COK IYI': 0, 'IYI': 0, 'INCELEME GEREKLI': 0, 'TEKRAR EDILMELI': 0}
        
        for i, file_path in enumerate(self.selected_files, 1):
            if self.cancel_requested:
                self.result_text.insert(END, "\nİşlem iptal edildi.\n")
                break
                
            try:
                patient_id = os.path.basename(file_path).split('_')[0]
                data = self.parse_coverage_data(file_path)
                quality_result = self.evaluate_quality(data)
                
                quality_counts[quality_result['quality']] += 1
                
                if quality_result['score'] >= 70:
                    successful_samples += 1
                total_score += quality_result['score']
                
                summary += (f"{patient_id}: "
                          f"Ort={data['mean_coverage']:.1f}x, "
                          f"Med={data['median_coverage']:.1f}x, "
                          f"M/O={data['med_mean_ratio']:.2f}, "
                          f"Düşük={data['low_coverage_percentage']:.1f}%, "
                          f"Kalite={quality_result['quality']} "
                          f"({quality_result['score']}/100)\n")
                
                report = self.format_report(patient_id, data, quality_result)
                self.result_text.insert(END, report)
                
                self.progress["value"] = i
                self.root.update_idletasks()
                
            except Exception as e:
                print(f"Hata ({file_path}): {str(e)}")
                continue

        if self.selected_files:
            success_rate = (successful_samples / len(self.selected_files)) * 100
            avg_score = total_score / len(self.selected_files)
            
            summary += f"\nKALITE DAGILIMI:"
            for quality, count in quality_counts.items():
                if count > 0:
                    percentage = (count / len(self.selected_files)) * 100
                    summary += f"\n• {quality}: {count} örnek (%{percentage:.1f})"
            
            summary += f"\n\nGENEL BASARI ORANI: %{success_rate:.1f}"
            summary += f"\nORTALAMA KALITE PUANI: {avg_score:.1f}/100\n"

        self.result_text.insert('1.0', summary + "\n")
        self.cancel_button.config(state='disabled')
        self.result_text.see("1.0")

    def on_generate_click(self):
        if not self.selected_files:
            self.result_text.insert('1.0', "Lütfen önce dosya seçin.\n")
            return
            
        self.cancel_requested = False
        self.cancel_button.config(state='normal')
        self.progress["value"] = 0
        self.progress["maximum"] = len(self.selected_files)
        
        thread = threading.Thread(target=self.generate_reports)
        thread.start()

    def cancel_reports(self):
        self.cancel_requested = True
        self.cancel_button.config(state='disabled')

    def copy_all(self):
        content = self.result_text.get("1.0", END)
        self.root.clipboard_clear()
        self.root.clipboard_append(content)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = NGSQualityReport()
    app.run()
```

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

