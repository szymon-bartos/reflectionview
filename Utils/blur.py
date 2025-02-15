import cv2
import numpy as np
import os
import joblib
import logging

# Załaduj wytrenowany model
clf = joblib.load(r'Utils\sharpness_classifier.pkl')


class BlurInspector:
    def __init__(self, directory, batch_size=10):
        self.directory = directory
        self.blurred_images = []
        self.batch_size = batch_size  # Wielkość partii przetwarzania zdjęć

    def extract_features(self, image):
        try:
            image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            laplacian_var = cv2.Laplacian(image_gray, cv2.CV_64F).var()
            gradient_x = cv2.Sobel(image_gray, cv2.CV_64F, 1, 0, ksize=5)
            gradient_y = cv2.Sobel(image_gray, cv2.CV_64F, 0, 1, ksize=5)
            gradient_magnitude = np.sqrt(gradient_x ** 2 + gradient_y ** 2)
            gradient_mean = np.mean(gradient_magnitude)
            edges = cv2.Canny(image_gray, 100, 200)
            edge_hist = np.sum(edges) / (image_gray.shape[0] * image_gray.shape[1])
            return [laplacian_var, gradient_mean, edge_hist]
        except Exception as e:
            logging.error(f"Błąd podczas wyodrębniania cech obrazu: {e}")
            return None

    def is_blurred(self, image_path):
        try:
            image = cv2.imread(image_path)
            if image is None:
                logging.warning(f"Nie udało się wczytać obrazu: {image_path}")
                return False

            features = self.extract_features(image)
            if features is None:
                return False

            prediction = clf.predict([features])
            return prediction[0] == 1  # 1 oznacza rozmyte
        except Exception as e:
            logging.error(f"Błąd podczas analizy obrazu {image_path}: {e}")
            return False

    def analyze_directory(self):
        try:
            self.blurred_images = []

            # Lista plików w folderze
            image_files = [
                f for f in os.listdir(self.directory)
                if os.path.isfile(os.path.join(self.directory, f)) and
                f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.arw', '.nef', '.cr2', '.dng', '.raw'))
            ]

            if not image_files:
                logging.info("Brak zdjęć do analizy w folderze.")
                return self.blurred_images

            logging.info(f"Znaleziono {len(image_files)} zdjęć do analizy.")

            # Przetwarzanie wsadowe
            for i in range(0, len(image_files), self.batch_size):
                batch_files = image_files[i:i + self.batch_size]
                for file_name in batch_files:
                    file_path = os.path.join(self.directory, file_name)
                    if self.is_blurred(file_path):
                        self.blurred_images.append(file_name)

                logging.info(f"Przetworzono {min(i + self.batch_size, len(image_files))}/{len(image_files)} zdjęć.")

            return self.blurred_images
        except Exception as e:
            logging.error(f"Błąd podczas analizy katalogu: {e}")
            return []

# Testowanie funkcji
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Wprowadź ścieżkę do katalogu, który chcesz przeanalizować
    folder_to_analyze = "D:/MAGISTERKA - TEST/szybki test - podzial"

    inspector = BlurInspector(folder_to_analyze, batch_size=10)
    blurred_images = inspector.analyze_directory()

    if blurred_images:
        logging.info("Nieostre zdjęcia: ")
        for img in blurred_images:
            logging.info(img)
    else:
        logging.info("Wszystkie zdjęcia są ostre.")
