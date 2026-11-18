from streamlit.testing.v1 import AppTest


def test_upload_screen():
    app = AppTest.from_file('../app.py').run()
    assert not app.exception
    assert app.title[0].value == '📄 Belge Okunabilirlik Yardımcısı'


def test_uploaded_document():
    import io
    from unittest.mock import patch
    from PIL import Image, ImageDraw
    image = Image.new('RGB', (600, 800), 'white')
    ImageDraw.Draw(image).text((50, 100), 'Belge testi', fill='black')
    upload = io.BytesIO()
    image.save(upload, format='PNG')
    upload.size = upload.tell()
    upload.seek(0)
    with patch('streamlit.file_uploader', return_value=upload):
        app = AppTest.from_file('../app.py').run()
        assert not app.exception
        assert [x.value for x in app.subheader] == ['Orijinal belge', 'İyileştirilmiş belge', 'Çıkarılan metin']
        assert len(app.number_input) == 8
