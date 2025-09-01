import os
import csv
import time
import threading
import tkinter as tk

from datetime import datetime
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException

# URLS
URL = "https://www.elempleo.com/co/ofertas-empleo/?PublishDate=hoy"
# URL = "https://www.elempleo.com/co/ofertas-empleo/?PublishDate=hace-2-semanas"


# Globales
ofertas_procesadas = set()
TIME_LIST = 8
TIME_WRITE = 5
TIME_LONG = 8
TIME_MED = 5
TIME_SHRT = 1
driver_instance = None
broker = 35

# Configuración carpeta y archivo
now = datetime.now()
fecha = now.strftime("%Y-%m-%d - %H-%M")
CARPETA_DATOS = "datos"
ARCHIVO_CSV = os.path.join(CARPETA_DATOS, f"ofertas_elempleo - {fecha}.csv")

if not os.path.exists(CARPETA_DATOS):
    os.makedirs(CARPETA_DATOS)

if not os.path.exists(ARCHIVO_CSV):
    with open(ARCHIVO_CSV, "w", newline="", encoding="utf-8") as file:
        # Delimitador
        writer = csv.writer(file, delimiter="|")
        writer.writerow(["id", "Titulo", "Salario", "Ciudad", "Fecha", "Detalle", "Cargo", "Tipo de puesto", "Nivel de educación", "Sector", "Experiencia", "Tipo de contrato", "Vacantes", "Areas", "Profesiones", "Nombre empresa", "Descripcion empresa", "Habilidades", "Cargos"])

# Ventana estado
root = tk.Tk()
root.title("Ejecución en proceso")
root.geometry("700x200")
root.resizable(False, False)
label = tk.Label(root, text="Ejecutando script...", font=("Arial", 12))
label.pack(pady=40)

def force_close():
    global driver_instance
    label.config(text="Cerrando...")
    if driver_instance:
        try:
            driver_instance.quit()
        except:
            pass
    root.quit()
    root.destroy()

btn_close = tk.Button(root, text="Finalizar", command=force_close, bg="red", fg="white")
btn_close.pack(pady=10)

# Configuración navegador
def setup_driver():
    prefs = {
        "profile.managed_default_content_settings.images": 2,  # Bloquear imágenes
        "profile.default_content_setting_values.notifications": 2,  # Bloquear notificaciones
        "profile.managed_default_content_settings.media_stream": 2,  # Bloquear cámara/micrófono
    }

    options = webdriver.ChromeOptions()
    options.add_experimental_option("prefs", prefs)
    # options.add_argument("--headless")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu-sandbox")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-ipc-flooding-protection")
    options.add_argument("--aggressive-cache-discard")
    options.add_argument("--disable-background-networking")
    options.add_argument("--log-level=3")
    options.add_argument("--silent")
    options.add_argument("--disable-logging")
    options.add_argument("--disable-gpu-logging")
    options.add_argument("--disable-extensions-http-throttling")
    driver = webdriver.Chrome(options=options)
    return driver

# Cerrar cookies
def cerrar_cookies(driver):
    try:
        btn_cookies = WebDriverWait(driver, TIME_MED).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='col-xs-12 col-sm-4 buttons-politics text-right']//a"))
        )
        btn_cookies.click()
    except NoSuchElementException:
        pass

# Extractor de texto
def extraer_info_oferta(driver):
    label.config(text="Escrapeando ofertas...")

    try:
        # Elementos sencillos
        titulo_oferta_element = driver.find_element(By.XPATH, "//div[@class='eeoffer-data-wrapper']//h1")
        salario_oferta_element = driver.find_element(By.XPATH, "//div[@class='eeoffer-data-wrapper']//span[contains(@class,'js-joboffer-salary')]")
        ciudad_oferta_element = driver.find_element(By.XPATH, "//div[@class='eeoffer-data-wrapper']//span[contains(@class,'js-joboffer-city')]")
        fecha_oferta_element = driver.find_element(By.XPATH, "//i[contains(@class,'fa-clock-o')]/following-sibling::span[2]")
        detalle_oferta_element = driver.find_element(By.XPATH, "//div[@class='description-block']//p//span")
        cargo_oferta_element = driver.find_element(By.XPATH, "//i[contains(@class,'fa-sitemap')]/following-sibling::span")
        tipo_puesto_oferta_element = driver.find_element(By.XPATH, "//i[contains(@class,'fa-user-circle')]/parent::p")
        nivel_educacion_oferta_element = driver.find_element(By.XPATH, "//i[contains(@class,'fa-graduation-cap')]/following-sibling::span")
        sector_oferta_element = driver.find_element(By.XPATH, "//i[contains(@class,'fa-building')]/following-sibling::span")
        experiencia_oferta_element = driver.find_element(By.XPATH, "//i[contains(@class,'fa-list')]/following-sibling::span")
        tipo_contrato_oferta_element = driver.find_element(By.XPATH, "//i[contains(@class,'fa-file-text')]/following-sibling::span")
        vacantes_oferta_element = driver.find_element(By.XPATH, "//i[contains(@class,'fa-address-book')]/parent::p")

        # Limpiar el texto de detalle_oferta_element
        detalle_oferta_texto = detalle_oferta_element.text.replace("\n", " ").replace("|", " ").replace("  ", " ").replace("   ", " ").replace("    ", " ").replace("\t", " ").replace(";" , " ").strip()

        # Tratamiento fecha invisible
        fecha_oferta_texto = fecha_oferta_element.get_attribute("textContent").strip()

        # Elementos con menú desplegable
        def cerrar_modales_abiertos():
            try:
                close_area = driver.find_element(By.XPATH, "//div[@id='AreasLightBox']//i[contains(@class,'fa-times-circle')]")
                if close_area.is_displayed():
                    driver.execute_script("arguments[0].click();", close_area)
                    time.sleep(0.5)
            except:
                pass
                
            try:
                close_prof = driver.find_element(By.XPATH, "//div[@id='ProfessionLightBox']//i[contains(@class,'fa-times-circle')]")
                if close_prof.is_displayed():
                    driver.execute_script("arguments[0].click();", close_prof)
                    time.sleep(0.5)
            except:
                pass

        try:
            boton_area_element = driver.find_element(By.XPATH, "//i[contains(@class,'fa-users')]/following-sibling::a")
            driver.execute_script("arguments[0].click();", boton_area_element)
            time.sleep(0.5)
            areas = WebDriverWait(driver, TIME_MED).until(
                
                EC.presence_of_all_elements_located((By.XPATH, "//div[@class='modal-content']//div[@class='modal-body']//li[@class='js-area']"))
            )
            time.sleep(0.5)
            areas_texto = [area.text.strip() for area in areas]
            cerrar_modales_abiertos()
        except:
            area_oferta = driver.find_element(By.XPATH, "//i[contains(@class,'fa-users')]/following-sibling::span")
            areas_texto = [area_oferta.text.strip()]

        areas_oferta = ", ".join(areas_texto)

        try:
            boton_profesion_element = driver.find_element(By.XPATH, "//i[contains(@class,'fa-briefcase')]/following-sibling::a")
            driver.execute_script("arguments[0].click();", boton_profesion_element)
            time.sleep(0.5)
            profesiones = WebDriverWait(driver, TIME_MED).until(
                EC.presence_of_all_elements_located((By.XPATH, "//div[@class='modal-content']//div[@class='modal-body']//li[@class='js-profession']"))
            )
            time.sleep(0.5)
            profesiones_texto = [profesion.text.strip() for profesion in profesiones]
            cerrar_modales_abiertos()
        except:
            profesion_oferta = driver.find_element(By.XPATH, "//i[contains(@class,'fa-briefcase')]/following-sibling::span")
            profesiones_texto = [profesion_oferta.text.strip()]

        profesiones_oferta = ", ".join(profesiones_texto)

        # Información de la empresa
        try:
            nombre_empresa_oferta_element = driver.find_element(By.XPATH, "//div[contains(@class,'ee-header-company')]//strong")
        except:
            nombre_empresa_oferta_element = driver.find_element(By.XPATH, "//div[contains(@class,'data-company')]//span//span//strong")    

        try:
            descripcion_empresa_oferta_element = driver.find_element(By.XPATH, "//div[contains(@class,'eeoffer-data-wrapper')]//div[contains(@class,'company-description')]//div")
        except:
            descripcion_empresa_oferta_element = driver.find_element(By.XPATH, "//div[contains(@class,'eeoffer-data-wrapper')]//span[contains(@class,'company-sector')]")


        # Información adicional
        try:
            habilidades = driver.find_elements(By.XPATH, "//div[@class='ee-related-words']//div[contains(@class,'ee-keywords')]//li//span")

            habilidades_texto = [habilidad.text.strip() for habilidad in habilidades if habilidad.text.strip()]
        except:
            try:
                habilidades = driver.find_elements(By.XPATH, "//div[contains(@class,'ee-related-words')]//div[contains(@class,'ee-keywords')]//li//span")
                habilidades_texto = [habilidad.text.strip() for habilidad in habilidades if habilidad.text.strip()]
            except:
                habilidades_texto = []

        if habilidades_texto:
            habilidades_oferta = ", ".join(habilidades_texto)
        else:
            habilidades_oferta = ""

        try:
            cargos = driver.find_elements(By.XPATH, "//div[@class='ee-related-words']//div[contains(@class,'ee-container-equivalent-positions')]//li")
            cargos_texto = [cargo.text.strip() for cargo in cargos if cargo.text.strip()]
        except:
            try:
                cargos = driver.find_elements(By.XPATH, "//div[contains(@class,'ee-related-words')]//div[contains(@class,'ee-equivalent-positions')]//li//span")
                cargos_texto = [cargo.text.strip() for cargo in cargos if cargo.text.strip()]
            except:
                cargos_texto = []

        if cargos_texto:
            cargos_oferta = ", ".join(cargos_texto)
        else:
            cargos_oferta = ""

        # Campo Id
        try:
            id_oferta_element = WebDriverWait(driver, TIME_MED).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'offer-data-additional')]//p//span[contains(@class,'js-offer-id')]"))
            )
            id_oferta_texto = id_oferta_element.get_attribute("textContent").strip()
        except:
            id_oferta_texto = f"ERROR-{broker}-{int(time.time())}"

        return id_oferta_texto, titulo_oferta_element, salario_oferta_element, ciudad_oferta_element, fecha_oferta_texto, detalle_oferta_texto, cargo_oferta_element, tipo_puesto_oferta_element, nivel_educacion_oferta_element, sector_oferta_element, experiencia_oferta_element, tipo_contrato_oferta_element, vacantes_oferta_element, areas_oferta, profesiones_oferta, nombre_empresa_oferta_element, descripcion_empresa_oferta_element, habilidades_oferta, cargos_oferta
    except Exception:
        return label.config(text="Error al obtener la información de la oferta")

# Escritura de la oferta
def escritura_datos(
        id_oferta_texto,
        titulo_oferta_element,
        salario_oferta_element,
        ciudad_oferta_element,
        fecha_oferta_texto,
        detalle_oferta_texto,
        cargo_oferta_element,
        tipo_puesto_oferta_element,
        nivel_educacion_oferta_element,
        sector_oferta_element,
        experiencia_oferta_element,
        tipo_contrato_oferta_element,
        vacantes_oferta_element,
        areas_oferta,
        profesiones_oferta,
        nombre_empresa_oferta_element,
        descripcion_empresa_oferta_element,
        habilidades_oferta,
        cargos_oferta
):
    datos = [
        id_oferta_texto,
        titulo_oferta_element.text,
        salario_oferta_element.text,
        ciudad_oferta_element.text,
        fecha_oferta_texto,
        detalle_oferta_texto,
        cargo_oferta_element.text,
        tipo_puesto_oferta_element.text,
        nivel_educacion_oferta_element.text,
        sector_oferta_element.text,
        experiencia_oferta_element.text,
        tipo_contrato_oferta_element.text,
        vacantes_oferta_element.text,
        areas_oferta,
        profesiones_oferta,
        nombre_empresa_oferta_element.text,
        descripcion_empresa_oferta_element.text,
        habilidades_oferta,
        cargos_oferta
    ]
    label.config(text="Escribiendo oferta...")
    with open(ARCHIVO_CSV, "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, delimiter="|")
        writer.writerow(datos)

def lector_ofertas(driver):
    global ofertas_procesadas
    
    try:
        WebDriverWait(driver, TIME_MED).until(lambda d: d.execute_script("return document.readyState") == "complete")
        label.config(text="Buscando ofertas...")
        ofertas = WebDriverWait(driver, TIME_LIST).until(
            EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@class, 'text-ellipsis js-offer-title')]"))
        )
        
        total_ofertas = len(ofertas)
        label.config(text=f"Ofertas encontradas: {total_ofertas}")
        
        if total_ofertas == 0:
            label.config(text="No se encontraron ofertas en esta página")
            return False
        
        enlaces_ofertas = []
        for i, oferta in enumerate(ofertas):
            try:
                enlace = (oferta.get_dom_attribute("href") or oferta.get_attribute("href") or "").strip()
                if enlace and enlace not in ofertas_procesadas:
                    enlaces_ofertas.append({
                        'enlace': enlace,
                        'posicion': i + 1
                    })
                    # ofertas_procesadas.add(enlace)
                else:
                    print(f"Oferta {i+1}: Enlace vacío o ya procesada")
            except Exception as e:
                print(f"Error obteniendo enlace de oferta {i+1}: {str(e)}")
                continue
        
        ofertas_nuevas = len(enlaces_ofertas)
        label.config(text=f"Ofertas nuevas a procesar: {ofertas_nuevas}")
        
        if ofertas_nuevas == 0:
            label.config(text="No hay ofertas nuevas para procesar")
            return True
        
        ventana_original = driver.current_window_handle
        
        for i, oferta_data in enumerate(enlaces_ofertas):
            enlace = oferta_data['enlace']
            posicion = oferta_data['posicion']
            
            try:
                label.config(text=f"Procesando oferta {i+1}/{ofertas_nuevas} (Posición {posicion})")
                
                if driver.current_window_handle != ventana_original:
                    driver.switch_to.window(ventana_original)
                
                driver.execute_script(f"window.open('{enlace}', '_blank')")
                
                WebDriverWait(driver, TIME_MED).until(lambda d: len(d.window_handles) > 1)
                driver.switch_to.window(driver.window_handles[-1])
                
                WebDriverWait(driver, TIME_LONG).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                
                try:
                    datos_oferta = extraer_info_oferta(driver)
                    escritura_datos(*datos_oferta)
                    ofertas_procesadas.add(enlace)
                except Exception as e:
                    print(f"Error WebDriver en oferta {posicion}: {str(e)}")
                
                label.config(text=f"Oferta {i+1} procesada correctamente")
                
            except TimeoutException:
                label.config(text=f"Timeout procesando oferta {i+1}")
                print(f"Timeout en oferta {posicion}: {enlace}")
            except WebDriverException as e:
                label.config(text=f"Error de WebDriver en oferta {i+1}")
                print(f"Excepción error WebDriver en oferta {posicion}: {str(e)}")
            except Exception as e:
                label.config(text=f"Error inesperado en oferta {i+1}")
                print(f"Error inesperado en oferta {posicion}: {str(e)}")
            finally:
                try:
                    if len(driver.window_handles) > 1:
                        driver.close()
                    driver.switch_to.window(ventana_original)
                except:
                    try:
                        driver.switch_to.window(driver.window_handles[0])
                    except:
                        pass
        
        label.config(text=f"Procesamiento completado: {ofertas_nuevas} ofertas")
        return True
        
    except TimeoutException:
        label.config(text="Timeout: No se pudieron encontrar ofertas")
        return False
    except Exception as e:
        label.config(text=f"Error crítico en lector_ofertas: {str(e)}")
        print(f"Error crítico: {str(e)}")
        return False
    
def siguiente_pagina(driver):
    try:
        # Guarda el primer <a> para comparar
        first_a = driver.find_element(By.XPATH, "//a[contains(@class,'js-offer-title')]")
        btn_siguiente = driver.find_element(By.XPATH, "//ul[contains(@class,'pagination')]//li//a//i[contains(@class,'fa-angle-right')]")
        li_contenedor = driver.find_element(By.XPATH, "//ul[contains(@class,'pagination')]//li//a//i[contains(@class,'fa-angle-right')]/ancestor::li")
        if "disabled" in li_contenedor.get_attribute("class").split():
            return False

        driver.execute_script("arguments[0].click();", btn_siguiente)

        # Esperar al cierre del primer DOM
        WebDriverWait(driver, TIME_LONG).until(EC.staleness_of(first_a))
        WebDriverWait(driver, TIME_LONG).until(
            EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@class,'js-offer-title')]"))
        )
        return True
    except NoSuchElementException:
        return False

# Bucle inicio global
def main():
    global root, driver_instance
    driver_instance = setup_driver()
    try:
        driver_instance.get(URL)
        cerrar_cookies(driver_instance)
        pag = 1
        while True:
            ok = lector_ofertas(driver_instance)
            label.config(text="Ofertas procesadas correctamente")
            label.config(text=f"Ofertas procesadas correctamente. Páginas: {pag}")
            if not ok:
                label.config(text="No se pudieron procesar las ofertas")
                break
            if not siguiente_pagina(driver_instance):
                break
            pag += 1

    except Exception as e:
        label.config(text=f"Error en ejecución: {str(e)}")
    finally:
        label.config(text="Cerrando navegador...")
        try:
            driver_instance.quit()
        except:
            pass
        driver_instance = None

        root.after(2000, lambda: root.quit())


def run_scraping():
    try:
        main()
    except Exception as e:
        label.config(text=f"Error crítico: {str(e)}")
        root.after(3000, lambda: root.quit())

def on_closing():
    force_close()

root.protocol("WM_DELETE_WINDOW", on_closing)

threading.Thread(target=run_scraping, daemon=True).start()
root.mainloop()