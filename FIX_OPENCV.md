# OpenCV GUI Hiba Javítása

## A probléma
Az OpenCV-nek nincs GUI támogatása (cv2.namedWindow nem működik).

## Megoldások

### 1. Opció: OpenCV újratelepítése (AJÁNLOTT)

```bash
# Távolítsd el a jelenlegi OpenCV-t
pip uninstall opencv-python opencv-python-headless

# Telepítsd a teljes GUI támogatással rendelkező verziót
pip install opencv-contrib-python
```

### 2. Opció: Ha az 1. opció nem működik

```bash
pip uninstall opencv-python opencv-python-headless opencv-contrib-python
pip install opencv-python==4.8.1.78
```

### 3. Opció: Alternatív megoldás PyQt5-tel

Ha továbbra sem működik, telepítsd a PyQt5-öt:

```bash
pip install PyQt5
```

## Tesztelés

A javítás után futtasd ezt a tesztet:

```bash
python utils/region_selector.py
```

Ha működik, látnod kell egy screenshot ablakot, ahol ki tudsz jelölni egy területet.
