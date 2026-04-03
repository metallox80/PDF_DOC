import streamlit as st
import fitz
from PIL import Image
import io
import os
from pdf2docx import Converter
from deep_translator import GoogleTranslator
import librosa
import soundfile as sf
import numpy as np
import matplotlib.pyplot as plt
import yt_dlp

st.set_page_config(page_title="Barco WEB TOOL", layout="wide")

st.title("🚀 Gemini Ultimate Web Tool 2026")

# Sidebar
menu = st.sidebar.radio("Scegli Funzione", ["📄 PDF Manager", "🌐 Traduttore PDF", "🎵 Audio Editor", "📺 YouTube Downloader"])

# --- SEZIONE PDF MANAGER ---
if menu == "📄 PDF Manager":
    st.header("Gestione PDF")
    uploaded_pdf = st.file_uploader("Carica un PDF", type="pdf")
    if uploaded_pdf:
        with open("temp.pdf", "wb") as f:
            f.write(uploaded_pdf.getbuffer())
        col1, col2 = st.columns([1, 2])
        with col1:
            if st.button("Converti in Word"):
                cv = Converter("temp.pdf")
                cv.convert("output.docx")
                cv.close()
                with open("output.docx", "rb") as f:
                    st.download_button("📥 Scarica Word", f, "documento.docx")
        with col2:
            doc = fitz.open("temp.pdf")
            page_num = st.slider("Pagina", 1, len(doc), 1)
            pix = doc[page_num-1].get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
            st.image(Image.open(io.BytesIO(pix.tobytes("png"))))

# --- SEZIONE TRADUTTORE ---
elif menu == "🌐 Traduttore PDF":
    st.header("Traduttore PDF")
    up_trans = st.file_uploader("Carica PDF", type="pdf")
    lang = st.selectbox("Lingua", ["it", "en", "fr", "es"])
    if up_trans and st.button("Traduci"):
        doc = fitz.open(stream=up_trans.read(), filetype="pdf")
        out_doc = fitz.open()
        translator = GoogleTranslator(source='auto', target=lang)
        for page in doc:
            new_page = out_doc.new_page(width=page.rect.width, height=page.rect.height)
            for b in page.get_text("blocks"):
                if b[4].strip():
                    trad = translator.translate(b[4][:4000])
                    new_page.insert_text((b[0], b[1]), trad, fontsize=9)
        buf = io.BytesIO()
        out_doc.save(buf)
        st.download_button("📥 Scarica Traduzione", buf.getvalue(), "tradotto.pdf")

# --- SEZIONE AUDIO ---
elif menu == "🎵 Audio Editor":
    st.header("Audio Editor")
    up_audio = st.file_uploader("Carica audio", type=["mp3", "wav"])
    if up_audio:
        y, sr = librosa.load(up_audio, sr=None)
        duration = len(y) / sr
        start_t, end_t = st.slider("Taglio (sec)", 0.0, duration, (0.0, duration))
        if st.button("Taglia e Scarica"):
            trimmed = y[int(start_t*sr):int(end_t*sr)]
            buf = io.BytesIO()
            sf.write(buf, trimmed, sr, format='WAV')
            st.download_button("📥 Scarica WAV", buf.getvalue(), "taglio.wav")

# --- SEZIONE YOUTUBE (VERSIONE FIX 403) ---
elif menu == "📺 YouTube Downloader":
    st.header("Scarica Audio da YouTube")
    url = st.text_input("Incolla il link del video YouTube:")
    format_choice = st.radio("Scegli formato uscita:", ["mp3", "wav"])
    
    if url and st.button("Estrai Audio"):
        try:
            with st.spinner("Aggirando i blocchi di YouTube..."):
                # Opzioni avanzate per evitare l'errore 403
                ydl_opts = {
                    'format': 'bestaudio/best',
                    # Questo simula un browser reale
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'nocheckcertificate': True,
                    'quiet': True,
                    'no_warnings': True,
                    'outtmpl': 'audio_temp.%(ext)s',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': format_choice,
                        'preferredquality': '192',
                    }],
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    # Scarica il file
                    ydl.download([url])
                
                # Il nome del file creato da yt-dlp con il postprocessor
                final_filename = f"audio_temp.{format_choice}"
                
                if os.path.exists(final_filename):
                    with open(final_filename, "rb") as f:
                        st.download_button(f"📥 Scarica {format_choice.upper()}", f, f"youtube_audio.{format_choice}")
                    
                    # Pulizia obbligatoria per non riempire il server
                    os.remove(final_filename)
                    st.success("Conversione riuscita!")
                else:
                    st.error("Il file non è stato generato correttamente.")

        except Exception as e:
            st.error(f"Errore tecnico: {e}")
            st.info("Suggerimento: Se l'errore persiste, prova con un altro link o riprova tra pochi minuti. YouTube blocca temporaneamente gli indirizzi IP dei server cloud.")

st.sidebar.info("Gemini Tool v2.1")
