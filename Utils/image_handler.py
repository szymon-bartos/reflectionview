from PIL import Image, ExifTags, UnidentifiedImageError
import rawpy
import os
import io
from PIL.ImageQt import ImageQt
from PyQt5.QtGui import QPixmap, QImage

def load_image(image_path):
    """
    Ładuje obraz z podanej ścieżki i zwraca go jako obiekt Image z biblioteki PIL.

    :param image_path: Ścieżka do pliku graficznego.
    :return: Obiekt Image z biblioteki PIL.
    """
    extension = os.path.splitext(image_path)[1].lower()

    if extension in ['.arw', '.nef', '.cr2', '.dng', '.raw', '.tiff']:
        with rawpy.imread(image_path) as raw:
            try:
                # Pobieranie miniatury
                thumbnail = raw.extract_thumb()
                if thumbnail.format == rawpy.ThumbFormat.JPEG:
                    image = Image.open(io.BytesIO(thumbnail.data))
                else:
                    image = Image.fromarray(thumbnail.data)
                return image
            except rawpy._rawpy.LibRawNoThumbnailError:
                # Jeżeli nie ma miniatury, przetwarzamy pełny obraz
                rgb_image = raw.postprocess()
                return Image.fromarray(rgb_image)
    else:
        return Image.open(image_path)

def get_image_with_orientation(image_path):
    """
    Ładuje obraz i uwzględnia orientację EXIF.

    :param image_path: Ścieżka do pliku graficznego.
    :return: Obiekt Image z uwzględnioną orientacją.
    """
    image = load_image(image_path)
    try:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        exif = image._getexif()
        if exif is not None:
            exif = dict(exif.items())
            orientation = exif.get(orientation, None)

            if orientation == 3:
                image = image.rotate(180, expand=True)
            elif orientation == 6:
                image = image.rotate(270, expand=True)
            elif orientation == 8:
                image = image.rotate(90, expand=True)
    except (AttributeError, KeyError, IndexError):
        pass

    return image

def rotate_image(image, angle):
    """
    Obraca obraz o podany kąt.

    :param image: Obiekt Image z biblioteki PIL.
    :param angle: Kąt obrotu w stopniach.
    :return: Obrócony obiekt Image.
    """
    return image.rotate(angle, expand=True)

def resize_image(image_path, new_size):
    """
    Zmienia rozmiar obrazu do podanych wymiarów i zapisuje wynik.

    :param image_path: Ścieżka do pliku graficznego.
    :param new_size: Nowe wymiary (szerokość, wysokość).
    """
    image = Image.open(image_path)
    resized_image = image.resize(new_size)
    resized_image.save(image_path)

def load_image_thumbnail(image_path, size=(100, 100)):
    """
    Ładuje obraz z podanej ścieżki i zwraca jego miniaturę jako obiekt QPixmap.

    :param image_path: Ścieżka do pliku graficznego.
    :param size: Rozmiar miniatury (domyślnie 100x100 pikseli).
    :return: Miniatura obrazu jako obiekt QPixmap.
    """

    # Pobierz rozszerzenie pliku
    extension = os.path.splitext(image_path)[1].lower()

    if extension in ['.arw', '.nef', '.cr2', '.dng', '.raw', '.tiff']:  # Obsługiwane formaty plików RAW
        # Otwórz plik RAW za pomocą rawpy
        with rawpy.imread(image_path) as raw:
            try:
                # Pobieranie miniatury
                thumbnail = raw.extract_thumb()
                if thumbnail.format == rawpy.ThumbFormat.JPEG:
                    image = Image.open(io.BytesIO(thumbnail.data))
                else:
                    image = Image.fromarray(thumbnail.data)
            except rawpy._rawpy.LibRawNoThumbnailError:
                # Jeżeli nie ma miniatury, przetwarzamy pełny obraz
                rgb_image = raw.postprocess()
                image = Image.fromarray(rgb_image)
    else:
        # Otwórz plik za pomocą biblioteki Pillow
        image = Image.open(image_path)

    # Utwórz miniaturę
    image.thumbnail(size)
    qt_image = ImageQt(image)
    return QPixmap.fromImage(qt_image)
