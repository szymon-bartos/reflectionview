import rawpy
from PIL import Image
import os


def load_image(file_path):
    """
    Ładuje obraz z podanej ścieżki do pliku. Obsługuje formaty RAW, JPEG, PNG i GIF.

    :param file_path: Ścieżka do pliku graficznego.
    :return: Obiekt Image z biblioteki PIL.
    """
    # Sprawdzenie, czy plik istnieje
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Plik nie istnieje: {file_path}")

    # Sprawdzenie uprawnień do pliku
    if not os.access(file_path, os.R_OK):
        raise PermissionError(f"Brak uprawnień do odczytu pliku: {file_path}")

    # Pobierz rozszerzenie pliku i zamień na małe litery
    extension = os.path.splitext(file_path)[1].lower()

    # Sprawdź, czy rozszerzenie jest jednym z obsługiwanych formatów RAW
    if extension in ['.raw', '.nef', '.cr2', '.arw', '.dng', '.tiff']:  # Popularne rozszerzenia plików RAW
        return load_raw_image(file_path)
    else:
        # Otwórz plik za pomocą biblioteki Pillow
        return Image.open(file_path)

    # Odczytaj dane EXIF
    exif_data = get_exif_data(file_path)



def load_raw_image(file_path):
    """
    Ładuje i przetwarza plik obrazu RAW.

    :param file_path: Ścieżka do pliku obrazu RAW.
    :return: Obiekt Image z biblioteki PIL.
    """
    # Dodaj debugowanie
    print(f"Próba otwarcia pliku RAW: {file_path}")

    # Otwórz plik RAW za pomocą biblioteki rawpy
    try:
        raw = rawpy.imread(file_path)
    except rawpy._rawpy.LibRawIOError as e:
        print(f"Błąd podczas otwierania pliku RAW: {e}")
        raise

    # Przetwórz obraz do formatu RGB
    rgb_image = raw.postprocess()

    # Konwertuj przetworzony obraz na obiekt Image z Pillow
    return Image.fromarray(rgb_image)


def save_image(image, path):
    """
    Zapisuje obraz na podanej ścieżce.

    :param image: Obiekt Image z biblioteki PIL.
    :param path: Ścieżka do zapisania obrazu.
    """
    image.save(path)

# Przykład użycia
if __name__ == "__main__":
    # Podaj pełną ścieżkę do pliku
    image_path = 'D:/Studia/Magisterka - PJ/Praca magisterska/Aplikacja/ReflectionView_1.0/DSC05057.ARW'
    print(f"Próba ładowania obrazu: {image_path}")
    image = load_image(image_path)
    image.show()