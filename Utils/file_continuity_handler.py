import os
import re
import logging
import concurrent.futures
from PIL import Image, UnidentifiedImageError
from PIL.ExifTags import TAGS
import exifread

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

class FileContinuityChecker:
    def __init__(self, directory, progress_callback=None, status_callback=None):
        self.directory = directory
        self.progress_callback = progress_callback
        self.status_callback = status_callback

    def get_exif_data(self, image_path):
        try:
            image = Image.open(image_path)
            exif_data = image.tag_v2 if hasattr(image, 'tag_v2') else image._getexif()

            if not exif_data:
                return "Unknown Model", "Unknown Serial Number"

            exif = {TAGS.get(k, k): v for k, v in exif_data.items()}
            model = exif.get('Model', 'Unknown Model')
            serial_number = exif.get('BodySerialNumber', 'Unknown Serial Number')
            return model, serial_number
        except (UnidentifiedImageError, AttributeError, KeyError, IndexError, TypeError) as e:
            logging.error(f"Error reading EXIF data from {image_path}: {e}")
            return "Unknown Model", "Unknown Serial Number"

    def get_exif_data_raw(self, image_path):
        try:
            with open(image_path, 'rb') as f:
                tags = exifread.process_file(f)
                model = tags.get('Image Model', 'Unknown Model')
                serial_number = tags.get('EXIF BodySerialNumber', 'Unknown Serial Number')

                if 'Image Make' in tags and 'Sony' in tags['Image Make'].values:
                    model = tags.get('Image Model', 'Unknown Model')
                    serial_number = tags.get('MakerNote SerialNumber', 'Unknown Serial Number')

                if isinstance(model, exifread.classes.IfdTag):
                    model = model.printable
                if isinstance(serial_number, exifread.classes.IfdTag):
                    serial_number = serial_number.printable
                return model, serial_number
        except Exception as e:
            logging.error(f"Error reading EXIF data from {image_path}: {e}")
            return "Unknown Model", "Unknown Serial Number"

    def is_image_file(self, file):
        # Sprawdź, czy plik jest obrazem na podstawie rozszerzenia
        valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.raw', '.nef', '.cr2', '.arw', '.dng', '.heif']
        return os.path.splitext(file)[1].lower() in valid_extensions

    def process_file(self, file):
        if not self.is_image_file(file):
            return None  # Ignoruj pliki nie będące obrazami

        ext = os.path.splitext(file)[1].lower()
        if ext in ['.raw', '.nef', '.cr2', '.arw', '.dng', '.tiff']:
            model, serial_number = self.get_exif_data_raw(os.path.join(self.directory, file))
        else:
            model, serial_number = self.get_exif_data(os.path.join(self.directory, file))
        return (file, model, serial_number, ext)

    def check_continuity(self):
        files = [f for f in os.listdir(self.directory) if os.path.isfile(os.path.join(self.directory, f)) and self.is_image_file(f)]
        if not files:
            return "Nie znalazłem plików graficznych."

        total_files = len(files)
        files_info = {}

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {executor.submit(self.process_file, file): file for file in files}

            for i, future in enumerate(concurrent.futures.as_completed(futures)):
                result = future.result()
                if result is None:
                    continue  # Pomijamy pliki nie będące obrazami
                file, model, serial_number, ext = result
                key = (model, serial_number, ext)
                if key not in files_info:
                    files_info[key] = []
                files_info[key].append(file)

                if self.status_callback:
                    self.status_callback(f"Analizuję plik: {file}")
                if self.progress_callback:
                    self.progress_callback(int((i + 1) / total_files * 100))

        report = []
        for (model, serial_number, ext), file_list in files_info.items():
            if model == "Unknown Model" and serial_number == "Unknown Serial Number":
                file_prefix = re.match(r'(\D+)', file_list[0]).group(1)
                file_list = sorted(file_list, key=lambda x: int(re.search(r'(\d+)(?=\.\w+$)', x).group(1)))
                first_file = file_list[0]
                last_file = file_list[-1]
                missing_files = []
                for i in range(len(file_list) - 1):
                    current_num = int(re.search(r'(\d+)(?=\.\w+$)', file_list[i]).group(1))
                    next_num = int(re.search(r'(\d+)(?=\.\w+$)', file_list[i + 1]).group(1))
                    if next_num != current_num + 1:
                        missing_files.extend(range(current_num + 1, next_num))
                if missing_files:
                    report.append(f"Pierwszy sprawdzany plik: {first_file} --> ostatni sprawdzany plik {last_file} ==== brakuje plików: {self.format_missing_files(missing_files)}")
                else:
                    report.append(f"Pierwszy sprawdzany plik: {first_file} --> ostatni sprawdzany plik {last_file} ==== nie brakuje żadnych plików")
            else:
                report.append(f"Sprawdzam pliki z urządzenia \"{model}\" o numerze seryjnym \"{serial_number}\":")
                if len(file_list) == 1:
                    report.append(f" dostępne jedno zdjęcie o nazwie {file_list[0]}")
                    continue

                file_list.sort(key=lambda x: int(re.search(r'(\d+)(?=\.\w+$)', x).group(1)))
                first_file = file_list[0]
                last_file = file_list[-1]
                missing_files = []
                for i in range(len(file_list) - 1):
                    current_number = int(re.search(r'(\d+)(?=\.\w+$)', file_list[i]).group(1))
                    next_number = int(re.search(r'(\d+)(?=\.\w+$)', file_list[i + 1]).group(1))
                    if next_number != current_number + 1:
                        missing_files.extend(range(current_number + 1, next_number))

                if missing_files:
                    report.append(f" Pierwszy sprawdzany plik: {first_file} --> ostatni sprawdzany plik {last_file} ==== brakuje plików: {self.format_missing_files(missing_files)}")
                else:
                    report.append(f" Pierwszy sprawdzany plik: {first_file} --> ostatni sprawdzany plik {last_file} ==== nie brakuje żadnych plików")

        return '\n'.join(report)

    def format_missing_files(self, missing_files):
        if not missing_files:
            return "brak"
        ranges = []
        start = missing_files[0]
        end = missing_files[0]

        for number in missing_files[1:]:
            if number == end + 1:
                end = number
            else:
                if end == start:
                    ranges.append(f"{start:04d}")
                elif end == start + 1:
                    ranges.append(f"{start:04d}")
                    ranges.append(f"{end:04d}")
                else:
                    ranges.append(f"{start:04d}-{end:04d}")
                start = number
                end = number

        if end == start:
            ranges.append(f"{start:04d}")
        elif end == start + 1:
            ranges.append(f"{start:04d}")
            ranges.append(f"{end:04d}")
        else:
            ranges.append(f"od {start:04d} do {end:04d}")

        return ', '.join(ranges)
