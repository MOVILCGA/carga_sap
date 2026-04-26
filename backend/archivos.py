import os
from werkzeug.utils import secure_filename


def guardar_archivo(file, folder="uploads"):
    if not file or file.filename == "":
        return None

    nombre = secure_filename(file.filename)
    ruta = os.path.join(folder, nombre)

    file.save(ruta)
    return ruta