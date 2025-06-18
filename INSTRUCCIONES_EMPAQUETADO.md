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
4.  **Tesseract OCR**: Tesseract (incluyendo las herramientas de desarrollo/entrenamiento como `tesseract`, `unicharset_extractor`, `mftraining`, `cntraining`, `combine_tessdata`) DEBE estar instalado en el sistema donde se **ejecutará** el `.exe` final, y sus ejecutables deben estar en el PATH del sistema. PyInstaller **no** empaqueta Tesseract en sí mismo. (Consulta la documentación oficial de Tesseract para su instalación).

5.  **Poppler (para funcionalidad PDF)**:
    *   La biblioteca `pdf2image` que usa la aplicación para procesar archivos PDF depende de Poppler.
    *   Poppler DEBE estar instalado en el sistema donde se **ejecutará** el `.exe` final, y las utilidades de Poppler (específicamente `pdftoppm.exe` y `pdfinfo.exe`) deben estar accesibles a través del PATH del sistema.
    *   PyInstaller **no** empaqueta Poppler.

    **Cómo Instalar Poppler en Windows y Añadirlo al PATH:**

    1.  **Descargar Poppler para Windows:**
        *   Poppler no tiene un instalador oficial simple para Windows. Necesitarás descargar una compilación de los binarios.
        *   Una fuente común y recomendada es la página de versiones del proyecto `poppler-windows` en GitHub de @oschwartz10612: [https://github.com/oschwartz10612/poppler-windows/releases/](https://github.com/oschwartz10612/poppler-windows/releases/)
        *   Descarga la última versión disponible (por ejemplo, `poppler-23.11.0-0_Windows.zip` o similar). Elige la versión que corresponda a tu sistema (32 o 64 bits, aunque las versiones más recientes suelen ser de 64 bits).

    2.  **Descomprimir Poppler:**
        *   Crea una carpeta en tu sistema donde quieras guardar Poppler. Por ejemplo: `C:\Program Files\poppler` o `C:\poppler`.
        *   Descomprime el contenido del archivo ZIP que descargaste dentro de esta carpeta. Deberías terminar con una estructura de carpetas como `C:\poppler\poppler-23.11.0-0in`, `C:\poppler\poppler-23.11.0\lib`, etc. (La ruta exacta de la subcarpeta con la versión puede variar).
        *   La carpeta crucial es la que contiene los archivos `.exe` como `pdftoppm.exe`. Usualmente es la subcarpeta `bin` o a veces `Libraryin` dentro de la carpeta de la versión de Poppler (ej: `C:\poppler\poppler-23.11.0-0in`). **Identifica y anota esta ruta completa.**

    3.  **Añadir la Carpeta `bin` de Poppler al PATH del Sistema:**
        *   Haz clic en el botón de **Inicio** de Windows.
        *   Escribe "**variables de entorno**" en la barra de búsqueda.
        *   Selecciona "**Editar las variables de entorno del sistema**". Esto abrirá la ventana de "Propiedades del sistema".
        *   En la pestaña "**Opciones avanzadas**", haz clic en el botón "**Variables de entorno...**".
        *   En la nueva ventana "Variables de entorno", en la sección inferior "**Variables del sistema**", busca la variable llamada `Path` (o `PATH`). Selecciónala.
        *   Haz clic en el botón "**Editar...**".
        *   En la ventana "Editar la variable de entorno", haz clic en "**Nuevo**".
        *   Pega la ruta completa a la carpeta `bin` de Poppler que anotaste anteriormente (ej: `C:\poppler\poppler-23.11.0-0in`).
        *   Haz clic en "**Aceptar**" en todas las ventanas abiertas ("Editar la variable de entorno", "Variables de entorno", "Propiedades del sistema") para guardar los cambios.

    4.  **Verificar y Reiniciar:**
        *   Para que los cambios en el PATH tengan efecto, **reinicia cualquier Símbolo del sistema (cmd) o PowerShell que tengas abierto**.
        *   **Reinicia la aplicación de entrenamiento Tesseract** si la tenías abierta.
        *   Si el problema persiste, un **reinicio completo de tu computadora** puede ser necesario.
        *   Para verificar si Poppler está en el PATH, puedes abrir un nuevo Símbolo del sistema y escribir `pdftoppm -h`. Si no da un error de comando no encontrado, Poppler está configurado.

## Pasos para Empaquetar con PyInstaller

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
    *   `--onefile`: Crea un único archivo `.exe`.
    *   `--windowed`: Suprime la ventana de consola para aplicaciones GUI.
    *   `--name EntrenadorTesseract`: Nombre del `.exe` resultante (ej. `EntrenadorTesseract.exe`).
    *   `app_entrenamiento_tesseract.py`: Script principal.

4.  **Encontrar el Ejecutable**:
    El `.exe` estará en la carpeta `dist` (ej. `dist/EntrenadorTesseract.exe`).

## Consideraciones Adicionales

*   **Icono de la Aplicación**: Usa `--icon=tu_icono.ico` para añadir un icono.
*   **Dependencias Externas**: Recuerda, Tesseract y Poppler deben estar instalados y en el PATH del sistema donde se ejecute el `.exe`. Comunica esto claramente al distribuir la aplicación.
*   **Errores Comunes**:
    *   `FileNotFoundError` para Tesseract/Poppler: Indica que no están en el PATH del sistema destino.
    *   Módulos no encontrados por PyInstaller: Usa `--hidden-import MODULENAME` o edita el archivo `.spec`.
*   **Tamaño del Ejecutable**: Los ejecutables `--onefile` pueden ser grandes.
*   **Pruebas**: Prueba siempre en una máquina limpia (o VM) con Tesseract y Poppler instalados, pero sin tu entorno de desarrollo Python.

## Limpieza
Puedes eliminar las carpetas `build` y el archivo `.spec` después de generar el ejecutable.
