import cv2
import numpy as np
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib  # Do zapisu i wczytania modelu

# Funkcja używana do wykrycia cech na zdjęciach
def extract_features(image):
    image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    laplacian_var = cv2.Laplacian(image_gray, cv2.CV_64F).var()
    gradient_x = cv2.Sobel(image_gray, cv2.CV_64F, 1, 0, ksize=5)
    gradient_y = cv2.Sobel(image_gray, cv2.CV_64F, 0, 1, ksize=5)
    gradient_magnitude = np.sqrt(gradient_x ** 2 + gradient_y ** 2)
    gradient_mean = np.mean(gradient_magnitude)
    edges = cv2.Canny(image_gray, 100, 200)
    edge_hist = np.sum(edges) / (image_gray.shape[0] * image_gray.shape[1])
    return [laplacian_var, gradient_mean, edge_hist]

# Ścieżki do folderów z ostrymi i nieostrymi zdjęciami
sharp_images_dir = "D:/MAGISTERKA - TEST/szybki test - podzial/sharp"
blurry_images_dir = "D:/MAGISTERKA - TEST/szybki test - podzial/blur"

features = []
labels = []

# Ekstrakcja cech dla ostrych obrazów
for filename in os.listdir(sharp_images_dir):
    image_path = os.path.join(sharp_images_dir, filename)
    image = cv2.imread(image_path)
    if image is not None:
        features.append(extract_features(image))
        labels.append(0)  # 0 oznacza ostre

# Ekstrakcja cech dla rozmytych obrazów
for filename in os.listdir(blurry_images_dir):
    image_path = os.path.join(blurry_images_dir, filename)
    image = cv2.imread(image_path)
    if image is not None:
        features.append(extract_features(image))
        labels.append(1)  # 1 oznacza rozmyte

# Podział danych na zestaw treningowy i testowy
X_train, X_test, y_train, y_test = train_test_split(features, labels, test_size=0.2, random_state=42)

# Trening klasyfikatora
clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, y_train)

# Ocena modelu
y_pred = clf.predict(X_test)
print(f"Dokładność modelu: {accuracy_score(y_test, y_pred) * 100:.2f}%")

# Zapisanie modelu
joblib.dump(clf, 'sharpness_classifier.pkl')
