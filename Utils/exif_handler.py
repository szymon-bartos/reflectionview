import exifread


def get_shutter_count(tags):
    """
    Próbuje odczytać wartość licznika migawki z danych EXIF.

    :param tags: Słownik z tagami EXIF.
    :return: Wartość licznika migawki lub 'Not Available' jeśli nie znaleziono.
    """
    # Specyficzne tagi dla różnych marek aparatów
    shutter_count_tags = {
        'Canon': ['MakerNote ShutterCount', 'MakerNote Tag 0x0093', 'MakerNote Tag 0x0095'],
        'Nikon': ['MakerNote ShutterCount', 'MakerNote Tag 0x00a7', 'MakerNote TotalShutterReleases'],
        'Sony': ['MakerNote ShutterCount', 'MakerNote Tag 0x9404', 'MakerNote Tag 0x9405'],
        'Fujifilm': ['MakerNote ShutterCount', 'MakerNote Tag 0x00b4'],
        'Panasonic': ['MakerNote ShutterCount'],
        'Olympus': ['MakerNote ShutterCount'],
        'Leica': ['MakerNote ShutterCount'],
        'Pentax': ['MakerNote ShutterCount'],
        'Sigma': ['MakerNote ShutterCount'],
        'Hasselblad': ['MakerNote ShutterCount'],
        'Ricoh': ['MakerNote ShutterCount'],
        'Casio': ['MakerNote ShutterCount'],
        'Kodak': ['MakerNote ShutterCount'],
        'Samsung': ['MakerNote ShutterCount'],
        'GoPro': ['MakerNote ShutterCount'],
        'DJI': ['MakerNote ShutterCount'],
    }

    # Próba odczytu liczników migawki dla różnych marek
    for brand, tags_list in shutter_count_tags.items():
        for tag in tags_list:
            if tag in tags:
                return str(tags[tag])

    # Ogólne tagi dla liczników migawki, jeśli specyficzne tagi nie zostały znalezione
    generic_tags = [
        'EXIF ShutterCount',  # Najczęstszy tag dla liczników migawki
        'Image ImageNumber',  # Alternatywny tag dla liczników migawki
    ]

    for tag in generic_tags:
        if tag in tags:
            return str(tags[tag])

    return 'Not Available'


def get_exif_data(image_path):
    """
    Odczytuje dane EXIF z podanego pliku obrazu.

    :param image_path: Ścieżka do pliku obrazu.
    :return: Słownik z danymi EXIF.
    """
    with open(image_path, 'rb') as image_file:
        tags = exifread.process_file(image_file)

    exif_data = {tag: str(tags[tag]) for tag in tags}

    # Dodaj odczytanie przebiegu migawki
    shutter_count = get_shutter_count(tags)
    exif_data = {'Shutter Count': shutter_count, **exif_data}  # Umieść Shutter Count na początku

    return exif_data


def extract_camera_model(tags):
    """
    Odczytuje model aparatu z danych EXIF.

    :param tags: Słownik z tagami EXIF.
    :return: Model aparatu lub None, jeśli nie znaleziono.
    """
    camera_model_tags = ['Image Model', 'EXIF LensModel']

    for tag in camera_model_tags:
        if tag in tags:
            return str(tags[tag])

    return None


def extract_lens_model(tags):
    """
    Odczytuje model obiektywu z danych EXIF.

    :param tags: Słownik z tagami EXIF.
    :return: Model obiektywu lub None, jeśli nie znaleziono.
    """
    lens_model_tags = ['EXIF LensModel', 'MakerNote LensModel']

    for tag in lens_model_tags:
        if tag in tags:
            return str(tags[tag])

    return None
