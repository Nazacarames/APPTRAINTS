# Guía para Empaquetar la Aplicación de Entrenamiento Tesseract en un .EXE

Esta guía te ayudará a empaquetar la aplicación Python (`app_entrenamiento_tesseract.py`) en un archivo ejecutable (`.exe`) para Windows, facilitando su distribución y uso sin necesidad de tener Python instalado en la máquina destino (aunque ciertas dependencias como Tesseract y Poppler aún necesitarán ser manejadas).

Usaremos **PyInstaller** para este propósito.

## Prerrequisitos

1.  **Python**: Debes tener Python instalado en tu sistema. La aplicación fue desarrollada con Python 3.x.
2.  **Pip**: El instalador de paquetes de Python, usualmente viene con Python.
3.  **Aplicación Funcional**: El script `app_entrenamiento_tesseract.py` y todas sus dependencias de Python (`Pillow`, `pdf2image`) deben estar instalados en tu entorno de Python donde ejecutarás PyInstaller.
    ```bash
    pip install Pillow pdf2image
    ```
4.  **Tesseract OCR**: Tesseract (incluyendo las herramientas de desarrollo/entrenamiento como `tesseract`, `unicharset_extractor`, `mftraining`, `cntraining`, `combine_tessdata`) DEBE estar instalado en el sistema donde se **ejecutará** el `.exe` final, y sus ejecutables deben estar en el PATH del sistema. PyInstaller **no** empaqueta Tesseract en sí mismo.
5.  **Poppler**: Para la funcionalidad de procesamiento de PDF, Poppler DEBE estar instalado en el sistema donde se **ejecutará** el `.exe` final, y las utilidades de Poppler (específicamente `pdftoppm` y `pdfinfo`) deben estar en el PATH del sistema o accesibles para la biblioteca `pdf2image`. PyInstaller **no** empaqueta Poppler.
    *   Puedes descargar Poppler para Windows desde [varias fuentes no oficiales](https://github.com/oschwartz10612/poppler-windows/releases/) que compilan los binarios. Asegúrate de añadir la carpeta `bin` de Poppler a tu PATH.

## Pasos para Empaquetar

1.  **Instalar PyInstaller**:
    Abre una terminal o símbolo del sistema y ejecuta:
    ```bash
    pip install pyinstaller
    ```

2.  **Navegar al Directorio de la Aplicación**:
    En la terminal, navega hasta el directorio donde tienes guardado `app_entrenamiento_tesseract.py`.

3.  **Ejecutar PyInstaller**:
    El comando básico para crear un ejecutable de un solo archivo y sin ventana de consola (ya que es una app GUI) es:
    ```bash
    pyinstaller --onefile --windowed --name EntrenadorTesseract app_entrenamiento_tesseract.py
    ```
    Desglose del comando:
    *   `pyinstaller`: Llama a la herramienta.
    *   `--onefile`: Crea un único archivo `.exe` (puede tardar más en iniciar, pero es más simple de distribuir). Si omites esto, creará una carpeta con muchos archivos junto al `.exe`.
    *   `--windowed`: Suprime la aparición de una ventana de consola cuando se ejecuta la aplicación GUI.
    *   `--name EntrenadorTesseract`: Especifica el nombre que tendrá el archivo `.exe` resultante (ej. `EntrenadorTesseract.exe`).
    *   `app_entrenamiento_tesseract.py`: Es el script principal de tu aplicación.

4.  **Encontrar el Ejecutable**:
    PyInstaller creará varias carpetas (`build`, `dist`) y un archivo `.spec`.
    *   Tu archivo `.exe` final estará dentro de la carpeta `dist`. Por ejemplo, `dist/EntrenadorTesseract.exe`.

## Consideraciones Adicionales

*   **Icono de la Aplicación**: Puedes añadir un icono personalizado a tu `.exe` usando la opción `--icon=tu_icono.ico` en el comando de PyInstaller. Asegúrate de que `tu_icono.ico` exista.
    ```bash
    pyinstaller --onefile --windowed --name EntrenadorTesseract --icon=app_icon.ico app_entrenamiento_tesseract.py
    ```
*   **Archivos de Datos y Hook (Avanzado)**:
    *   Nuestra aplicación actual no usa archivos de datos externos que necesite empaquetar (como imágenes o configuraciones JSON propias).
    *   Sin embargo, `pdf2image` depende de Poppler, y Tesseract es una dependencia externa. PyInstaller no puede empaquetar estas dependencias de sistema. El usuario final **siempre** necesitará tener Tesseract y Poppler correctamente instalados y en su PATH. Debes comunicar esto claramente.
*   **Errores Comunes**:
    *   **`FileNotFoundError` para Tesseract/Poppler al correr el `.exe`**: Esto significa que Tesseract o Poppler no están en el PATH del sistema donde se está ejecutando el `.exe`.
    *   **Módulos no encontrados por PyInstaller**: A veces, PyInstaller no detecta automáticamente todos los módulos importados (especialmente los "ocultos" o los importados dinámicamente). Podrías necesitar usar la opción `--hidden-import MODULENAME` o editar el archivo `.spec` generado. Para `pdf2image` y `Pillow`, esto no suele ser un problema.
*   **Tamaño del Ejecutable**: Los ejecutables `--onefile` pueden ser grandes porque empaquetan una versión de Python y las bibliotecas necesarias.
*   **Pruebas**: Siempre prueba tu ejecutable en una máquina limpia (o una máquina virtual) que no tenga tu entorno de desarrollo Python, pero SÍ tenga Tesseract y Poppler instalados, para simular la experiencia del usuario final.

## Limpieza
Después de generar el ejecutable, puedes eliminar las carpetas `build` y el archivo `.spec` si lo deseas. Mantén la carpeta `dist` que contiene tu `.exe`.

Esta guía debería ser suficiente para empezar a empaquetar tu aplicación. ¡Buena suerte!
