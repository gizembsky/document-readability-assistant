# Belge Okunabilirlik Yardımcısı

Tek sayfalık basılı Türkçe belgeler için Streamlit, OpenCV ve EasyOCR uygulaması.

## Çalıştırma

Python 3.12 önerilir.

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/streamlit run app.py --server.address 0.0.0.0
```

EasyOCR ilk OCR isteğinde Türkçe/İngilizce modellerini indirir (GitHub release sunucularına erişim gerekir), sonraki çalıştırmalarda depo içindeki `.easyocr/` önbelleğini kullanır. CPU üzerinde OCR zaman alabilir. Fotoğraflar sunucuda bellekte işlenir; uygulama fotoğraf veya metin dosyalarını diske kaydetmez. Paylaşılan sunucuda hassas belgeler için uygun erişim denetimi kurun. Seslendirme cihazın tarayıcı seslerini kullanır.

## Kullanım

JPG/PNG yükleyin, yeşil belge sınırını kontrol edin. Gerekirse dört köşenin X/Y koordinatlarını ayarlayın (ölçüler önizlemede belirtilir). Perspektif ve gölge/kontrast düzeltmesi otomatik uygulanır. Metni çıkar düğmesi her iki görüntüde OCR çalıştırır. Çıkan metni düzenleyebilir, büyütebilir, açık/koyu görünümde okuyabilir ve seslendirebilirsiniz. PNG ve UTF-8 metin indirilebilir.

Doğru referans metni girerek orijinal ve işlenmiş görüntülerin karakter/kelime hata oranlarını karşılaştırın. Ölçüm ham OCR sonuçlarını kullanır. Türkçe küçük harf ve boşluk normalizasyonu uygulanır; noktalama korunur. Düşük hata oranı daha iyidir; iyileşme garantisi yoktur.

## Kontroller ve sınırlar

```bash
.venv/bin/python -m pytest -q
```

Görüntüler en fazla 15 MB / 25 MP olabilir ve işleme için uzun kenarı 2000 piksele küçültülür. Bulanıklık eşiği sezgiseldir; belge içeriği ve ölçekten etkilenir. El yazısı, karmaşık tablolar, çok sayfalı belgeler kapsam dışıdır. Kaybolmuş harfler geri oluşturulmaz. Otomatik köşeler kullanıcı tarafından kontrol edilmelidir. Türkçe ses bulunması cihazın ses paketlerine bağlıdır.

Doğrulanan ortamın kesin paket sürümleri `requirements.lock.txt` dosyasındadır; aynı Linux/Python 3.12 ortamında tekrar kurulum için `pip install -r requirements.lock.txt` kullanılabilir. Varsayılan PyTorch dağıtımı GPU bağımlılıklarını da yükleyebilir; uygulama CPU kullanır.

Gerçek model indirme ve Türkçe OCR duman testi (Linux DejaVu Sans yazı tipi gerekir):

```bash
.venv/bin/python scripts/smoke_ocr.py
```
