import hashlib
import io
import json
import cv2
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError
import streamlit as st
import streamlit.components.v1 as components
from processing import detect_document, rectify, enhance, blur_score, error_rate

st.set_page_config(page_title='Belge Okunabilirlik Yardımcısı', page_icon='📄', layout='wide')
st.title('📄 Belge Okunabilirlik Yardımcısı')
st.caption('Tek sayfalık basılı Türkçe belgeler • Düzelt, oku, dinle')
st.info('Fotoğraflar uygulama sunucusunda işlenir; harici OCR hizmetine gönderilmez. El yazısı ve karmaşık tablolar ilk sürümün kapsamı dışındadır.')

@st.cache_resource
def reader():
    import easyocr
    return easyocr.Reader(['tr', 'en'], gpu=False, model_storage_directory='.easyocr', user_network_directory='.easyocr/user_network')


def png(image):
    buf = io.BytesIO()
    Image.fromarray(image).save(buf, format='PNG')
    return buf.getvalue()

upload = st.file_uploader('JPG veya PNG belge fotoğrafı yükle (en fazla 15 MB)', type=['jpg', 'jpeg', 'png'])
if upload is None:
    st.stop()
if upload.size > 15 * 1024**2:
    st.error('Lütfen 15 MB altında bir fotoğraf yükleyin.')
    st.stop()
try:
    source = Image.open(upload)
    if source.format not in ('JPEG', 'PNG') or source.width * source.height > 25_000_000:
        raise ValueError('JPG/PNG ve en fazla 25 megapiksel kullanın.')
    source = ImageOps.exif_transpose(source).convert('RGB')
    source.thumbnail((2000, 2000))
    image = np.array(source)
except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
    st.error(f'Görüntü açılamadı: {exc}')
    st.stop()
identity = hashlib.sha256(upload.getvalue()).hexdigest()
if st.session_state.get('document') != identity:
    st.session_state.clear()
    st.session_state.document = identity
score = blur_score(image)
if score < 80:
    st.warning('Fotoğraf bulanık veya az ayrıntılı olabilir. Daha iyi ışıkta, kamerayı sabit tutarak yeniden çekin. Kaybolan harfler geri getirilemez. Bu kontrol yaklaşık bir göstergedir.')
points = detect_document(image)
manual = st.checkbox('Dört köşeyi elle ayarla', value=points is None)
h, w = image.shape[:2]
if manual:
    st.caption('Önizlemedeki koordinatlara göre dört köşeyi ayarlayın. Otomatik sınır yanlışsa da bu seçeneği kullanabilirsiniz.')
    defaults = points if points is not None else np.float32([[0,0],[w-1,0],[w-1,h-1],[0,h-1]])
    selected = []
    for i, col in enumerate(st.columns(4)):
        with col:
            st.write(['Sol üst', 'Sağ üst', 'Sağ alt', 'Sol alt'][i])
            x = st.number_input('X', 0, w-1, int(defaults[i][0]), key=f'x{i}')
            y = st.number_input('Y', 0, h-1, int(defaults[i][1]), key=f'y{i}')
            selected.append([x,y])
    points = np.float32(selected)
if points is None:
    st.warning('Belge sınırları bulunamadı. Dört köşeyi elle ayarlayın.')
    st.stop()
try:
    corrected = rectify(image, points)
    improved = enhance(corrected)
except ValueError as exc:
    st.error(str(exc))
    st.stop()
version = hashlib.sha256(improved.tobytes()).hexdigest()
if st.session_state.get('version') != version:
    for key in ('ocr_original', 'ocr_processed', 'edited'):
        st.session_state.pop(key, None)
    st.session_state.version = version
marked = image.copy()
cv2.polylines(marked, [points.astype(np.int32)], True, (0, 180, 110), 4)
a, b, c = st.columns(3)
with a:
    st.subheader('Orijinal belge')
    st.image(marked, caption=f'Yeşil çizgi: seçilen sınır · {w} × {h} piksel')
with b:
    st.subheader('İyileştirilmiş belge')
    st.image(improved)
    st.download_button('Görüntüyü indir', png(improved), 'iyilestirilmis.png', 'image/png')
with c:
    st.subheader('Çıkarılan metin')
    if st.button('Metni çıkar', type='primary'):
        try:
            with st.spinner('Türkçe OCR çalışıyor. İlk kullanımda modeller indirilir…'):
                engine = reader()
                original = '\n'.join(engine.readtext(image, detail=0, paragraph=True))
                processed = '\n'.join(engine.readtext(improved, detail=0, paragraph=True))
                st.session_state.update(ocr_original=original, ocr_processed=processed, edited=processed)
        except Exception:
            st.error('OCR başlatılamadı. EasyOCR bağımlılıklarını ve ilk model indirmesi için ağ erişimini kontrol edin; yeniden deneyebilirsiniz.')
    if 'edited' in st.session_state:
        text = st.text_area('Metni kontrol edip düzeltebilirsiniz', key='edited', height=300)
        if not text.strip():
            st.warning('Metin bulunamadı. Köşeleri ve fotoğraf kalitesini kontrol edin.')
        st.download_button('Metni indir', text, 'belge.txt', 'text/plain; charset=utf-8')
        size = st.slider('Okuma yazı boyutu', 16, 40, 24)
        dark = st.toggle('Koyu okuma görünümü')
        import html
        st.markdown(f'<div style="font-size:{size}px;background:{"#18202c" if dark else "#fff"};color:{"#fff" if dark else "#18202c"};padding:20px;white-space:pre-wrap">{html.escape(text)}</div>', unsafe_allow_html=True)
        payload = json.dumps(text).replace('<', '\\u003c')
        components.html('''<button id="play">Sesli oku</button> <button id="stop">Durdur</button><p id="status"></p><script>
const text = ''' + payload + ''';
const status = document.getElementById('status');
document.getElementById('play').onclick=()=>{
 if (!('speechSynthesis' in window)) {status.textContent='Tarayıcı seslendirmeyi desteklemiyor.';return;}
 speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(text);u.lang='tr-TR';
 const voice=speechSynthesis.getVoices().find(v=>v.lang.startsWith('tr'));
 if(voice)u.voice=voice; else status.textContent='Türkçe ses bulunamadı; cihazın varsayılan sesi kullanılacak.';
 speechSynthesis.speak(u);};
document.getElementById('stop').onclick=()=>speechSynthesis.cancel();
window.addEventListener('pagehide',()=>speechSynthesis.cancel());</script>''', height=100)
        st.caption('Seslendirme tarayıcı/işletim sistemi seslerini kullanır; çevrimdışı çalışma ses sağlayıcısına bağlıdır.')
if 'ocr_processed' in st.session_state:
    with st.expander('OCR doğruluğunu karşılaştır'):
        st.write('Aynı doğru metne karşı ham OCR sonuçları ölçülür; elle düzeltilen metin ölçüme katılmaz. Küçük harfe çevirme ve boşluk normalizasyonu uygulanır. Düşük oran daha iyidir.')
        st.text_area('Orijinal görüntünün OCR sonucu', st.session_state.ocr_original, disabled=True)
        reference = st.text_area('Doğru metin (elle yazılmış referans)')
        if reference.strip():
            rows = []
            for label, result in [('Orijinal', st.session_state.ocr_original), ('İşlenmiş', st.session_state.ocr_processed)]:
                rows.append({'Görüntü': label, 'Karakter hata oranı (CER)': error_rate(reference, result), 'Kelime hata oranı (WER)': error_rate(reference, result, True)})
            st.dataframe(rows, hide_index=True)
            st.caption('Eklenen karakter/kelimeler nedeniyle hata oranı %100’ü aşabilir. İyileştirme her belgede OCR doğruluğunu artırmayabilir.')
