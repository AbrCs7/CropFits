import tkinter as tk
from tkinter import filedialog, messagebox
from astropy.io import fits
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize, LogNorm
import numpy as np
from matplotlib.widgets import RectangleSelector


class FITSViewer:
    def __init__(self, master):
        self.master = master
        self.master.title("FITS Viewer")
        self.file_path = None
        self.header = None
        self.image_data = None
        self.fig, self.ax = plt.subplots()
        self.norm_type = 'linear'
        self.vmin_percentile = 5
        self.vmax_percentile = 95
        self.img = None
        self.cbar = None
        self.roi_coords = None
        self.rect_selector = None  # Adicionando a inicialização do retângulo selecionador

        self.create_widgets()


    def create_widgets(self):
        self.open_button = tk.Button(self.master, text="Open FITS", command=self.open_fits)
        self.open_button.pack()

        self.norm_button = tk.Button(self.master, text="Adjust Normalization", command=self.adjust_normalization)
        self.norm_button.pack()

        self.header_button = tk.Button(self.master, text="Show Header", command=self.show_header)
        self.header_button.pack()

        self.roi_button = tk.Button(self.master, text="Set ROI", command=self.set_roi)
        self.roi_button.pack()

        self.save_roi_button = tk.Button(self.master, text="Save ROI as FITS", command=self.save_roi)
        self.save_roi_button.pack()

        self.freq_button = tk.Button(self.master, text="Show Frequency", command=self.show_frequency)
        self.freq_button.pack()

        self.clean_beam_button = tk.Button(self.master, text="Show Clean Beam", command=self.show_clean_beam)
        self.clean_beam_button.pack()

        self.pixel_scale_button = tk.Button(self.master, text="Show Pixel Scale", command=self.show_pixel_scale)
        self.pixel_scale_button.pack()

    def open_fits(self):
        self.file_path = filedialog.askopenfilename(filetypes=[("FITS files", "*.fits")])
        if self.file_path:
            with fits.open(self.file_path) as hdul:
                self.header = hdul[0].header
                self.image_data = hdul[0].data.squeeze()  # Remover dimensões unitárias
                print("Shape of loaded data:", self.image_data.shape)  # Mensagem de depuração
                self.display_image()


    def display_image(self):
        if self.image_data is not None:
            if self.img:
                self.img.remove()
                self.img = None

            # Check if all values are positive for log normalization
            if self.norm_type == 'log' and np.any(self.image_data <= 0):
                messagebox.showerror("Error", "Log normalization requires all values to be positive.")
                return

            vmin, vmax = self.vmin_percentile, self.vmax_percentile
            if self.norm_type == 'log':
                norm = LogNorm(vmin=np.percentile(self.image_data, vmin), vmax=np.percentile(self.image_data, vmax))
            else:
                norm = Normalize(vmin=np.percentile(self.image_data, vmin), vmax=np.percentile(self.image_data, vmax))

            self.img = self.ax.imshow(self.image_data, cmap='rainbow', origin='lower', norm=norm)
            self.ax.set_xlabel('Right Ascension')
            self.ax.set_ylabel('Declination')
            if self.img:
                if self.cbar:
                    try:
                        self.cbar.remove()
                    except Exception as e:
                        print("Error removing colorbar:", e)
                    self.cbar = None
                self.cbar = self.fig.colorbar(self.img, ax=self.ax, orientation='vertical')
                self.cbar.set_label('Intensity (Jy/beam)')
            plt.show()






    def adjust_normalization(self):
        norm_window = tk.Toplevel(self.master)
        norm_window.title("Adjust Normalization")

        tk.Label(norm_window, text="Normalization Type:").grid(row=0, column=0, sticky="w")

        self.norm_type_var = tk.StringVar(value=self.norm_type)
        tk.Radiobutton(norm_window, text="Linear", variable=self.norm_type_var, value='linear').grid(row=0, column=1, sticky="w")
        tk.Radiobutton(norm_window, text="Log", variable=self.norm_type_var, value='log').grid(row=0, column=2, sticky="w")

        tk.Label(norm_window, text="Vmin Percentile:").grid(row=1, column=0, sticky="w")
        self.vmin_entry = tk.Entry(norm_window)
        self.vmin_entry.insert(0, str(self.vmin_percentile))
        self.vmin_entry.grid(row=1, column=1, sticky="w")

        tk.Label(norm_window, text="Vmax Percentile:").grid(row=2, column=0, sticky="w")
        self.vmax_entry = tk.Entry(norm_window)
        self.vmax_entry.insert(0, str(self.vmax_percentile))
        self.vmax_entry.grid(row=2, column=1, sticky="w")

        tk.Button(norm_window, text="Apply", command=self.apply_normalization).grid(row=3, column=0, columnspan=3)

    def apply_normalization(self):
        self.norm_type = self.norm_type_var.get()
        try:
            self.vmin_percentile = float(self.vmin_entry.get())
            self.vmax_percentile = float(self.vmax_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid percentile values")
            return

        if not 0 <= self.vmin_percentile <= 100 or not 0 <= self.vmax_percentile <= 100:
            messagebox.showerror("Error", "Percentile values must be between 0 and 100")
            return

        # Verifica se a imagem foi exibida anteriormente antes de tentar remover a barra de cores
        if self.img:
            # Exibe a imagem com a nova normalização
            self.display_image()

            # Verifica se a barra de cores foi criada anteriormente e, se sim, a remove
            if self.cbar:
                self.cbar.remove()



    def show_header(self):
        if self.header:
            header_window = tk.Toplevel(self.master)
            header_window.title("FITS Header")

            header_text = tk.Text(header_window)
            header_text.insert(tk.END, str(self.header))
            header_text.pack(expand=True, fill=tk.BOTH)

            scrollbar = tk.Scrollbar(header_window, orient=tk.VERTICAL, command=header_text.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            header_text.config(yscrollcommand=scrollbar.set)
        else:
            messagebox.showinfo("Header", "No FITS header available.")

    def set_roi(self):
        if self.image_data is not None:
            if hasattr(self, 'rect_selector') and self.rect_selector is not None:
                self.rect_selector.set_active(False)
                del self.rect_selector

            self.rect_selector = RectangleSelector(self.ax, self.on_select,
                                                   minspanx=5, minspany=5,
                                                   spancoords='pixels', interactive=True)
            plt.show()


    def on_select(self, eclick, erelease):
        x1, y1 = int(eclick.xdata), int(eclick.ydata)
        x2, y2 = int(erelease.xdata), int(erelease.ydata)
        self.roi_coords = (x1, x2, y1, y2)

    

    def save_roi(self):
        if self.roi_coords and self.image_data is not None:
            x1, x2, y1, y2 = self.roi_coords
            roi_data = self.image_data[y1:y2, x1:x2]  # Invertendo y1 e y2 para cortar corretamente
            roi_header = self.header.copy()
            roi_header['NAXIS1'] = roi_data.shape[1]
            roi_header['NAXIS2'] = roi_data.shape[0]
            output_file = filedialog.asksaveasfilename(defaultextension=".fits", filetypes=[("FITS files", "*.fits")])
            if output_file:
                fits.writeto(output_file, roi_data, roi_header, overwrite=True)
                messagebox.showinfo("Save ROI", f"ROI saved as {output_file}")

    def show_frequency(self):
        if self.header and 'RESTFRQ' in self.header:
            messagebox.showinfo("Frequency", f"Frequency: {self.header['RESTFRQ']} Hz")
        else:
            messagebox.showinfo("Frequency", "No frequency information available.")

    def show_clean_beam(self):
        if self.header and all(k in self.header for k in ['BMAJ', 'BMIN', 'BPA']):
            messagebox.showinfo("Clean Beam", f"Clean Beam: Major={self.header['BMAJ']} deg, Minor={self.header['BMIN']} deg, PA={self.header['BPA']} deg")
        else:
            messagebox.showinfo("Clean Beam", "No clean beam information available.")

    def show_pixel_scale(self):
        if self.header and 'CDELT1' in self.header and 'CDELT2' in self.header:
            scale_x = self.header['CDELT1'] * 3600  # Convert from degrees to arcseconds
            scale_y = self.header['CDELT2'] * 3600  # Convert from degrees to arcseconds
            messagebox.showinfo("Pixel Scale", f"Pixel Scale: {scale_x} arcsec/pixel, {scale_y} arcsec/pixel")
        else:
            messagebox.showinfo("Pixel Scale", "No pixel scale information available.")

def main():
    root = tk.Tk()
    app = FITSViewer(root)
    root.mainloop()

if __name__ == "__main__":
    main()


