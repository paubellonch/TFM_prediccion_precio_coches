from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time
import pymongo

import requests
from bs4 import BeautifulSoup


from PIL import Image
import numpy as np
import base64
from io import BytesIO
# Inicializar el controlador de Selenium (asegúrate de tener el controlador adecuado para tu navegador)
chrome_driver_path = '/Users/paubellonchmarchan/PycharmProjects/tfm_cars/driver/chromedriver_v3'
# Configurar las opciones del controlador de Chrome
chrome_options = Options()
# Para ejecución en segundo plano sin interfaz gráfica
#chrome_options.add_argument("--headless")
chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')


# Crear una conexión a la base de datos MongoDB
client = pymongo.MongoClient('mongodb+srv://paubellonch99:YSsMTs3NLtkDCkC5@cluster0.xdne2xq.mongodb.net/?retryWrites=true&w=majority')
db = client['autos']  # Nombre de la base de datos
data_preprocessing_autocasion = db['autos_todownload'] # Nombre de la colección

# Crear la instancia del controlador de Chrome
driver = webdriver.Chrome(service=Service(chrome_driver_path), options=chrome_options)
url = 'https://www.autocasion.com/coches-ocasion'
driver.get(url)
# Crear una lista para almacenar los datos de cada artículo
lista_articulos = []

pagina = 0
while True:
    print("Pagina " + str(pagina))
    pagina += 1
    # Esperar a que los resultados de búsqueda se carguen
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, '//*[@id="results-html"]/article')))

    # Obtener el contenido HTML de la página cargada
    html = driver.page_source

    # Crear objeto BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')

    # Utilizar select para seleccionar todos los elementos de los artículos
    articulos = soup.select('article.anuncio')
    cambios=0
    cambios=0
    for articulo in articulos:
        """
        if cambios==2:
            break
        cambios=1;
        """
        time.sleep(1)
        marca_modelo = articulo.select_one('h2[itemprop="name"]').text.strip()
        detalles = articulo.select('ul li')
        km = detalles[2].text.strip()
        año = detalles[1].text.strip()
        precio_element = articulo.select_one('p.precio span')
        precio = precio_element.text.strip()

        # Obtener el enlace del anuncio
        enlace_anuncio = articulo.select_one('a[href]')
        anuncio_url = enlace_anuncio['href']

        url_base = 'https://www.autocasion.com'
        url_completa = url_base + anuncio_url
        driver.get(url_completa)

        # Esperar a que la página individual del vehículo se cargue
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="carrusel-images"]')))
            num_fotos = int(driver.find_element(By.ID, 'carrusel-images').text.split()[0])
            imagenes_cargadas = 1;
            # Hacer clic en el enlace para ver las fotos utilizando JavaScript
            enlace_fotos = driver.find_element(By.XPATH, '//*[@id="carrusel-images"]')
            driver.execute_script("arguments[0].click();", enlace_fotos)

            # Crear una lista para almacenar las URLs de las imágenes del artículo
            imagenes_articulo = []

            # Esperar un poco para asegurar que se carguen todas las imágenes
            time.sleep(1)

            # Obtener las URLs de las imágenes
            images = driver.find_elements(By.XPATH, '//*[@id="modalVisualizador"]/div/div/div/section/div/img')

            # Crear una lista para almacenar las URLs de las imágenes del artículo

            for image in images:
                img_url = image.get_attribute('src')
                if img_url:
                    # Agregar la URL de la imagen a la lista 'imagenes_articulo'
                    imagenes_articulo.append(img_url)

            # Hacer clic en el botón para ver las siguientes imágenes
            try:
                while True:
                    # Encontrar el botón "Siguiente"
                    next_button = driver.find_element(By.XPATH,
                                                      '//*[@id="modalVisualizador"]/div/div/div/section/div/button[2]')
                    imagenes_cargadas += 1
                    # Hacer clic en el botón "Siguiente" para mostrar la siguiente imagen
                    driver.execute_script("arguments[0].click();", next_button)

                    # Esperar un poco para asegurar que se cargue la siguiente imagen
                    time.sleep(1)

                    # Obtener las URLs de las nuevas imágenes
                    images = driver.find_elements(By.XPATH, '//*[@id="modalVisualizador"]/div/div/div/section/div/img')

                    for image in images:
                        img_url = image.get_attribute('src')
                        if img_url:
                            # Agregar la URL de la imagen a la lista 'imagenes_articulo'
                            imagenes_articulo.append(img_url)

                    # Verificar si hay más imágenes disponibles (si el botón "Siguiente" está deshabilitado)
                    is_next_disabled = next_button.get_attribute('aria-disabled')
                    if is_next_disabled == 'true' or imagenes_cargadas >= num_fotos:
                        break
            except Exception as e:
                print("Error al obtener las imágenes adicionales:", e)

        except Exception as e:
            imagenes_articulo=[]

        # Crear un diccionario con los datos del artículo y la lista de imágenes
        datos_articulo = {
            'marca_modelo': marca_modelo,
            'kilometros': km,
            'año': año,
            'imagenes': imagenes_articulo,  # Agregar la lista de imágenes al diccionario
            'precio': precio
        }
        data_preprocessing_autocasion.insert_one(datos_articulo)
        driver.back()



    # Hacer clic en el botón "Siguiente" para ir a la siguiente página
    try:
        # Hacer clic en el botón "Siguiente"
        time.sleep(1)
        siguiente_button = WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, '//a[text()="Siguiente"]')))
        driver.execute_script("arguments[0].click();", siguiente_button)
    except Exception as e:
        print("No se puede hacer clic en el botón 'Siguiente'. Se detiene el proceso.")
        break


# Cerrar el controlador de Selenium
driver.quit()








