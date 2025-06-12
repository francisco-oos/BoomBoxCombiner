import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import datetime

class BoomBoxCombinerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("BoomBox Combiner")

        self.files = []  # Lista con los archivos seleccionados
        self.sort_order = tk.StringVar(value="desc")  # Orden de fecha descendente por defecto

        self.setup_ui()  # Configura la interfaz inicial

    def setup_ui(self):
        """
        Configura la interfaz principal con botones y lista de archivos
        """
        frm = ttk.Frame(self.root, padding=10)
        frm.grid(sticky='nsew')

        # Etiqueta para archivos seleccionados
        ttk.Label(frm, text="Archivos seleccionados:").grid(column=0, row=0, sticky='w')

        # Frame para contener la lista con scrollbars
        listbox_frame = ttk.Frame(frm)
        listbox_frame.grid(column=0, row=1, columnspan=2, pady=5, sticky='nsew')

        # Scrollbar vertical para la lista
        y_scroll = ttk.Scrollbar(listbox_frame, orient='vertical')
        y_scroll.pack(side='right', fill='y')
        # Scrollbar horizontal para la lista
        x_scroll = ttk.Scrollbar(listbox_frame, orient='horizontal')
        x_scroll.pack(side='bottom', fill='x')

        # Listbox que muestra los archivos seleccionados
        self.listbox = tk.Listbox(
            listbox_frame, width=80, height=10,
            yscrollcommand=y_scroll.set,
            xscrollcommand=x_scroll.set
        )
        self.listbox.pack(side='left', fill='both', expand=True)

        # Configuramos las scrollbars para que funcionen con la listbox
        y_scroll.config(command=self.listbox.yview)
        x_scroll.config(command=self.listbox.xview)

        # Botones principales
        ttk.Button(frm, text="Seleccionar archivos CSV", command=self.select_files).grid(column=0, row=2, sticky='w', pady=5)
        ttk.Button(frm, text="Combinar y exportar", command=self.combine_and_export).grid(column=1, row=2, sticky='e', pady=5)
        ttk.Button(frm, text="Eliminar archivo seleccionado", command=self.delete_selected_file).grid(column=0, row=3, sticky='w', pady=5)
        ttk.Button(frm, text="Previsualizar combinación", command=self.preview_combined_file).grid(column=1, row=3, sticky='e', pady=5)

        # Radio buttons para orden de fechas
        ttk.Radiobutton(frm, text="Reciente primero", variable=self.sort_order, value="desc").grid(column=0, row=4, sticky='w')
        ttk.Radiobutton(frm, text="Antiguo primero", variable=self.sort_order, value="asc").grid(column=1, row=4, sticky='e')

        # Ajustamos expansión dinámica
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        frm.grid_rowconfigure(1, weight=1)
        frm.grid_columnconfigure(0, weight=1)

    def select_files(self):
        """
        Permite seleccionar múltiples archivos CSV y los añade a la lista
        """
        new_files = list(filedialog.askopenfilenames(filetypes=[("CSV Files", "*.csv")]))
        self.files.extend(new_files)
        self.refresh_listbox()

    def delete_selected_file(self):
        """
        Elimina el archivo seleccionado de la lista en la ventana principal
        """
        selected_index = self.listbox.curselection()
        if selected_index:
            del self.files[selected_index[0]]
            self.refresh_listbox()
        else:
            messagebox.showwarning("Advertencia", "Seleccione un archivo para eliminar.")

    def refresh_listbox(self):
        """
        Actualiza la lista visual de archivos seleccionados en la ventana principal
        """
        self.listbox.delete(0, tk.END)
        for f in self.files:
            self.listbox.insert(tk.END, f)

    def combine_files(self):
        """
        Combina los archivos CSV seleccionados en un solo DataFrame,
        eliminando la columna 'ID' si existe y ordenando por 'Time'
        """
        if not self.files:
            messagebox.showwarning("Advertencia", "No se han seleccionado archivos.")
            return None

        dfs = []
        columnas_finales = None

        for file in self.files:
            df = pd.read_csv(file, dtype=str)
            if 'ID' in df.columns:
                df.drop(columns=['ID'], inplace=True)

            if columnas_finales is None:
                columnas_finales = df.columns.tolist()
            else:
                # Alinea columnas para evitar errores
                df = df.reindex(columns=columnas_finales, fill_value="")

            dfs.append(df)

        combined_df = pd.concat(dfs, ignore_index=True)

        # Ordena por la columna 'Time' según la preferencia seleccionada
        if "Time" in combined_df.columns:
            original_time = combined_df["Time"].copy()
            parsed_time = pd.to_datetime(original_time, format="%Y-%m-%d %H:%M:%S.%f", errors="coerce")
            combined_df = combined_df.assign(_parsed_time=parsed_time)
            combined_df = combined_df.sort_values(by="_parsed_time", ascending=(self.sort_order.get() == "asc"))
            combined_df = combined_df.drop(columns=["_parsed_time"])
            combined_df["Time"] = original_time.loc[combined_df.index]

        return combined_df

    def combine_and_export(self):
        """
        Combina los archivos y exporta el CSV combinado a un archivo seleccionado por el usuario
        """
        try:
            combined_df = self.combine_files()
            if combined_df is None:
                return

            fecha = datetime.datetime.now().strftime("%Y%m%d")
            save_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                initialfile=f"BoomBox-{fecha}.csv"
            )

            if save_path:
                combined_df.to_csv(save_path, index=False, encoding='utf-8')
                messagebox.showinfo("Éxito", f"Archivo exportado:\n{save_path}")

        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error:\n{e}")

    def preview_combined_file(self):
        """
        Muestra una ventana con la vista previa del archivo combinado.
        Permite buscar, filtrar, eliminar filas, copiar texto y guardar el filtro.
        """
        try:
            combined_df = self.combine_files()
            if combined_df is None:
                return

            self.preview_df_original = combined_df.copy()
            self.preview_df_filtered = combined_df.copy()

            # Creamos ventana de vista previa
            preview_window = tk.Toplevel(self.root)
            self.preview_window = preview_window  # Guardamos referencia para diálogos modales
            preview_window.title("Vista previa del archivo combinado")
            preview_window.geometry("1100x700")

            main_frame = ttk.Frame(preview_window, padding=5)
            main_frame.pack(expand=True, fill='both')

            # Frame para herramientas (buscar, botones)
            tools_frame = ttk.Frame(main_frame)
            tools_frame.pack(fill='x', pady=5)

            ttk.Label(tools_frame, text="Buscar:").pack(side='left')

            self.search_var = tk.StringVar()
            search_entry = ttk.Entry(tools_frame, textvariable=self.search_var)
            search_entry.pack(side='left', fill='x', expand=True, padx=5)
            search_entry.bind("<KeyRelease>", self.filter_treeview)

            clear_btn = ttk.Button(tools_frame, text="Limpiar filtro", command=self.clear_filter)
            clear_btn.pack(side='left', padx=5)

            export_btn = ttk.Button(tools_frame, text="Exportar filtrado", command=self.export_filtered)
            export_btn.pack(side='left', padx=5)

            # Botón para eliminar filas seleccionadas
            delete_btn = ttk.Button(tools_frame, text="Eliminar filas seleccionadas", command=self.delete_selected_rows)
            delete_btn.pack(side='left', padx=5)

            # Botón para guardar el DataFrame filtrado directamente
            save_btn = ttk.Button(tools_frame, text="Guardar filtrado", command=self.export_filtered)
            save_btn.pack(side='left', padx=5)

            self.count_label = ttk.Label(tools_frame, text="")
            self.count_label.pack(side='right')

            # Frame para el Treeview con scrollbars
            tree_frame = ttk.Frame(main_frame)
            tree_frame.pack(expand=True, fill='both')

            y_scroll = ttk.Scrollbar(tree_frame, orient='vertical')
            y_scroll.pack(side='right', fill='y')
            x_scroll = ttk.Scrollbar(tree_frame, orient='horizontal')
            x_scroll.pack(side='bottom', fill='x')

            self.tree = ttk.Treeview(tree_frame, show='headings',
                                     yscrollcommand=y_scroll.set,
                                     xscrollcommand=x_scroll.set)

            self.tree.pack(expand=True, fill='both')

            y_scroll.config(command=self.tree.yview)
            x_scroll.config(command=self.tree.xview)

            # Definimos las columnas (agregamos columna N°)
            columns = list(combined_df.columns)
            columns.insert(0, "#")
            self.tree["columns"] = columns

            self.tree.column("#", width=50, anchor='center')
            self.tree.heading("#", text="N°")

            for col in combined_df.columns:
                self.tree.column(col, anchor='w')
                self.tree.heading(col, text=col)

            # Configuramos el tag para filas duplicadas en 'Time' con color amarillo
            self.tree.tag_configure('highlight_duplicate', background='yellow')

            # Agregamos menú contextual para copiar texto
            self.tree.bind("<Button-3>", self.show_context_menu)
            self.context_menu = tk.Menu(self.root, tearoff=0)
            self.context_menu.add_command(label="Copiar texto", command=self.copy_cell_text)
            self.right_click_info = {"row": None, "col": None}

            # Cargamos datos en el Treeview
            self.load_treeview(self.preview_df_filtered)
            self.update_count_label()

        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al generar la vista previa:\n{e}")

    def load_treeview(self, df):
        """
        Carga el DataFrame en el Treeview.
        Resalta filas que tengan valores duplicados en la columna 'Time' pintándolas de amarillo.
        """
        self.tree.delete(*self.tree.get_children())

        # Detectamos filas con valores duplicados en 'Time'
        duplicates_mask = df.duplicated(subset=['Time'], keep=False)

        df_reset = df.reset_index(drop=True)

        for i, row in df_reset.iterrows():
            values = [i + 1] + list(row.astype(str))

            # Si 'Time' está duplicado, pintamos la fila de amarillo
            if duplicates_mask.iloc[i]:
                self.tree.insert("", "end", values=values, tags=('highlight_duplicate',))
            else:
                self.tree.insert("", "end", values=values)

    def filter_treeview(self, event=None):
        """
        Filtra filas según texto ingresado en la búsqueda,
        actualiza el Treeview y la etiqueta de conteo.
        """
        filtro = self.search_var.get().lower()

        if filtro == "":
            self.preview_df_filtered = self.preview_df_original.copy()
        else:
            mask = self.preview_df_original.apply(
                lambda row: row.astype(str).str.lower().str.contains(filtro).any(),
                axis=1
            )
            self.preview_df_filtered = self.preview_df_original[mask]

        self.load_treeview(self.preview_df_filtered)
        self.update_count_label()

    def clear_filter(self):
        """
        Limpia filtro de búsqueda y actualiza vista
        """
        self.search_var.set("")
        self.filter_treeview()

    def update_count_label(self):
        """
        Actualiza etiqueta con conteo de filas visibles y totales
        """
        visibles = len(self.preview_df_filtered)
        total = len(self.preview_df_original)
        self.count_label.config(text=f"Mostrando {visibles} de {total} filas")

    def export_filtered(self):
        """
        Exporta el DataFrame filtrado a CSV mediante diálogo guardar archivo.
        """
        if self.preview_df_filtered.empty:
            messagebox.showinfo("Exportar", "No hay datos para exportar.", parent=self.preview_window)
            return

        fecha = datetime.datetime.now().strftime("%Y%m%d")
        default_name = f"BoomBox-{fecha}-filtrado.csv"

        save_path = filedialog.asksaveasfilename(
            parent=self.preview_window,
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=default_name
        )

        if save_path:
            try:
                self.preview_df_filtered.to_csv(save_path, index=False, encoding='utf-8')
                messagebox.showinfo("Exportar", f"Archivo exportado:\n{save_path}", parent=self.preview_window)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo exportar el archivo:\n{e}", parent=self.preview_window)

    def delete_selected_rows(self):
        """
        Elimina las filas seleccionadas del Treeview y del DataFrame original,
        confirmando la eliminación con diálogo modal ligado a la ventana de vista previa
        """
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("Advertencia", "Seleccione al menos una fila para eliminar.", parent=self.preview_window)
            return

        # Confirmamos la eliminación con diálogo modal ligado a la ventana preview
        if not messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Está seguro de eliminar {len(selected_items)} fila(s)?",
            parent=self.preview_window
        ):
            return

        indices_to_remove = []
        for item in selected_items:
            values = self.tree.item(item, "values")
            if values:
                try:
                    # Convertimos número de fila a índice base 0
                    row_number = int(values[0]) - 1
                    indices_to_remove.append(row_number)
                except:
                    pass

        # Ordenamos indices descendente para eliminar sin alterar índices aún por eliminar
        indices_to_remove = sorted(set(indices_to_remove), reverse=True)

        for idx in indices_to_remove:
            if 0 <= idx < len(self.preview_df_original):
                self.preview_df_original = self.preview_df_original.drop(self.preview_df_original.index[idx])

        self.preview_df_original.reset_index(drop=True, inplace=True)

        # Aplicamos filtro actual para mantener coherencia
        filtro = self.search_var.get().lower()
        if filtro == "":
            self.preview_df_filtered = self.preview_df_original.copy()
        else:
            mask = self.preview_df_original.apply(
                lambda row: row.astype(str).str.lower().str.contains(filtro).any(),
                axis=1
            )
            self.preview_df_filtered = self.preview_df_original[mask]

        # Recargamos Treeview y actualizamos contador
        self.load_treeview(self.preview_df_filtered)
        self.update_count_label()

    def show_context_menu(self, event):
        """
        Muestra menú contextual al hacer clic derecho sobre una celda del Treeview,
        guarda la fila y columna seleccionada para la acción copiar.
        """
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            row_id = self.tree.identify_row(event.y)
            col = self.tree.identify_column(event.x)
            self.right_click_info = {"row": row_id, "col": col}
            self.context_menu.tk_popup(event.x_root, event.y_root)
        else:
            self.context_menu.unpost()

    def copy_cell_text(self):
        """
        Copia al portapapeles el texto de la celda seleccionada en el menú contextual.
        """
        row_id = self.right_click_info.get("row")
        col = self.right_click_info.get("col")
        if not row_id or not col:
            return

        col_index = int(col.replace("#", "")) - 1  # Ajustamos índice 0-based
        if col_index < 0:
            return

        item = self.tree.item(row_id)
        values = item.get("values", [])
        if col_index >= len(values):
            return

        text_to_copy = values[col_index]
        self.root.clipboard_clear()
        self.root.clipboard_append(text_to_copy)
        #messagebox.showinfo("Copiar", f"Texto copiado:\n{text_to_copy}", parent=self.preview_window)


if __name__ == "__main__":
    root = tk.Tk()
    app = BoomBoxCombinerApp(root)
    root.mainloop()
