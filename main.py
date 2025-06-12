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
        new_files = list(filedialog.askopenfilenames(filetypes=[("CSV Files", "*.csv")]))
        self.files.extend(new_files)
        self.refresh_listbox()

    def delete_selected_file(self):
        selected_index = self.listbox.curselection()
        if selected_index:
            del self.files[selected_index[0]]
            self.refresh_listbox()
        else:
            messagebox.showwarning("Advertencia", "Seleccione un archivo para eliminar.")

    def refresh_listbox(self):
        self.listbox.delete(0, tk.END)
        for f in self.files:
            self.listbox.insert(tk.END, f)

    def combine_files(self):
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
                df = df.reindex(columns=columnas_finales, fill_value="")

            dfs.append(df)

        combined_df = pd.concat(dfs, ignore_index=True)

        if "Time" in combined_df.columns:
            original_time = combined_df["Time"].copy()
            parsed_time = pd.to_datetime(original_time, format="%Y-%m-%d %H:%M:%S.%f", errors="coerce")
            combined_df = combined_df.assign(_parsed_time=parsed_time)
            combined_df = combined_df.sort_values(by="_parsed_time", ascending=(self.sort_order.get() == "asc"))
            combined_df = combined_df.drop(columns=["_parsed_time"])
            combined_df["Time"] = original_time.loc[combined_df.index]

        return combined_df

    def combine_and_export(self):
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
        try:
            combined_df = self.combine_files()
            if combined_df is None:
                return

            self.preview_df_original = combined_df.copy()
            self.preview_df_filtered = combined_df.copy()

            preview_window = tk.Toplevel(self.root)
            preview_window.title("Vista previa del archivo combinado")
            preview_window.geometry("1100x700")

            main_frame = ttk.Frame(preview_window, padding=5)
            main_frame.pack(expand=True, fill='both')

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

            self.count_label = ttk.Label(tools_frame, text="")
            self.count_label.pack(side='right')

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

            columns = list(combined_df.columns)
            columns.insert(0, "#")
            self.tree["columns"] = columns

            self.tree.column("#", width=50, anchor='center')
            self.tree.heading("#", text="N°")

            for col in combined_df.columns:
                self.tree.column(col, anchor='w')
                self.tree.heading(col, text=col)

            self.load_treeview(self.preview_df_filtered)
            self.update_count_label()

        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al generar la vista previa:\n{e}")

    def load_treeview(self, df):
        self.tree.delete(*self.tree.get_children())

        # Reseteamos índice para numerar bien desde 1 y en orden
        df_reset = df.reset_index(drop=True)

        for i, row in df_reset.iterrows():
            self.tree.insert("", "end", values=[i+1] + list(row))

    def filter_treeview(self, event=None):
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
        self.search_var.set("")
        self.filter_treeview()

    def update_count_label(self):
        visibles = len(self.preview_df_filtered)
        total = len(self.preview_df_original)
        self.count_label.config(text=f"Mostrando {visibles} de {total} filas")

    def export_filtered(self):
        if self.preview_df_filtered.empty:
            messagebox.showinfo("Exportar", "No hay datos para exportar.")
            return

        try:
            fecha = datetime.datetime.now().strftime("%Y%m%d")
            save_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                initialfile=f"BoomBox-Filtered-{fecha}.csv"
            )

            if save_path:
                self.preview_df_filtered.to_csv(save_path, index=False, encoding='utf-8')
                messagebox.showinfo("Éxito", f"Archivo exportado:\n{save_path}")

        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al exportar:\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = BoomBoxCombinerApp(root)
    root.mainloop()
