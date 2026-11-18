"""Document geometry, enhancement and reproducible OCR evaluation."""
import cv2
import numpy as np


def order_points(points):
    p = np.asarray(points, dtype=np.float32)
    if p.shape != (4, 2) or not np.isfinite(p).all():
        raise ValueError('Dört geçerli köşe seçin.')
    hull = cv2.convexHull(p).reshape(-1, 2)
    if len(hull) != 4 or cv2.contourArea(hull) < 100:
        raise ValueError('Köşeler farklı olmalı ve bir dörtgen oluşturmalı.')
    # Convex hull is cyclic; rotate to top-left, then orient clockwise.
    hull = np.roll(hull, -np.argmin(hull.sum(axis=1)), axis=0)
    u, v = hull[1]-hull[0], hull[2]-hull[1]
    if u[0]*v[1] - u[1]*v[0] < 0:
        hull = hull[[0, 3, 2, 1]]
    return hull


def detect_document(image):
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(cv2.GaussianBlur(gray, (5, 5), 0), 40, 120)
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    for contour in sorted(contours, key=cv2.contourArea, reverse=True):
        if cv2.contourArea(contour) < gray.size * .15:
            continue
        poly = cv2.approxPolyDP(contour, .02 * cv2.arcLength(contour, True), True)
        if len(poly) == 4 and cv2.isContourConvex(poly):
            return order_points(poly.reshape(4, 2))
    return None


def rectify(image, points):
    p = order_points(points)
    h, w = image.shape[:2]
    if (p[:, 0] < 0).any() or (p[:, 0] >= w).any() or (p[:, 1] < 0).any() or (p[:, 1] >= h).any():
        raise ValueError('Köşeler görüntü içinde olmalı.')
    width = int(max(np.linalg.norm(p[1]-p[0]), np.linalg.norm(p[2]-p[3])))
    height = int(max(np.linalg.norm(p[3]-p[0]), np.linalg.norm(p[2]-p[1])))
    target = np.float32([[0, 0], [width-1, 0], [width-1, height-1], [0, height-1]])
    return cv2.warpPerspective(image, cv2.getPerspectiveTransform(p, target), (width, height))


def enhance(image):
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    background = cv2.GaussianBlur(gray, (0, 0), 25)
    normalized = cv2.divide(gray, np.maximum(background, 1), scale=220)
    clean = cv2.fastNlMeansDenoising(normalized, h=7)
    return cv2.createCLAHE(clipLimit=2, tileGridSize=(8, 8)).apply(clean)


def blur_score(image):
    return float(cv2.Laplacian(cv2.cvtColor(image, cv2.COLOR_RGB2GRAY), cv2.CV_64F).var())


def error_rate(reference, prediction, words=False):
    # Same normalization for both images; Turkish lowercase handles dotted I.
    def normalize(s):
        return ' '.join(s.replace('I', 'ı').replace('İ', 'i').lower().split())
    a, b = normalize(reference), normalize(prediction)
    if words:
        a, b = a.split(), b.split()
    if not a:
        raise ValueError('Doğru metin boş olamaz.')
    row = list(range(len(b)+1))
    for i, x in enumerate(a, 1):
        nxt = [i]
        for j, y in enumerate(b, 1):
            nxt.append(min(nxt[-1]+1, row[j]+1, row[j-1]+(x != y)))
        row = nxt
    return row[-1] / len(a)
