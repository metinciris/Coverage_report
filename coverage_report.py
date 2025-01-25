import os
import random
import re
import time
import threading
from tkinter import Tk, Frame, Label, Button, Text, Scrollbar, filedialog, WORD, END, LEFT, RIGHT, Y, BOTH, X
from tkinter import ttk

# Puanlama için kullanılan sabitler
MIN_MEAN_COVERAGE_FOR_0 = 300
MIN_MEAN_COVERAGE_FOR_10 = 400
MIN_MEAN_COVERAGE_FOR_20 = 500

MIN_RATIO_FOR_0 = 0.80
MIN_RATIO_FOR_10 = 0.85

MIN_TARGET_50X_FOR_0 = 90
MIN_TARGET_50X_FOR_15 = 95

MIN_SPECIFICITY_FOR_0 = 89
MIN_SPECIFICITY_FOR_5 = 90

MAX_LOW_COVERAGE_REGIONS_FOR_0 = 10
MAX_LOW_COVERAGE_REGIONS_FOR_5 = 5

class NGSQualityReport:
    def __init__(self):
        self.root = Tk()
        self.root.title("NGS Kalite Rapor v3.0")
        self.selected_files = []
        self.setup_gui()

    def setup_gui(self):
        self.root.geometry("1200x800")

        # Ana çerçeve
        main_frame = Frame(self.root, padx=20, pady=20)
        main_frame.pack(expand=True, fill=BOTH)

        # Üst kısım kontrol butonları
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

        # İlerleme göstergesi
        self.progress = ttk.Progressbar(control_frame, orient="horizontal",
                                        length=200, mode="determinate")
        self.progress.pack(side=RIGHT, padx=5)

        # Text widget ve scrollbar
        text_frame = Frame(main_frame)
        text_frame.pack(expand=True, fill=BOTH)

        scrollbar = Scrollbar(text_frame)
        scrollbar.pack(side=RIGHT, fill=Y)

        self.result_text = Text(text_frame,
                                wrap=WORD,
                                font=('Consolas', 12),
                                yscrollcommand=scrollbar.set)
        self.result_text.pack(side=LEFT, expand=True, fill=BOTH)

        scrollbar.config(command=self.result_text.yview)

    def select_files(self):
        """Kullanıcıya PDF dosyalarını seçtirmek için dosya diyalogu açar."""
        self.selected_files = filedialog.askopenfilenames(
            filetypes=[("PDF files", "*.pdf")],
            title="Coverage Raporlarını Seçin"
        )
        self.files_label.config(text=f"Seçili: {len(self.selected_files)}")

    def copy_all(self):
        """Text widget içeriğini panoya kopyalar."""
        content = self.result_text.get("1.0", END)
        self.root.clipboard_clear()
        self.root.clipboard_append(content)

    def evaluate_quality_weighted(self, data):
        """
        Ağırlıklı kalite değerlendirme sistemi.
        Puanlar: (30+20+30+10+10) = 100 üzerinden hesaplanır.
        """
        issues = []

        # 1. Ortalama Kapsama
        coverage_score = 30
        if data['mean_coverage'] < MIN_MEAN_COVERAGE_FOR_0:
            coverage_score = 0
            issues.append("Ortalama kapsama çok düşük")
        elif data['mean_coverage'] < MIN_MEAN_COVERAGE_FOR_10:
            coverage_score = 10
            issues.append("Ortalama kapsama düşük")
        elif data['mean_coverage'] < MIN_MEAN_COVERAGE_FOR_20:
            coverage_score = 20

        # 2. Medyan/Ortalama Oranı
        ratio = data['median_coverage'] / data['mean_coverage']
        ratio_score = 20
        if ratio < MIN_RATIO_FOR_0:
            ratio_score = 0
            issues.append("Medyan/Ortalama oranı kritik seviyede düşük")
        elif ratio < MIN_RATIO_FOR_10:
            ratio_score = 10
            issues.append("Medyan/Ortalama oranı düşük")

        # 3. 50x Üzeri Kapsama
        coverage_50x_score = 30
        if data['target_50x'] < MIN_TARGET_50X_FOR_0:
            coverage_50x_score = 0
            issues.append("50x kapsama kritik seviyede düşük")
        elif data['target_50x'] < MIN_TARGET_50X_FOR_15:
            coverage_50x_score = 15
            issues.append("50x kapsama düşük")

        # 4. Spesifiklik
        specificity_score = 10
        if data['specificity'] < MIN_SPECIFICITY_FOR_0:
            specificity_score = 0
            issues.append("Spesifiklik kritik seviyede düşük")
        elif data['specificity'] < MIN_SPECIFICITY_FOR_5:
            specificity_score = 5
            issues.append("Spesifiklik düşük")

        # 5. Düşük Kapsamalı Bölgeler
        low_coverage_score = 10
        if data['low_coverage_regions'] > MAX_LOW_COVERAGE_REGIONS_FOR_0:
            low_coverage_score = 0
            issues.append("Çok fazla düşük kapsamalı bölge")
        elif data['low_coverage_regions'] > MAX_LOW_COVERAGE_REGIONS_FOR_5:
            low_coverage_score = 5
            issues.append("Düşük kapsamalı bölge sayısı yüksek")

        # Toplam Skor
        total_score = (coverage_score + ratio_score +
                       coverage_50x_score + specificity_score +
                       low_coverage_score)

        # Kalite Seviyesi Belirleme
        if total_score >= 90:
            quality = "MUKEMMEL"
        elif total_score >= 80:
            quality = "COK IYI"
        elif total_score >= 70:
            quality = "IYI"
        elif total_score >= 60:
            quality = "INCELEME GEREKLI"
        else:
            quality = "TEKRAR EDILMELI"

        # Otomatik Düşürme Kuralları (örnek)
        if ratio < 0.85:
            quality = min(quality, "IYI")
        if data['specificity'] < 90:
            quality = min(quality, "IYI")
        if data['target_50x'] < 95:
            quality = min(quality, "IYI")

        return {
            'score': total_score,
            'quality': quality,
            'issues': issues,
            'metrics': {
                'coverage_score': coverage_score,
                'ratio_score': ratio_score,
                'coverage_50x_score': coverage_50x_score,
                'specificity_score': specificity_score,
                'low_coverage_score': low_coverage_score
            }
        }

    def parse_coverage_data(self, file_path):
        """
        Gerçek PDF parse fonksiyonunuzu burada geliştirebilirsiniz.
        Şu an örnek/dummy veri oluşturuyor.
        """
        # Örneğin pdfplumber kullanımı:
        """
        import pdfplumber
        try:
            with pdfplumber.open(file_path) as pdf:
                # pdf sayfaları üzerinde gezerek
                # bir regex veya string araması yapabilirsiniz
                # coverage = ...
                # median_coverage = ...
                # vs...
        except Exception as e:
            print("PDF parse hatası:", e)
            # Default veya 0 değerlerle geri dön
        """

        try:
            # PDF'ten gerçek metrikleri okuyamadığımız için
            # şimdilik random değer üretmeye devam ediyoruz.
            base_coverage = random.uniform(400, 600)
            median_cov = base_coverage * random.uniform(0.8, 0.95)
            target_50x_val = random.uniform(93, 97)

            return {
                'mean_coverage': round(base_coverage, 1),
                'target_50x': round(target_50x_val, 1),
                'min_coverage': round(random.uniform(25, 35), 1),
                'median_coverage': round(median_cov, 1),
                'max_coverage': round(base_coverage * 2.4, 1),
                '1x_coverage': round(random.uniform(99.8, 100), 1),
                '10x_coverage': round(random.uniform(99.5, 99.9), 1),
                '20x_coverage': round(random.uniform(99.0, 99.5), 1),
                '50x_coverage': round(random.uniform(97.0, 99.0), 1),
                '100x_coverage': round(random.uniform(94.0, 96.0), 1),
                '200x_coverage': round(random.uniform(83.0, 87.0), 1),
                '500x_coverage': round(random.uniform(73.0, 77.0), 1),
                'target_regions': 856,
                'total_length': 165127,
                'low_coverage_regions': round(random.uniform(5, 9)),
                'specificity': round(random.uniform(89.5, 91.5), 1)
            }
        except Exception as e:
            print(f"PDF parse sırasında hata: {e}")
            # Hata durumunda default değerlere dönebilirsiniz
            return {
                'mean_coverage': 0,
                'target_50x': 0,
                'min_coverage': 0,
                'median_coverage': 0,
                'max_coverage': 0,
                '1x_coverage': 0,
                '10x_coverage': 0,
                '20x_coverage': 0,
                '50x_coverage': 0,
                '100x_coverage': 0,
                '200x_coverage': 0,
                '500x_coverage': 0,
                'target_regions': 0,
                'total_length': 0,
                'low_coverage_regions': 0,
                'specificity': 0
            }

    def format_detailed_report(self, patient_id, data, quality_result):
        """Detaylı raporu string olarak formatlar."""
        issues_text = '\n'.join(['• ' + issue for issue in quality_result['issues']])\
            if quality_result['issues'] else 'Önemli bir sorun tespit edilmedi.'

        report = f"""{'='*80}
                    NGS KALITE RAPORU - {patient_id}
{'='*80}

GENEL KALITE DEGERLENDIRMESI:
---------------------------
Kalite Seviyesi: {quality_result['quality']}
Toplam Puan: {quality_result['score']}/100

METRIK PUANLARI:
--------------
Ortalama Kapsama: {quality_result['metrics']['coverage_score']}/30
Medyan/Ortalama Oranı: {quality_result['metrics']['ratio_score']}/20
50x Kapsama: {quality_result['metrics']['coverage_50x_score']}/30
Spesifiklik: {quality_result['metrics']['specificity_score']}/10
Düşük Kapsamalı Bölgeler: {quality_result['metrics']['low_coverage_score']}/10

DETAYLI METRIKLER:
----------------
Ortalama Kapsama: {data['mean_coverage']}x
Medyan Kapsama: {data['median_coverage']}x
Medyan/Ortalama Oranı: {data['median_coverage']/data['mean_coverage']:.2f}
50x Üzeri Kapsama: %{data['target_50x']}
Minimum Kapsama: {data['min_coverage']}x
Maksimum Kapsama: {data['max_coverage']}x

KAPSAMA ANALIZI:
--------------
1x   Kapsama: %{data['1x_coverage']}  (Hedef: >99.5%) {'✓' if data['1x_coverage'] > 99.5 else '⚠️'}
10x  Kapsama: %{data['10x_coverage']} (Hedef: >99.0%) {'✓' if data['10x_coverage'] > 99.0 else '⚠️'}
20x  Kapsama: %{data['20x_coverage']} (Hedef: >98.0%) {'✓' if data['20x_coverage'] > 98.0 else '⚠️'}
50x  Kapsama: %{data['50x_coverage']} (Hedef: >95.0%) {'✓' if data['50x_coverage'] > 95.0 else '⚠️'}
100x Kapsama: %{data['100x_coverage']} (Hedef: >90.0%) {'✓' if data['100x_coverage'] > 90.0 else '⚠️'}
200x Kapsama: %{data['200x_coverage']} (Hedef: >80.0%) {'✓' if data['200x_coverage'] > 80.0 else '⚠️'}
500x Kapsama: %{data['500x_coverage']} (Hedef: >70.0%) {'✓' if data['500x_coverage'] > 70.0 else '⚠️'}

KALITE METRIKLERI:
----------------
Hedef Bölge Sayısı: {data['target_regions']}
Toplam Hedef Uzunluk: {data['total_length']}
Düşük Kapsamalı Bölge Sayısı (<50x): {data['low_coverage_regions']}
Spesifiklik Oranı: %{data['specificity']}

TESPIT EDILEN SORUNLAR:
---------------------
{issues_text}

{'='*80}
"""
        return report

    def on_generate_click(self):
        """Rapor oluşturma için threading üzerinden çağırılır."""
        if not self.selected_files:
            self.result_text.insert('1.0', "Lütfen önce dosya seçin.\n")
            return

        # İptal butonunu aktifleştir ve progress sıfırla
        self.cancel_requested = False
        self.cancel_button.config(state='normal')
        self.progress["value"] = 0
        self.progress["maximum"] = len(self.selected_files)

        # Arka planda rapor oluşturma
        thread = threading.Thread(target=self.generate_reports)
        thread.start()

    def cancel_reports(self):
        """İptal butonuna basıldığında, iptal isteğini işaretler."""
        self.cancel_requested = True
        self.cancel_button.config(state='disabled')

    def generate_reports(self):
        """Seçili dosyaları parse ederek rapor oluşturur."""
        self.result_text.delete('1.0', END)
        all_results = []
        summary = f"""{'='*80}\nTOPLU SONUC OZETI ({len(self.selected_files)} dosya):\n{'-'*80}\n"""

        for i, file_path in enumerate(self.selected_files, start=1):
            if self.cancel_requested:
                self.result_text.insert(END, "\nİşlem iptal edildi.\n")
                break

            patient_id = os.path.basename(file_path).split('_')[0]
            data = self.parse_coverage_data(file_path)
            quality_result = self.evaluate_quality_weighted(data)

            all_results.append({
                'patient_id': patient_id,
                'data': data,
                'quality_result': quality_result
            })

            summary += (f"{patient_id}: "
                        f"Ort={data['mean_coverage']}x, "
                        f"Med={data['median_coverage']}x, "
                        f"50x>=%{data['target_50x']}, "
                        f"Kalite={quality_result['quality']} "
                        f"(Puan: {quality_result['score']})\n")

            # Progress güncelle
            self.progress["value"] = i
            time.sleep(0.2)  # Gerçek senaryoda parse süresini simüle ediyoruz

        # Eğer iptal edilmediyse özet devam etsin
        if not self.cancel_requested:
            # Başarı istatistikleri
            successful = sum(1 for r in all_results if r['quality_result']['score'] >= 70)
            if len(all_results) > 0:
                success_rate = (successful / len(all_results)) * 100
            else:
                success_rate = 0

            summary += f"\nGENEL BASARI ORANI: %{success_rate:.1f}\n"

            # Sorunlu örnekler
            failed_samples = [r for r in all_results if r['quality_result']['issues']]
            if failed_samples:
                summary += "\nINCELENMESI GEREKEN ORNEKLER:\n"
                for sample in failed_samples:
                    issues_joined = ", ".join(sample['quality_result']['issues'])
                    summary += f"{sample['patient_id']}: {issues_joined}\n"

            summary += f"\n{'='*80}\n\n"
            self.result_text.insert(END, summary)

            # Detaylı raporlar
            for result in all_results:
                report = self.format_detailed_report(
                    result['patient_id'],
                    result['data'],
                    result['quality_result']
                )
                self.result_text.insert(END, report)

        # İptal butonu pasifleştir
        self.cancel_button.config(state='disabled')
        self.result_text.see("1.0")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = NGSQualityReport()
    app.run()
