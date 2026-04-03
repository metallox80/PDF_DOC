import streamlit as st
import fitz  # PyMuPDF
from PIL import Image
import io
import os
from pdf2docx import Converter
from deep_translator import GoogleTranslator
from streamlit_mermaid import st_mermaid

st.set_page_config(page_title="Gemini Master Tool 2026", layout="wide")

# --- CARICAMENTO FILE UNICO NELLA SIDEBAR ---
st.sidebar.title("📁 Carica Documento")
uploaded_file = st.sidebar.file_uploader("Carica il PDF una volta sola per tutti i tool", type="pdf")

if uploaded_file:
    # Salvataggio in session_state per non perdere il file durante i cambi tab
    st.session_state['pdf_bytes'] = uploaded_file.read()
    st.sidebar.success("✅ File pronto per l'uso!")
else:
    st.sidebar.info("Inizia caricando un PDF qui sopra.")

# --- MENU DI NAVIGAZIONE ---
st.sidebar.markdown("---")
menu = st.sidebar.radio("Scegli Funzione", ["🏠 Dashboard & Anteprima", "🔄 Converti & Estrai", "🔃 Ruota & Riordina", "🌐 Traduttore PDF", "📊 Crea Diagrammi"])

# Messaggio di errore se manca il file (tranne che per i diagrammi)
if not uploaded_file and menu != "📊 Crea Diagrammi":
    st.warning("⚠️ Per favore, carica un file PDF nella barra laterale a sinistra per iniziare.")
    st.stop()

# --- 🏠 DASHBOARD & ANTEPRIMA ---
if menu == "🏠 Dashboard & Anteprima":
    st.header("Anteprima Documento")
    doc = fitz.open(stream=st.session_state['pdf_bytes'], filetype="pdf")
    st.write(f"**Nome file:** {uploaded_file.name} | **Pagine:** {len(doc)}")
    
    page_num = st.slider("Sfoglia pagine", 1, len(doc), 1)
    page = doc[page_num-1]
    pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
    st.image(Image.open(io.BytesIO(pix.tobytes("png"))), use_container_width=True)

# --- 🔄 CONVERTI & ESTRAI ---
elif menu == "🔄 Converti & Estrai":
    st.header("Conversione ed Estrazione")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Word")
        if st.button("Converti in .docx"):
            with st.spinner("Conversione..."):
                with open("temp_shared.pdf", "wb") as f:
                    f.write(st.session_state['pdf_bytes'])
                cv = Converter("temp_shared.pdf")
                cv.convert("output.docx")
                cv.close()
                with open("output.docx", "rb") as f:
                    st.download_button("📥 Scarica Word", f, "documento.docx")
    
    with col2:
        st.subheader("Estratto")
        range_p = st.text_input("Intervallo (es: 1-3)", "1-1")
        if st.button("Estrai Pagine"):
            doc = fitz.open(stream=st.session_state['pdf_bytes'], filetype="pdf")
            try:
                start, end = map(int, range_p.split('-'))
                new_doc = fitz.open()
                new_doc.insert_pdf(doc, from_page=start-1, to_page=end-1)
                buf = io.BytesIO()
                new_doc.save(buf)
                st.download_button("📥 Scarica Estratto PDF", buf.getvalue(), "estratto.pdf")
            except:
                st.error("Formato non valido.")

# --- 🔃 RUOTA & RIORDINA ---
elif menu == "🔃 Ruota & Riordina":
    st.header("Modifica Struttura")
    doc = fitz.open(stream=st.session_state['pdf_bytes'], filetype="pdf")
    
    tab_rot, tab_ord = st.tabs(["🔃 Ruota", "🔢 Riordina"])
    
    with tab_rot:
        angle = st.selectbox("Angolo di rotazione", [90, 180, 270])
        if st.button("Applica Rotazione"):
            for page in doc:
                page.set_rotation(page.rotation + angle)
            buf = io.BytesIO()
            doc.save(buf)
            st.download_button("📥 Scarica PDF Ruotato", buf.getvalue(), "ruotato.pdf")
            
    with tab_ord:
        st.write("### Anteprima per Riordino")
        cols = st.columns(6)
        for i in range(len(doc)):
            pix = doc[i].get_pixmap(matrix=fitz.Matrix(0.15, 0.15))
            with cols[i % 6]:
                st.image(Image.open(io.BytesIO(pix.tobytes("png"))), caption=f"P. {i+1}")
        
        new_order_str = st.text_input("Nuovo ordine (es: 2, 1, 3)", value=", ".join(map(str, range(1, len(doc) + 1))))
        if st.button("Salva Nuovo Ordine"):
            try:
                new_order = [int(x.strip()) - 1 for x in new_order_str.split(",")]
                doc.select(new_order)
                buf = io.BytesIO()
                doc.save(buf)
                st.download_button("📥 Scarica PDF Riordinato", buf.getvalue(), "riordinato.pdf")
            except:
                st.error("Controlla i numeri inseriti.")

# --- 🌐 TRADUTTORE PDF ---
elif menu == "🌐 Traduttore PDF":
    st.header("Traduzione PDF")
    lang = st.selectbox("Lingua di destinazione", ["it", "en", "fr", "es", "de"])
    if st.button("Avvia Traduzione"):
        with st.spinner("Traduzione..."):
            doc = fitz.open(stream=st.session_state['pdf_bytes'], filetype="pdf")
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
            st.download_button("📥 Scarica PDF Tradotto", buf.getvalue(), "tradotto.pdf")

# --- 📊 CREA DIAGRAMMI ---
elif menu == "📊 Crea Diagrammi":
    st.header("Generatore Diagrammi")
    code = st.text_area("Codice Mermaid", "graph TD\nA[File Caricato] --> B[Scegli Tool]\nB --> C[Scarica Risultato]", height=200)
    st_mermaid(code)

st.sidebar.markdown("---")
st.sidebar.info("Gemini Tool 2026 - Versione Unificata")
