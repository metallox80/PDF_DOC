import streamlit as st
import fitz  # PyMuPDF
from PIL import Image
import io
import os
from pdf2docx import Converter
from deep_translator import GoogleTranslator
import librosa
import soundfile as sf
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Gemini Master Tool 2026", layout="wide")

st.title("🚀 Gemini Ultimate Web Tool 2026")
st.write("Versione Cloud: PDF, Audio e Traduzione")

# Sidebar per la navigazione
menu = st.sidebar.radio("Scegli Funzione", ["📄 PDF Manager", "🌐 Traduttore PDF", "🎵 Audio Editor"])

# --- SEZIONE PDF MANAGER ---
if menu == "📄 PDF Manager":
    st.header("Gestione PDF")
    uploaded_pdf = st.file_uploader("Carica un PDF", type="pdf")
    
    if uploaded_pdf:
        # Salvataggio temporaneo per elaborazione
        with open("temp.pdf", "wb") as f:
            f.write(uploaded_pdf.getbuffer())
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Azioni")
            if st.button("Converti in Word"):
                with st.spinner("Conversione..."):
                    cv = Converter("temp.pdf")
                    cv.convert("output.docx")
                    cv.close()
                    with open("output.docx", "rb") as f:
                        st.download_button("📥 Scarica Word", f, "documento.docx")

            st.divider()
            st.subheader("Estrai Pagine")
            range_pages = st.text_input("Range (es: 1-3)", "1-1")
            if st.button("Estrai"):
                start, end = map(int, range_pages.split('-'))
                doc = fitz.open("temp.pdf")
                new_doc = fitz.open()
                new_doc.insert_pdf(doc, from_page=start-1, to_page=end-1)
                buf = io.BytesIO()
                new_doc.save(buf)
                st.download_button("📥 Scarica Estratto", buf.getvalue(), "estratto.pdf")

        with col2:
            st.subheader("Anteprima")
            doc = fitz.open("temp.pdf")
            page_num = st.slider("Pagina", 1, len(doc), 1)
            page = doc[page_num-1]
            pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            st.image(img, use_container_width=True)

# --- SEZIONE TRADUTTORE ---
elif menu == "🌐 Traduttore PDF":
    st.header("Traduttore PDF Integrato")
    up_trans = st.file_uploader("Carica PDF da tradurre", type="pdf", key="trans")
    lang = st.selectbox("Lingua Destinazione", ["it", "en", "fr", "es", "de"])
    
    if up_trans and st.button("Traduci tutto il PDF"):
        with st.spinner("Traduzione in corso (potrebbe richiedere tempo)..."):
            doc = fitz.open(stream=up_trans.read(), filetype="pdf")
            out_doc = fitz.open()
            translator = GoogleTranslator(source='auto', target=lang)
            
            for page in doc:
                new_page = out_doc.new_page(width=page.rect.width, height=page.rect.height)
                text_blocks = page.get_text("blocks")
                for b in text_blocks:
                    if b[4].strip():
                        trad = translator.translate(b[4][:4000])
                        new_page.insert_text((b[0], b[1]), trad, fontsize=9)
            
            buf = io.BytesIO()
            out_doc.save(buf)
            st.download_button("📥 Scarica PDF Tradotto", buf.getvalue(), "tradotto.pdf")

# --- SEZIONE AUDIO ---
elif menu == "🎵 Audio Editor":
    st.header("Audio Visualizer & Trimmer")
    up_audio = st.file_uploader("Carica file audio", type=["mp3", "wav", "ogg"])
    
    if up_audio:
        y, sr = librosa.load(up_audio, sr=None)
        
        # Plot waveform
        fig, ax = plt.subplots(figsize=(10, 3))
        librosa.display.waveshow(y, sr=sr, ax=ax, color='#3498db')
        st.pyplot(fig)
        
        st.write("Seleziona l'intervallo di tempo (secondi) da tagliare:")
        duration = len(y) / sr
        start_t, end_t = st.slider("Intervallo", 0.0, duration, (0.0, duration))
        
        if st.button("Taglia e Scarica"):
            idx_s, idx_e = int(start_t * sr), int(end_t * sr)
            trimmed = y[idx_s:idx_e]
            buf = io.BytesIO()
            sf.write(buf, trimmed, sr, format='WAV')
            st.download_button("📥 Scarica Taglio (.wav)", buf.getvalue(), "taglio.wav")

st.sidebar.info("Gemini Tool v2 - Accessibile da Browser")
