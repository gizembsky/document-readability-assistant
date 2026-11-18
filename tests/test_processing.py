import cv2
import numpy as np
import pytest
from processing import detect_document, rectify, enhance, error_rate


def test_document_pipeline():
    image = np.zeros((500, 500, 3), dtype=np.uint8)
    cv2.fillConvexPoly(image, np.int32([[70,40],[440,70],[400,460],[40,420]]), (240,240,240))
    cv2.putText(image, 'TEST', (100,250), cv2.FONT_HERSHEY_SIMPLEX, 2, (30,30,30), 3)
    corners = detect_document(image)
    assert corners is not None
    fixed = rectify(image, corners)
    assert fixed.shape[0] > 300 and fixed.shape[1] > 300
    result = enhance(fixed)
    assert result.ndim == 2 and result.dtype == np.uint8
    assert result.std() > 10


def test_invalid_corners():
    with pytest.raises(ValueError):
        rectify(np.zeros((100,100,3), dtype=np.uint8), [[0,0]]*4)


def test_metrics():
    assert error_rate('İYİ  BİR', 'iyi bir') == 0
    assert error_rate('abc', 'axc') == pytest.approx(1/3)
    assert error_rate('bir iki', 'bir üç', True) == .5
    with pytest.raises(ValueError):
        error_rate('', 'abc')
