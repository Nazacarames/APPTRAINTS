import tkinter as tk
from tkinter import filedialog, Listbox, Entry, Label, Button, Frame, simpledialog, messagebox, scrolledtext
import os
import shutil
import subprocess
import threading
import glob
from PIL import Image

try:
    from pdf2image import convert_from_path
    from pdf2image.exceptions import PDFInfoNotInstalledError, PDFPageCountError, PDFSyntaxError, PDFPopplerTimeoutError
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

class TesseractTrainerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Herramienta de Entrenamiento Tesseract (con soporte PDF)")
        self.root.geometry("800x750")

        self.image_paths_with_text = {}
        self.training_base_dir = "datos_entrenamiento_tesseract"
        self.pdf_temp_image_dir = os.path.join(self.training_base_dir, "pdf_imagenes_extraidas")

        self.current_training_dir = None
        self.lang_code = ""
        self.model_name = ""
        self.font_name = "customfont"

        if PDF2IMAGE_AVAILABLE:
            try:
                os.makedirs(self.pdf_temp_image_dir, exist_ok=True)
            except OSError as e:
                print(f"Advertencia: No se pudo crear el directorio para imágenes de PDF: {e}")

        if not PDF2IMAGE_AVAILABLE:
            print("ADVERTENCIA INICIAL: La biblioteca pdf2image no se encontró o Poppler no está configurado.")
            print("La funcionalidad para procesar archivos PDF no estará disponible.")
            # Considerar mostrar esto en el log de la GUI también al inicio.
            # self.log_message("ADVERTENCIA: pdf2image/Poppler no disponible. Carga de PDFs deshabilitada.") # No se puede llamar a log_message aquí aún.

        top_frame = Frame(root)
        top_frame.pack(pady=10)
        Label(top_frame, text="Código de Idioma (ej: spa):").pack(side=tk.LEFT, padx=5)
        self.lang_code_entry = Entry(top_frame, width=10)
        self.lang_code_entry.pack(side=tk.LEFT, padx=5)
        self.lang_code_entry.insert(0, "spa")
        Label(top_frame, text="Nombre del Modelo Salida:").pack(side=tk.LEFT, padx=5)
        self.model_name_entry = Entry(top_frame, width=20)
        self.model_name_entry.pack(side=tk.LEFT, padx=5)
        self.model_name_entry.insert(0, "custom_model")

        middle_frame = Frame(root)
        middle_frame.pack(pady=10, fill=tk.BOTH, expand=True)
        Label(middle_frame, text="Imágenes/PDFs para Entrenar (ruta - 'texto asignado'):").pack()
        self.image_listbox = Listbox(middle_frame, selectmode=tk.SINGLE, width=80, height=10)
        self.image_listbox.pack(pady=5, padx=20, fill=tk.BOTH, expand=True)
        self.image_listbox.bind('<<ListboxSelect>>', self.on_image_select)

        image_buttons_frame = Frame(middle_frame)
        image_buttons_frame.pack(pady=5)
        self.add_files_button = Button(image_buttons_frame, text="Añadir Archivos (Imágenes/PDF)", command=self.add_files)
        self.add_files_button.pack(side=tk.LEFT, padx=5)
        self.set_image_text_button = Button(image_buttons_frame, text="Asignar/Editar Texto", command=self.set_image_text, state=tk.DISABLED)
        self.set_image_text_button.pack(side=tk.LEFT, padx=5)
        self.remove_image_button = Button(image_buttons_frame, text="Remover Seleccionada", command=self.remove_selected_image, state=tk.DISABLED)
        self.remove_image_button.pack(side=tk.LEFT, padx=5)

        bottom_frame = Frame(root)
        bottom_frame.pack(pady=10)
        self.train_button = Button(bottom_frame, text="Iniciar Entrenamiento", command=self.start_training_thread, state=tk.DISABLED)
        self.train_button.pack()

        log_frame = Frame(root)
        log_frame.pack(pady=10, fill=tk.BOTH, expand=True, side=tk.BOTTOM)
        Label(log_frame, text="Log de Actividad y Entrenamiento:").pack()
        self.log_text_widget = scrolledtext.ScrolledText(log_frame, height=15, state=tk.DISABLED, wrap=tk.WORD)
        self.log_text_widget.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

    def log_message(self, message, clear_log=False):
        self.root.after(0, self._log_message_thread_safe, message, clear_log)

    def _log_message_thread_safe(self, message, clear_log):
        self.log_text_widget.config(state=tk.NORMAL)
        if clear_log: self.log_text_widget.delete('1.0', tk.END)
        self.log_text_widget.insert(tk.END, message + "\n")
        self.log_text_widget.see(tk.END)
        self.log_text_widget.config(state=tk.DISABLED)

    def _clean_filename(self, filename):
        name, ext = os.path.splitext(filename)
        name = name.replace(" ", "_")
        return name + ext

    def _convert_pdf_to_images(self, pdf_path):
        if not PDF2IMAGE_AVAILABLE:
            self.log_message("Error: pdf2image no está instalado o Poppler no está configurado.")
            self.root.after(0, messagebox.showerror, "Error de PDF", "pdf2image/Poppler no disponible.", {"parent": self.root})
            return None

        self.log_message(f"Iniciando conversión de PDF: {os.path.basename(pdf_path)}...")
        try:
            os.makedirs(self.pdf_temp_image_dir, exist_ok=True)
        except OSError as e:
            self.log_message(f"Error crítico: No se pudo crear directorio para imágenes de PDF '{self.pdf_temp_image_dir}': {e}")
            self.root.after(0, messagebox.showerror, "Error de Directorio", f"No se pudo crear directorio temporal para PDF: {e}", {"parent": self.root})
            return None

        extracted_image_paths = []
        try:
            pdf_basename = os.path.splitext(os.path.basename(pdf_path))[0]
            pdf_basename = self._clean_filename(pdf_basename)
            pil_images = convert_from_path(pdf_path, dpi=300, thread_count=os.cpu_count() or 1)
            if not pil_images:
                self.log_message(f"pdf2image no retornó imágenes para {os.path.basename(pdf_path)}. ¿PDF vacío o dañado?")
                return None
            for i, image_obj in enumerate(pil_images):
                page_num = i + 1
                image_filename = f"{pdf_basename}_pagina_{page_num}.png"
                image_full_path = os.path.join(self.pdf_temp_image_dir, image_filename)
                try:
                    image_obj.save(image_full_path, "PNG")
                    extracted_image_paths.append(image_full_path)
                except Exception as save_e:
                    self.log_message(f"Error al guardar la página {page_num} de {pdf_basename} como imagen: {save_e}")
            if not extracted_image_paths:
                 self.log_message(f"No se pudieron extraer y guardar páginas válidas de {pdf_basename}.")
                 return None
            self.log_message(f"PDF '{os.path.basename(pdf_path)}' convertido a {len(extracted_image_paths)} imágenes en '{self.pdf_temp_image_dir}'.")
            return extracted_image_paths
        except PDFInfoNotInstalledError:
            self.log_message("Error de Poppler: Poppler no está instalado o no se encuentra en el PATH del sistema.")
            self.root.after(0, messagebox.showerror, "Error de Poppler", "Poppler no encontrado. Instálalo y asegúrate que esté en el PATH.", {"parent": self.root})
            return None
        except (PDFPageCountError, PDFSyntaxError) as e:
            self.log_message(f"Error en el archivo PDF '{os.path.basename(pdf_path)}': {e}")
            self.root.after(0, messagebox.showerror, "Error de PDF", f"El PDF '{os.path.basename(pdf_path)}' es inválido o está corrupto: {e}", {"parent": self.root})
            return None
        except PDFPopplerTimeoutError as e:
            self.log_message(f"Timeout al procesar PDF '{os.path.basename(pdf_path)}' con Poppler: {e}")
            self.root.after(0, messagebox.showerror, "Error de PDF", f"Timeout procesando PDF '{os.path.basename(pdf_path)}'.", {"parent": self.root})
            return None
        except Exception as e:
            self.log_message(f"Error inesperado durante conversión de PDF '{os.path.basename(pdf_path)}': {type(e).__name__} - {e}")
            self.root.after(0, messagebox.showerror, "Error de Conversión PDF", f"Fallo inesperado al convertir PDF: {e}", {"parent": self.root})
            return None

    def add_files(self):
        filetypes = (
            ('Archivos Soportados', '*.png *.tif *.tiff *.jpg *.jpeg *.pdf'),
            ('Imágenes PNG', '*.png'),
            ('Imágenes TIFF', '*.tif *.tiff'),
            ('Imágenes JPEG', '*.jpg *.jpeg'),
            ('Documentos PDF', '*.pdf'),
            ('Todos los archivos', '*.*')
        )
        initial_dir = getattr(self, "_last_filedialog_path", os.path.expanduser("~"))

        selected_files = filedialog.askopenfilenames(
            title='Selecciona imágenes o PDFs para entrenar',
            filetypes=filetypes,
            initialdir=initial_dir,
            parent=self.root
        )

        if selected_files:
            self._last_filedialog_path = os.path.dirname(selected_files[0])
            new_items_added_to_listbox = False

            for file_path_orig in selected_files:
                base_name_orig = os.path.basename(file_path_orig)

                if file_path_orig.lower().endswith(".pdf"):
                    if PDF2IMAGE_AVAILABLE:
                        self.log_message(f"Procesando PDF: {base_name_orig}...")
                        image_paths_from_pdf = self._convert_pdf_to_images(file_path_orig) # Esto ya loguea el resultado de la conversión

                        if image_paths_from_pdf: # Si la conversión fue exitosa y retornó rutas
                            for img_path in image_paths_from_pdf:
                                if img_path not in self.image_paths_with_text:
                                    self.image_paths_with_text[img_path] = ""
                                    # Añadir la ruta de la imagen extraída al listbox, para que el usuario le asigne texto
                                    self.image_listbox.insert(tk.END, f"{img_path} - ''")
                                    self.log_message(f"Imagen de PDF '{os.path.basename(img_path)}' añadida a la lista para asignación de texto.")
                                    new_items_added_to_listbox = True
                                else:
                                    self.log_message(f"Imagen de PDF '{os.path.basename(img_path)}' ya estaba en la lista.")
                        # else: _convert_pdf_to_images ya habrá logueado el error/fallo.
                    else: # PDF2IMAGE_AVAILABLE es False
                        self.log_message(f"PDF '{base_name_orig}' ignorado; pdf2image/Poppler no disponible.")
                        messagebox.showwarning("PDF no Soportado", "Carga de PDFs deshabilitada (pdf2image o Poppler no están instalados/configurados correctamente).", parent=self.root)

                elif file_path_orig.lower().endswith(('.png', '.tif', '.tiff', '.jpg', '.jpeg')):
                    file_path = file_path_orig
                    original_dir = os.path.dirname(file_path)
                    sanitized_basename = self._clean_filename(base_name_orig)

                    if base_name_orig != sanitized_basename:
                        sanitized_full_path = os.path.join(original_dir, sanitized_basename)
                        try:
                            if os.path.abspath(file_path).lower() != os.path.abspath(sanitized_full_path).lower() and                                not os.path.exists(sanitized_full_path):
                                os.rename(file_path, sanitized_full_path)
                                self.log_message(f"Archivo renombrado: '{base_name_orig}' -> '{sanitized_basename}'")
                                file_path = sanitized_full_path
                            elif os.path.exists(sanitized_full_path) and os.path.abspath(file_path).lower() != os.path.abspath(sanitized_full_path).lower():
                                 self.log_message(f"Advertencia: '{sanitized_basename}' ya existe. Usando nombre original '{base_name_orig}'.")
                            else:
                                file_path = sanitized_full_path
                        except OSError as e:
                            self.log_message(f"Error al renombrar '{base_name_orig}': {e}. Usando nombre original.")

                    if file_path not in self.image_paths_with_text:
                        self.image_paths_with_text[file_path] = ""
                        self.image_listbox.insert(tk.END, f"{file_path} - ''")
                        self.log_message(f"Archivo de imagen añadido: {os.path.basename(file_path)}")
                        new_items_added_to_listbox = True
                    else:
                        self.log_message(f"Archivo de imagen ya listado: {os.path.basename(file_path)}")
                else:
                    self.log_message(f"Archivo no soportado ignorado: {base_name_orig}")

            if new_items_added_to_listbox and self.image_listbox.size() > 0:
                last_idx = self.image_listbox.size() - 1
                if self.image_listbox.get(last_idx): # Asegurar que el último ítem no esté vacío
                    self.image_listbox.select_clear(0, tk.END)
                    self.image_listbox.select_set(last_idx)
                    self.image_listbox.activate(last_idx)
                    self.on_image_select(None) # Actualizar estado de botones
            self.update_train_button_state()
        else:
            self.log_message("No se seleccionaron archivos.")

    def on_image_select(self, event):
        if self.image_listbox.curselection():
            self.set_image_text_button.config(state=tk.NORMAL); self.remove_image_button.config(state=tk.NORMAL)
        else:
            self.set_image_text_button.config(state=tk.DISABLED); self.remove_image_button.config(state=tk.DISABLED)

    def set_image_text(self):
        selected_indices = self.image_listbox.curselection()
        if not selected_indices: messagebox.showwarning("Advertencia", "No has seleccionado ninguna imagen.", parent=self.root); return
        selected_index = selected_indices[0]
        listbox_entry_text = self.image_listbox.get(selected_index)
        image_path = listbox_entry_text.split(" - '")[0] if " - '" in listbox_entry_text else listbox_entry_text
        current_text = self.image_paths_with_text.get(image_path, "")
        new_text = simpledialog.askstring("Asignar Texto", f"Texto para:\n{os.path.basename(image_path)}", initialvalue=current_text, parent=self.root)
        if new_text is not None:
            self.image_paths_with_text[image_path] = new_text
            self.image_listbox.delete(selected_index); self.image_listbox.insert(selected_index, f"{image_path} - '{new_text}'"); self.image_listbox.select_set(selected_index)
            self.log_message(f"Texto asignado a {os.path.basename(image_path)}: '{new_text}'")
            self.update_train_button_state()
        else:
            self.log_message(f"Asignación de texto cancelada para {os.path.basename(image_path)}.")

    def remove_selected_image(self):
        selected_indices = self.image_listbox.curselection()
        if not selected_indices: messagebox.showwarning("Advertencia", "No has seleccionado imagen para remover.", parent=self.root); return
        selected_index = selected_indices[0]
        listbox_entry_text = self.image_listbox.get(selected_index)
        image_path_to_remove = listbox_entry_text.split(" - '")[0] if " - '" in listbox_entry_text else listbox_entry_text

        confirm_msg = f"¿Remover '{os.path.basename(image_path_to_remove)}' de la lista?"
        is_pdf_extracted_image = self.pdf_temp_image_dir is not None and self.pdf_temp_image_dir in os.path.normpath(image_path_to_remove)

        if messagebox.askyesno("Confirmar", confirm_msg, parent=self.root):
            self.image_listbox.delete(selected_index)
            if image_path_to_remove in self.image_paths_with_text: del self.image_paths_with_text[image_path_to_remove]

            if is_pdf_extracted_image:
                 self.log_message(f"Ítem removido: {os.path.basename(image_path_to_remove)} (imagen de PDF).")
                 # No se elimina del disco automáticamente por defecto.
            else:
                self.log_message(f"Ítem removido de la lista: {os.path.basename(image_path_to_remove)}")

            if self.image_listbox.size() == 0: self.set_image_text_button.config(state=tk.DISABLED); self.remove_image_button.config(state=tk.DISABLED)
            elif selected_index > 0: self.image_listbox.select_set(selected_index -1); self.image_listbox.activate(selected_index -1)
            elif self.image_listbox.size() > 0: self.image_listbox.select_set(0); self.image_listbox.activate(0)
            self.on_image_select(None); self.update_train_button_state()

    def update_train_button_state(self):
        if not self.image_paths_with_text: self.train_button.config(state=tk.DISABLED); return
        all_texts_assigned = all(text.strip() for text in self.image_paths_with_text.values())
        self.train_button.config(state=tk.NORMAL if all_texts_assigned else tk.DISABLED)

    def set_ui_state(self, enabled):
        self.add_files_button.config(state=tk.NORMAL if enabled else tk.DISABLED)
        set_text_enabled = enabled and self.image_listbox.curselection()
        remove_enabled = enabled and self.image_listbox.curselection()
        self.set_image_text_button.config(state=tk.NORMAL if set_text_enabled else tk.DISABLED)
        self.remove_image_button.config(state=tk.NORMAL if remove_enabled else tk.DISABLED)
        self.train_button.config(state=tk.NORMAL if enabled else tk.DISABLED)
        self.lang_code_entry.config(state=tk.NORMAL if enabled else tk.DISABLED)
        self.model_name_entry.config(state=tk.NORMAL if enabled else tk.DISABLED)
        if enabled: self.update_train_button_state()

    def _ask_clean_directory(self, dir_path):
        if not os.path.exists(dir_path): return None # Corrección: debería ser True si no existe, o manejar None en el llamador
        response = messagebox.askyesno("Confirmar Limpieza",
                                       f"El directorio '{dir_path}' ya existe y podría contener archivos de un proceso anterior. ¿Quieres limpiarlo (eliminar su contenido) y continuar?",
                                       parent=self.root)
        if response:
            self.log_message(f"Usuario aceptó limpiar directorio '{dir_path}'.")
            try:
                shutil.rmtree(dir_path)
                os.makedirs(dir_path, exist_ok=True)
                self.log_message(f"Directorio '{dir_path}' limpiado y recreado.")
                return True
            except Exception as e:
                self.log_message(f"Error al limpiar el directorio '{dir_path}': {e}")
                messagebox.showerror("Error de Directorio", f"No se pudo limpiar el directorio '{dir_path}'. Error: {e}", parent=self.root)
                return False
        else:
            self.log_message("Usuario decidió no limpiar el directorio. El entrenamiento podría usar archivos antiguos o fallar.")
            return True # Permitir continuar si el usuario no quiere limpiar. El pipeline podría fallar.

    def start_training_thread(self):
        self.log_message("Validando datos...", clear_log=True)
        self.lang_code = self.lang_code_entry.get().strip()
        self.model_name = self.model_name_entry.get().strip()
        if not self.lang_code: messagebox.showerror("Error", "Código de idioma vacío.", parent=self.root); self.log_message("Error: Código de idioma vacío."); return
        if not self.model_name: messagebox.showerror("Error", "Nombre de modelo vacío.", parent=self.root); self.log_message("Error: Nombre de modelo vacío."); return
        if not self.image_paths_with_text: messagebox.showerror("Error", "No hay archivos.", parent=self.root); self.log_message("Error: No hay archivos."); return
        if not all(text.strip() for text in self.image_paths_with_text.values()): messagebox.showerror("Error", "Asignar texto a todas las imágenes.", parent=self.root); self.log_message("Error: Faltan textos."); return

        self.current_training_dir = os.path.join(self.training_base_dir, f"{self.lang_code}-training-files")

        # Manejo de _ask_clean_directory:
        # Si retorna None (directorio no existe), crearlo.
        # Si retorna True (limpiado o usuario no quiso limpiar y se permite continuar), proceder.
        # Si retorna False (limpieza falló), abortar.
        clean_status = self._ask_clean_directory(self.current_training_dir)

        if clean_status is False:
            self.log_message("Limpieza de directorio de entrenamiento fallida. Abortando entrenamiento.")
            return

        try: # Asegurar que el directorio existe (sea porque se limpió, no se limpió, o no existía antes)
            os.makedirs(self.current_training_dir, exist_ok=True)
        except Exception as e:
            self.log_message(f"Error creando directorio de entrenamiento '{self.current_training_dir}': {e}")
            messagebox.showerror("Error Directorio", f"No se pudo crear directorio de entrenamiento: {e}", parent=self.root)
            return

        self.set_ui_state(False)
        threading.Thread(target=self.execute_training_pipeline, daemon=True).start()

    def execute_training_pipeline(self):
        try:
            self.log_message(f"--- Iniciando Pipeline: Idioma: {self.lang_code}, Modelo: {self.model_name} ---")
            prepared_files_info = self._prepare_training_data_files()
            if not prepared_files_info: self.root.after(0, self.set_ui_state, True); return
            if not self._run_tesseract_box_generation(prepared_files_info): self._training_failed("generación .box/.tr"); return
            if not self._create_font_properties_file(): self._training_failed("creación font_properties"); return
            if not self._run_unicharset_extraction(): self._training_failed("extracción unicharset"); return
            if not self._run_mftraining(): self._training_failed("mftraining"); return
            if not self._run_cntraining(): self._training_failed("cntraining"); return
            if not self._rename_training_files(): self._training_failed("renombrado archivos"); return
            if not self._combine_tessdata(): self._training_failed("combinación .traineddata"); return
            final_model_path = os.path.join(self.current_training_dir, f"{self.lang_code}.traineddata")
            output_model_path = os.path.join(self.training_base_dir, f"{self.model_name}.traineddata")
            try:
                shutil.copy(final_model_path, output_model_path)
                self.log_message(f"--- ENTRENAMIENTO COMPLETADO ---"); self.log_message(f"Modelo guardado en: {output_model_path}")
                self.root.after(0, messagebox.showinfo, "Entrenamiento Exitoso", f"Modelo '{output_model_path}' creado.", {"parent": self.root})
            except Exception as e: self.log_message(f"Error al copiar modelo final: {e}"); self._training_failed(f"copiar modelo a {output_model_path}"); return
        except Exception as e: self.log_message(f"Error CRÍTICO en pipeline: {e}", True); self.root.after(0, messagebox.showerror, "Error Crítico", f"Error inesperado: {e}", {"parent": self.root})
        finally: self.root.after(0, self.set_ui_state, True)

    def _training_failed(self, step_name):
        self.log_message(f"--- Entrenamiento FALLIDO: {step_name} ---")
        self.root.after(0, messagebox.showerror, "Error de Entrenamiento", f"Falló: {step_name}. Revisa log.", {"parent": self.root})

    def _prepare_training_data_files(self):
        self.log_message("Copiando archivos al directorio de entrenamiento y creando .gt.txt...")
        copied_files_info = []
        for original_image_path, text_content in self.image_paths_with_text.items():
            base_filename = os.path.basename(original_image_path)
            name_part, ext_part = os.path.splitext(base_filename)
            new_image_path_in_training_dir = os.path.join(self.current_training_dir, base_filename)
            gt_text_filepath = os.path.join(self.current_training_dir, f"{name_part}.gt.txt")
            try:
                shutil.copy(original_image_path, new_image_path_in_training_dir)
                with open(gt_text_filepath, 'w', encoding='utf-8') as f: f.write(text_content)
                self.log_message(f"Copiada al training dir: {base_filename}, Creado GT: {name_part}.gt.txt")
                copied_files_info.append({'image': new_image_path_in_training_dir, 'gt': gt_text_filepath, 'base': name_part, 'ext': ext_part})
            except Exception as e: self.log_message(f"Error procesando {base_filename} para entrenamiento: {e}"); self.root.after(0, messagebox.showerror, "Error", f"Error procesando {base_filename}: {e}", {"parent": self.root}); return None
        if not copied_files_info: self.log_message("No se prepararon archivos para entrenamiento."); return None
        self.log_message("Preparación de datos para entrenamiento completada."); return copied_files_info

    def _run_command(self, command_parts, working_dir, check_file=None):
        try:
            self.log_message(f"Ejecutando en '{working_dir}': {' '.join(command_parts)}")
            process = subprocess.Popen(command_parts, cwd=working_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace')
            stdout, stderr = process.communicate(timeout=600)
            if stdout: self.log_message(f"Salida '{os.path.basename(command_parts[0])}':\n{stdout.strip()}") # Corregido para mostrar basename
            if stderr: self.log_message(f"Errores '{os.path.basename(command_parts[0])}':\n{stderr.strip()}") # Corregido para mostrar basename
            if process.returncode != 0: self.log_message(f"Comando '{os.path.basename(command_parts[0])}' falló (cód: {process.returncode})"); return False
            if check_file and not os.path.exists(os.path.join(working_dir, check_file)):
                self.log_message(f"Archivo esperado '{check_file}' no encontrado tras '{os.path.basename(command_parts[0])}'."); return False
            return True
        except FileNotFoundError: self.log_message(f"Comando '{command_parts[0]}' no encontrado. ¿Tesseract/Poppler en PATH?"); self.root.after(0, messagebox.showerror, "Error Comando", f"No se encontró: {command_parts[0]}", {"parent": self.root}); return False
        except subprocess.TimeoutExpired: self.log_message(f"Comando '{command_parts[0]}' tomó mucho tiempo."); self.root.after(0, messagebox.showerror, "Error Comando", f"{command_parts[0]} excedió tiempo límite.", {"parent": self.root}); return False
        except Exception as e: self.log_message(f"Error ejecutando '{command_parts[0]}': {e}"); return False

    def _run_tesseract_box_generation(self, prepared_files_info):
        self.log_message("--- Generando archivos .box y .tr ---")
        for file_info in prepared_files_info:
            img_path = file_info['image']; base_name = file_info['base']
            cmd = ["tesseract", img_path, os.path.join(self.current_training_dir, base_name), "nobatch", "box.train"]
            if not self._run_command(cmd, self.current_training_dir, check_file=f"{base_name}.box"): return False
            if not os.path.exists(os.path.join(self.current_training_dir, f"{base_name}.tr")): self.log_message(f"Advertencia: {base_name}.tr no encontrado.")
        self.log_message(".box/.tr generados."); return True

    def _create_font_properties_file(self):
        self.log_message("--- Creando archivo font_properties ---")
        fp_path = os.path.join(self.current_training_dir, "font_properties")
        content = f"{self.font_name} 0 0 0 0 0"
        try:
            with open(fp_path, "w", encoding="utf-8") as f: f.write(content)
            self.log_message(f"font_properties creado."); return True
        except Exception as e: self.log_message(f"Error al crear font_properties: {e}"); return False

    def _run_unicharset_extraction(self):
        self.log_message("--- Extrayendo unicharset ---")
        box_files = glob.glob(os.path.join(self.current_training_dir, "*.box"))
        if not box_files: self.log_message("Error: No .box para unicharset_extractor."); return False
        cmd = ["unicharset_extractor"] + [os.path.basename(bf) for bf in box_files]
        return self._run_command(cmd, self.current_training_dir, check_file="unicharset")

    def _run_mftraining(self):
        self.log_message("--- Ejecutando mftraining ---")
        tr_files = glob.glob(os.path.join(self.current_training_dir, "*.tr"))
        if not tr_files: self.log_message("Error: No .tr para mftraining."); return False
        output_unicharset_name = f"{self.lang_code}.unicharset"
        cmd = ["mftraining", "-F", "font_properties", "-U", "unicharset", "-O", output_unicharset_name] + [os.path.basename(tf) for tf in tr_files]
        if not self._run_command(cmd, self.current_training_dir, check_file=output_unicharset_name): return False
        if not os.path.exists(os.path.join(self.current_training_dir, "inttemp")): self.log_message("Error: 'inttemp' no encontrado tras mftraining."); return False
        return True

    def _run_cntraining(self):
        self.log_message("--- Ejecutando cntraining ---")
        tr_files = glob.glob(os.path.join(self.current_training_dir, "*.tr"))
        if not tr_files: self.log_message("Error: No .tr para cntraining."); return False
        cmd = ["cntraining"] + [os.path.basename(tf) for tf in tr_files]
        return self._run_command(cmd, self.current_training_dir, check_file="normproto")

    def _rename_training_files(self):
        self.log_message("--- Renombrando archivos de entrenamiento ---")
        lang_unicharset_path = os.path.join(self.current_training_dir, f"{self.lang_code}.unicharset")
        if not os.path.exists(lang_unicharset_path):
            self.log_message(f"Error: {self.lang_code}.unicharset no encontrado.")
            plain_unicharset_path = os.path.join(self.current_training_dir, "unicharset")
            if os.path.exists(plain_unicharset_path):
                self.log_message(f"Fallback: Renombrando 'unicharset' a '{self.lang_code}.unicharset'")
                try: shutil.move(plain_unicharset_path, lang_unicharset_path)
                except Exception as e: self.log_message(f"Fallo al renombrar unicharset (fallback): {e}"); return False
            else: return False
        files_to_prefix = {"inttemp": True, "pffmtable": True, "shapetable": True, "normproto": True}
        for filename, required in files_to_prefix.items():
            original_path = os.path.join(self.current_training_dir, filename)
            prefixed_path = os.path.join(self.current_training_dir, f"{self.lang_code}.{filename}")
            if os.path.exists(original_path):
                try:
                    if os.path.exists(prefixed_path): os.remove(prefixed_path)
                    shutil.move(original_path, prefixed_path)
                    self.log_message(f"Renombrado: {filename} -> {self.lang_code}.{filename}")
                except Exception as e: self.log_message(f"Error al renombrar {filename}: {e}"); return False
            elif not os.path.exists(prefixed_path) and required:
                self.log_message(f"Error: Archivo requerido '{filename}' (o '{self.lang_code}.{filename}') no encontrado."); return False
        self.log_message("Archivos renombrados correctamente."); return True

    def _combine_tessdata(self):
        self.log_message("--- Combinando a .traineddata ---")
        cmd = ["combine_tessdata", f"{self.lang_code}."]
        return self._run_command(cmd, self.current_training_dir, check_file=f"{self.lang_code}.traineddata")

if __name__ == "__main__":
    root = tk.Tk()
    app = TesseractTrainerApp(root)
    if not PDF2IMAGE_AVAILABLE:
        app.log_message("ADVERTENCIA INICIAL: pdf2image o Poppler no están disponibles. Carga de PDFs fallará.")
        app.log_message("Por favor, instala pdf2image y Poppler (ver https://pypi.org/project/pdf2image/).")
    root.mainloop()
