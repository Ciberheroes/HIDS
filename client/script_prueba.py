import os
import random
import string

directorio = "file_system"

extensiones = [".txt", ".csv", ".java", ".html", ".json", ".xml", ".jpg", ".png"]

def generar_contenido(extension):
    if extension == ".jpg" or extension == ".png":
        return ''.join(random.choices(string.ascii_letters + string.digits, k=1000))
    return ''.join(random.choices(string.ascii_letters + string.digits, k=100))

if not os.path.exists(directorio):
    os.makedirs(directorio)

for i in range(100):
    extension = random.choice(extensiones)
    nombre_archivo = f"file_{i+1}{extension}"
    ruta_archivo = os.path.join(directorio, nombre_archivo)
    if random.random() < 0.3:  # 30% de probabilidad de crear una carpeta nueva
        carpeta_nueva = f"folder_{random.randint(1, 10)}"
        ruta_archivo = os.path.join(directorio, carpeta_nueva, nombre_archivo)
        if not os.path.exists(os.path.join(directorio, carpeta_nueva)):
            os.makedirs(os.path.join(directorio, carpeta_nueva))
    else:
        ruta_archivo = os.path.join(directorio, nombre_archivo)
    with open(ruta_archivo, "w") as archivo:
        contenido = generar_contenido(extension)
        archivo.write(contenido)

print("Files created successfully.")
