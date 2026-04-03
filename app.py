import customtkinter as ctk
from tkinter import filedialog, messagebox
import fitz  # PyMuPDF
from PIL import Image
import io
import os
import threading
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import librosa
import soundfile as sf
import yt_dlp
from pdf2docx import Converter
from deep_translator import GoogleTranslator

class GeminiMasterTool(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Gemini Ultimate Master Tool 2026")
        self.geometry("1500x950")
        ctk.set_appearance_mode("dark")

        # --- STATO APPLICAZIONE ---
        self.pdf_doc = None
        self.pdf_path = None
        self.pdf_rotation = 0
        self.pdf_merge_list = []
        
        self.audio_series = None
        self.audio_sr = None
        self.sel_start = None
        self.sel_end = None

        # --- LAYOUT PRINCIPALE ---
        self.grid_columnconfigure(2, weight=1) # Area Visualizzazione
        self.grid_rowconfigure(0, weight=1)

        # 1. SIDEBAR (Controlli)
        self.sidebar = ctk.CTkScrollableFrame(self, width=320, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.setup_sidebar()

        # 2. MINIATURE PDF
        self.thumb_frame = ctk.CTkScrollableFrame(self, width=160, label_text="Pagine PDF")
        self.thumb_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        # 3. AREA VISUALIZZAZIONE
        self.main_view = ctk.CTkFrame(self, fg_color="#0a0a0a", corner_radius=15)
        self.main_view.grid(row=0, column=2, sticky="nsew", padx=10, pady=10)
        self.display_label = ctk.CTkLabel(self.main_view, text="Suite Multimediale 2026\nSeleziona un file a sinistra")
        self.display_label.pack(expand=True, fill="both")

    def add_section(self, text):
        ctk.CTkLabel(self.sidebar, text=text, font=("Arial", 13, "bold"), text_color="#3498db").pack(pady=(20, 5))

    def setup_sidebar(self):
        # --- PDF ---
        self.add_section("📄 GESTIONE PDF")
        ctk.CTkButton(self.sidebar, text="Apri PDF (Edit/Traduzione)", command=self.open_pdf).pack(pady=5, padx=10, fill="x")
        ctk.CTkButton(self.sidebar, text="+ Aggiungi a Unione", command=self.add_pdf_to_merge, fg_color="#16a085").pack(pady=2, padx=10, fill="x")
        self.lbl_merge = ctk.CTkLabel(self.sidebar, text="Coda PDF: 0", font=("Arial", 11))
        self.lbl_merge.pack()
        ctk.CTkButton(self.sidebar, text="Esegui Unione PDF", command=self.run_pdf_merge, fg_color="#27ae60").pack(pady=2, padx=10, fill="x")
        
        self.split_entry = ctk.CTkEntry(self.sidebar, placeholder_text="Range (es: 1-5)")
        self.split_entry.pack(pady=5, padx=10, fill="x")
        ctk.CTkButton(self.sidebar, text="Estrai Pagine", command=self.split_pdf).pack(pady=2, padx=10, fill="x")
        ctk.CTkButton(self.sidebar, text="Ruota 90°", command=self.rotate_pdf, fg_color="#d35400").pack(pady=2, padx=10, fill="x")
        ctk.CTkButton(self.sidebar, text="Converti in Word", command=self.pdf_to_word, fg_color="#34495e").pack(pady=2, padx=10, fill="x")

        # --- TRADUZIONE ---
        self.add_section("🌐 TRADUTTORE PDF")
        self.target_lang = ctk.StringVar(value="italian")
        ctk.CTkComboBox(self.sidebar, values=["italian", "english", "french", "german", "spanish"], variable=self.target_lang).pack(pady=5)
        ctk.CTkButton(self.sidebar, text="SALVA PDF TRADOTTO", command=self.translate_full_pdf, fg_color="#8e44ad").pack(pady=5, padx=10, fill="x")

        # --- AUDIO ---
        self.add_section("🎵 AUDIO EDITOR (VISUAL)")
        ctk.CTkButton(self.sidebar, text="Carica Audio", command=self.load_audio).pack(pady=5, padx=10, fill="x")
        self.btn_save_audio = ctk.CTkButton(self.sidebar, text="Salva Taglio Selezionato", command=self.save_audio_trim, fg_color="#e67e22", state="disabled")
        self.btn_save_audio.pack(pady=5, padx=10, fill="x")

        # --- YOUTUBE ---
        self.add_section("📺 YOUTUBE DOWNLOADER")
        self.yt_url = ctk.CTkEntry(self.sidebar, placeholder_text="Link YouTube...")
        self.yt_url.pack(pady=2, padx=10, fill="x")
        self.yt_fmt = ctk.StringVar(value="mp3")
        ctk.CTkComboBox(self.sidebar, values=["mp3", "wav"], variable=self.yt_fmt).pack(pady=2)
        self.btn_yt = ctk.CTkButton(self.sidebar, text="Scarica Audio", command=self.start_yt, fg_color="#c0392b")
        self.btn_yt.pack(pady=10, padx=10, fill="x")

    # --- LOGICA PDF ---
    def open_pdf(self):
        p = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if p:
            self.pdf_path = p
            self.pdf_doc = fitz.open(p)
            self.pdf_rotation = 0
            self.refresh_pdf_view()

    def refresh_pdf_view(self):
        for w in self.thumb_frame.winfo_children(): w.destroy()
        for i in range(len(self.pdf_doc)):
            pix = self.pdf_doc[i].get_pixmap(matrix=fitz.Matrix(0.1, 0.1))
            img = Image.open(io.BytesIO(pix.tobytes("ppm")))
            ctk_img = ctk.CTkImage(img, size=(100, 130))
            ctk.CTkButton(self.thumb_frame, text=f"P. {i+1}", image=ctk_img, compound="top", 
                          command=lambda p=i: self.show_pdf_page(p), fg_color="transparent").pack(pady=5)
        self.show_pdf_page(0)

    def show_pdf_page(self, idx):
        for w in self.main_view.winfo_children():
            if w != self.display_label: w.destroy()
        page = self.pdf_doc[idx]
        pix = page.get_pixmap(matrix=fitz.Matrix(1.2, 1.2).prerotate(self.pdf_rotation))
        img = Image.open(io.BytesIO(pix.tobytes("ppm")))
        img.thumbnail((850, 850))
        ctk_img = ctk.CTkImage(img, size=img.size)
        self.display_label.configure(image=ctk_img, text="")
        self.display_label.image = ctk_img

    def rotate_pdf(self):
        if self.pdf_doc: self.pdf_rotation = (self.pdf_rotation + 90) % 360; self.show_pdf_page(0)

    def translate_full_pdf(self):
        if not self.pdf_path: return
        out = filedialog.asksaveasfilename(defaultextension=".pdf")
        if out:
            doc_orig = fitz.open(self.pdf_path); doc_dest = fitz.open()
            translator = GoogleTranslator(source='auto', target=self.target_lang.get())
            for page in doc_orig:
                new_page = doc_dest.new_page(width=page.rect.width, height=page.rect.height)
                for b in page.get_text("blocks"):
                    if b[4].strip():
                        trad = translator.translate(b[4][:4500])
                        new_page.insert_text((b[0], b[1]), trad, fontsize=9)
            doc_dest.save(out); doc_dest.close(); messagebox.showinfo("OK", "Traduzione completata!")

    # --- LOGICA AUDIO (STILE AUDACITY) ---
    def load_audio(self):
        p = filedialog.askopenfilename(filetypes=[("Audio", "*.mp3 *.wav *.ogg")])
        if p:
            self.audio_series, self.audio_sr = librosa.load(p, sr=None)
            self.sel_start, self.sel_end = None, None
            self.plot_audio_visual()

    def plot_audio_visual(self):
        for w in self.main_view.winfo_children():
            if w != self.display_label: w.destroy()
        self.display_label.configure(image=None, text="")
        
        red = self.audio_series[::100]
        time = np.linspace(0, len(self.audio_series)/self.audio_sr, num=len(red))
        
        fig, ax = plt.subplots(figsize=(10, 4), facecolor='#0a0a0a')
        ax.plot(time, red, color='#3498db', linewidth=0.5)
        ax.set_facecolor('#0a0a0a')
        ax.axis('off')
        
        canvas = FigureCanvasTkAgg(fig, master=self.main_view)
        canvas.draw(); canvas.get_tk_widget().pack(expand=True, fill="both")
        
        # Click per tagliare
        fig.canvas.mpl_connect('button_press_event', lambda e: self.on_audio_click(e, ax, canvas))

    def on_audio_click(self, event, ax, canvas):
        if event.inaxes != ax: return
        if self.sel_start is None:
            self.sel_start = event.xdata
            ax.axvline(x=self.sel_start, color='green', linestyle='--')
        elif self.sel_end is None:
            self.sel_end = event.xdata
            ax.axvline(x=self.sel_end, color='red', linestyle='--')
            self.btn_save_audio.configure(state="normal")
            if self.sel_start > self.sel_end: self.sel_start, self.sel_end = self.sel_end, self.sel_start
        else:
            self.sel_start, self.sel_end = event.xdata, None
            self.btn_save_audio.configure(state="disabled")
            self.plot_audio_visual()
            return
        canvas.draw()

    def save_audio_trim(self):
        idx_s, idx_e = int(self.sel_start * self.audio_sr), int(self.sel_end * self.audio_sr)
        trimmed = self.audio_series[idx_s:idx_e]
        out = filedialog.asksaveasfilename(defaultextension=".wav")
        if out: sf.write(out, trimmed, self.audio_sr); messagebox.showinfo("OK", "Taglio salvato!")

    # --- LOGICA YOUTUBE ---
    def start_yt(self):
        url = self.yt_url.get()
        if url:
            self.btn_yt.configure(state="disabled", text="Scaricando...")
            threading.Thread(target=self.yt_worker, args=(url, self.yt_fmt.get()), daemon=True).start()

    def yt_worker(self, url, fmt):
        folder = filedialog.askdirectory()
        if folder:
            opts = {'format': 'bestaudio', 'outtmpl': f'{folder}/%(title)s.%(ext)s', 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': fmt}]}
            with yt_dlp.YoutubeDL(opts) as ydl: ydl.download([url])
            self.after(0, lambda: messagebox.showinfo("OK", "Download completato!"))
        self.after(0, lambda: self.btn_yt.configure(state="normal", text="Scarica Audio"))

    # Funzioni di supporto PDF
    def add_pdf_to_merge(self): self.pdf_merge_list.extend(filedialog.askopenfilenames(filetypes=[("PDF", "*.pdf")])); self.lbl_merge.configure(text=f"Coda PDF: {len(self.pdf_merge_list)}")
    def run_pdf_merge(self):
        if len(self.pdf_merge_list) < 2: return
        out = filedialog.asksaveasfilename(defaultextension=".pdf")
        if out:
            merger = fitz.open()
            for f in self.pdf_merge_list:
                with fitz.open(f) as src: merger.insert_pdf(src)
            merger.save(out); messagebox.showinfo("OK", "Uniti!"); self.pdf_merge_list = []
    def split_pdf(self):
        try:
            s, e = map(int, self.split_entry.get().split('-'))
            out = filedialog.asksaveasfilename(defaultextension=".pdf")
            if out: new = fitz.open(); new.insert_pdf(self.pdf_doc, from_page=s-1, to_page=e-1); new.save(out); messagebox.showinfo("OK", "Estratto!")
        except: pass
    def pdf_to_word(self):
        if self.pdf_path: out = filedialog.asksaveasfilename(defaultextension=".docx"); cv = Converter(self.pdf_path); cv.convert(out); cv.close(); messagebox.showinfo("OK", "Word creato!")

if __name__ == "__main__":
    app = GeminiMasterTool(); app.mainloop()
