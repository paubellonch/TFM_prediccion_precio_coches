import os
import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
import tensorflow as tf
import sys
import tempfile
sys.path.append("/content/models/research")
sys.path.append("/content/models/research/slim")
sys.path.append("/content/models/research/object_detection")
import numpy as np
import tensorflow as tf
from models.research.object_detection.utils import label_map_util
from PIL import Image
import os
import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
import io
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from pydrive2.files import FileNotUploadedError

directorio_credenciales = '/Users/paubellonchmarchan/PycharmProjects/tfm_cars/credentials_module.json'
# INICIAR SESION
def login():
    # Establece la ruta por defecto para el archivo de configuración del cliente OAuth 2.0
    GoogleAuth.DEFAULT_SETTINGS['client_config_file'] = directorio_credenciales

    # Inicializa el objeto de autenticación GoogleAuth
    gauth = GoogleAuth()

    # Carga las credenciales del archivo especificado anteriormente
    gauth.LoadCredentialsFile(directorio_credenciales)

    # Si no hay credenciales disponibles, autentica usando un servidor web local
    if gauth.credentials is None:
        gauth.LocalWebserverAuth(port_numbers=[8092])
    # Si el token de acceso ha expirado, refresca las credenciales
    elif gauth.access_token_expired:
        gauth.Refresh()
    # Si el token de acceso aún es válido, autoriza las credenciales
    else:
        gauth.Authorize()

    # Guarda las credenciales actualizadas en el archivo de credenciales
    gauth.SaveCredentialsFile(directorio_credenciales)

    # Inicializa el objeto GoogleDrive con las credenciales autorizadas y lo retorna
    credenciales = GoogleDrive(gauth)
    return credenciales


# Configurar la conexión a la base de datos MongoDB
client = MongoClient(
    'mongodb+srv://paubellonch99:YSsMTs3NLtkDCkC5@cluster0.xdne2xq.mongodb.net/?retryWrites=true&w=majority')
db = client['autos']
data_preprocessing_autocasion =db['autos_todownload']

"""
# Crear una carpeta para almacenar las imágenes descargadas
carpeta_imagenes = '/Users/paubellonchmarchan/Desktop/TFM/CAR IMAGES'
if not os.path.exists(carpeta_imagenes):
    os.makedirs(carpeta_imagenes)
"""

# Ruta al modelo y etiquetas
MODEL_DIR = '/Users/paubellonchmarchan/PycharmProjects/tfm_cars/ssd_resnet50_v1_fpn_640x640_coco17_tpu-8/saved_model'
PATH_TO_LABELS = '/Users/paubellonchmarchan/PycharmProjects/tfm_cars/mscoco_label_map.pbtxt'
json_googledrive='/Users/paubellonchmarchan/PycharmProjects/tfm_cars/client_secret.json'

# Cargar el modelo de TensorFlow 2.x
model = tf.saved_model.load(MODEL_DIR)
print("modelo cargado")

# Cargar las etiquetas
label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=90, use_display_name=True)
category_index = label_map_util.create_category_index(categories)


# Función para descargar una imagen desde una URL
def descargar_imagen(url, nombre_archivo, carpeta_id_registro):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        print(f"Descargando imagen de URL: {url}")
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Lanza una excepción si la respuesta no es 200 OK
        prediccion = detect_car(response.content)
        print(prediccion)
        if prediccion:

            subir_imagen_a_drive(nombre_archivo, response.content, carpeta_id_registro)
            print(f"Imagen descargada: {nombre_archivo}")
        else:
            print(f"Imagen NO descargada: {nombre_archivo}")
    except requests.exceptions.RequestException as e:
        print(f"Error al descargar la imagen: {e}")
    except Exception as e:
        print(f"Error desconocido: {e}")


def detect_car(image_bytes):
    imagen_des = Image.open(io.BytesIO(image_bytes))
    image_np = np.array(imagen_des).astype(np.uint8)
    image_np_expanded = np.expand_dims(image_np, axis=0)
    input_tensor = tf.convert_to_tensor(image_np_expanded, dtype=tf.uint8)

    # Llamando al modelo para inferencia
    infer = model.signatures["serving_default"]
    detections = infer(input_tensor)

    boxes = np.squeeze(detections['detection_boxes'].numpy())
    scores = np.squeeze(detections['detection_scores'].numpy())
    classes = np.squeeze(detections['detection_classes'].numpy()).astype(np.int32)

    # Contando las detecciones de coches y edificios
    car_count = np.sum((classes == 3) & (scores > 0.5))
    building_detected = np.any((classes == 2) & (scores > 0.5))

    # Comprobar condiciones
    if car_count == 1 and not building_detected:
        return True  # Solo se detectó un coche y ningún edificio con confianza > 0.5
    else:
        return False  # Se detectaron múltiples coches o se detectó un edificio


# Obtener todos los registros de la colección y obtener el número aproximado de documentos
registros = list(data_preprocessing_autocasion.find())
num_documentos = len(registros)

def buscar_o_crear_carpeta(nombre_carpeta, id_folder_parent=None):
    credenciales = login()
    query = f"title='{nombre_carpeta}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if id_folder_parent:
        query += f" and '{id_folder_parent}' in parents"

    # Busca la carpeta en Google Drive
    carpeta_lista = credenciales.ListFile({'q': query}).GetList()

    # Si la carpeta ya existe, devuelve su ID
    if carpeta_lista:
        return carpeta_lista[0]['id'], True

    # Si no existe, crea la carpeta y devuelve su ID
    else:
        folder_metadata = {
            'title': nombre_carpeta,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if id_folder_parent:
            folder_metadata['parents'] = [{"kind": "drive#fileLink", "id": id_folder_parent}]
        folder = credenciales.CreateFile(folder_metadata)
        folder.Upload()
        return folder['id'], False

def subir_imagen_a_drive(nombre_archivo, contenido_imagen, id_carpeta_destino):
    credenciales = login()

    archivo = credenciales.CreateFile({
        'title': nombre_archivo,
        'parents': [{'id': id_carpeta_destino}]
    })

    # Guardar el contenido binario en un archivo temporal
    with tempfile.NamedTemporaryFile(delete=True) as temp:
        temp.write(contenido_imagen)
        temp.flush()

        # Establecer el contenido del archivo y subirlo
        archivo.SetContentFile(temp.name)
        archivo.Upload()

    return archivo['id']

carpeta_imagenes, valor = buscar_o_crear_carpeta("car_scrapping",'1VHIIsRij4zsGSoYTOtD9KyeqBFcwXHAB')
creada=True
for i, registro in enumerate(registros):
    imagenes = registro['imagenes']

    # Crear una subcarpeta en Google Drive para cada registro basada en el ObjectId
    id_registro = str(registro['_id'])
    carpeta_id_registro, creada= buscar_o_crear_carpeta(id_registro, carpeta_imagenes)

    print(f"Procesando registro {i + 1}/{num_documentos}")
    if creada == False:
        # Descargar y subir cada imagen
        for j, url_imagen in enumerate(imagenes):
            nombre_archivo = f"{id_registro}_{j + 1}.jpeg"
            print(f"Descargando imagen {j + 1}/{len(imagenes)}")
            contenido_imagen = descargar_imagen(url_imagen, nombre_archivo, carpeta_id_registro)

    else:
        print(f"Coche ya existe, no hace falta descargar")






"""
# Recorrer los registros y realizar el web scraping para descargar las imágenes
for i, registro in enumerate(registros):
    imagenes = registro['imagenes']

    # Crear una subcarpeta para cada registro basada en el ObjectId
    id_registro = registro['_id']
    carpeta_id_registro = os.path.join(carpeta_imagenes, str(id_registro))
    if not os.path.exists(carpeta_id_registro):
        os.makedirs(carpeta_id_registro)

    print(f"Procesando registro {i + 1}/{num_documentos}")

    # Descargar cada imagen utilizando web scraping
    for j, url_imagen in enumerate(imagenes):
        nombre_archivo = f"{id_registro}_{j + 1}.jpeg"
        print(f"Descargando imagen {j + 1}/{len(imagenes)}")
        descargar_imagen(url_imagen, os.path.join(carpeta_id_registro, nombre_archivo))

print("Descarga de imágenes completada.")
"""