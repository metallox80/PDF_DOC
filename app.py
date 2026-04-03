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
uploaded_file = st.sidebar.file_uploader("Carica il PDF qui", type="pdf")

if uploaded_file:
    # Gestione della sessione per evitare ricaricamenti inutili
    if 'pdf_bytes' not in st.session_state or st.session_state.get('last_uploaded') != uploaded_file.name:
        st.session_state['pdf_bytes'] = uploaded_file.read()
        st.session_state['last_uploaded'] = uploaded_file.name
    st.sidebar.success(f"✅ {uploaded_file.name} pronto!")
else:
    st.sidebar.info("Carica un PDF a sinistra.")

# --- MENU ---
st.sidebar.markdown("---")
menu = st.sidebar.radio("Scegli Funzione", ["🏠 Dashboard", "🔄 Converti & Estrai", "🔃 Ruota & Riordina", "🌐 Traduttore", "📊 Diagrammi"])

if not uploaded_file and menu != "📊 Diagrammi":
    st.warning("⚠️ Carica un file PDF nella sidebar per iniziare.")
    st.stop()

# --- LOGICA DASHBOARD ---
if menu == "🏠 Dashboard":
    st.header("Anteprima Documento")
    doc = fitz.open(stream=st.session_state['pdf_bytes'], filetype="pdf")
    p_idx = st.slider("Pagina", 1, len(doc), 1) - 1
    pix = doc[p_idx].get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
    st.image(Image.open(io.BytesIO(pix.tobytes("png"))), use_container_width=True)

# --- LOGICA CONVERTI & ESTRAI ---
elif menu == "🔄 Converti & Estrai":
    st.header("Conversione ed Estrazione")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Esporta in Word"):
            with open("temp.pdf", "wb") as f: f.write(st.session_state['pdf_bytes'])
            cv = Converter("temp.pdf"); cv.convert("out.docx"); cv.close()
            with open("out.docx", "rb") as f: st.download_button("📥 Scarica Word", f, "doc.docx")
    with col2:
        range_p = st.text_input("Range (es: 1-2)", "1-1")
        if st.button("Estrai Pagine"):
            doc = fitz.open(stream=st.session_state['pdf_bytes'], filetype="pdf")
            try:
                s, e = map(int, range_p.split('-'))
                new = fitz.open(); new.insert_pdf(doc, from_page=s-1, to_page=e-1)
                buf = io.BytesIO(); new.save(buf)
                st.download_button("📥 Scarica Estratto", buf.getvalue(), "estratto.pdf")
            except: st.error("Errore nel formato range.")

# --- LOGICA RUOTA & RIORDINA (FIX ANTEPRIMA) ---
elif menu == "🔃 Ruota & Riordina":
    st.header("Modifica Struttura")
    doc = fitz.open(stream=st.session_state['pdf_bytes'], filetype="pdf")
    tab_rot, tab_ord = st.tabs(["🔃 Rotazione", "🔢 Riordino"])
    
    with tab_rot:
        col_ctrl, col_prev = st.columns([1, 1])
        with col_ctrl:
            angle = st.selectbox("Seleziona angolo di rotazione:", [0, 90, 180, 270], index=0)
            st.write("L'anteprima mostra come cambierà la prima pagina.")
            if st.button("Conferma e Ruota tutto il PDF"):
                for page in doc:
                    page.set_rotation((page.rotation + angle) % 360)
                buf = io.BytesIO()
                doc.save(buf)
                st.download_button("📥 Scarica PDF Ruotato", buf.getvalue(), "ruotato.pdf")
        
        with col_prev:
            # FIX: Generazione anteprima immediata basata sulla scelta dell'utente
            page_preview = doc[0]
            # Usiamo Matrix per simulare la rotazione visiva nell'anteprima
            mat = fitz.Matrix(angle) 
            pix = page_preview.get_pixmap(matrix=mat)
            st.image(Image.open(io.BytesIO(pix.tobytes("png"))), caption=f"Anteprima a {angle}°", use_container_width=True)
            
    with tab_ord:
        st.write("### Ordine Pagine")
        grid = st.columns(6)
        for i in range(len(doc)):
            pix = doc[i].get_pixmap(matrix=fitz.Matrix(0.1, 0.1))
            with grid[i % 6]: st.image(Image.open(io.BytesIO(pix.tobytes("png"))), caption=f"P. {i+1}")
        order = st.text_input("Nuova sequenza (es: 3,2,1)", value=", ".join(map(str, range(1, len(doc)+1))))
        if st.button("Applica Ordine"):
            try:
                idx_list = [int(x.strip()) - 1 for x in order.split(",")]
                doc.select(idx_list)
                buf = io.BytesIO(); doc.save(buf)
                st.download_button("📥 Scarica Riordinato", buf.getvalue(), "riordinato.pdf")
            except: st.error("Errore nei numeri inseriti.")

# --- TRADUTTORE ---
elif menu == "🌐 Traduttore":
    st.header("Traduzione PDF")
    lang = st.selectbox("Verso:", ["it", "en", "fr", "es", "de"])
    if st.button("Traduci"):
        with st.spinner("Traduzione..."):
            doc = fitz.open(stream=st.session_state['pdf_bytes'], filetype="pdf")
            out = fitz.open()
            translator = GoogleTranslator(source='auto', target=lang)
            for page in doc:
                new_p = out.new_page(width=page.rect.width, height=page.rect.height)
                for b in page.get_text("blocks"):
                    if b[4].strip():
                        new_p.insert_text((b[0], b[1]), translator.translate(b[4][:4000]), fontsize=9)
            buf = io.BytesIO(); out.save(buf); st.download_button("📥 Scarica Tradotto", buf.getvalue(), "tradotto.pdf")

# --- DIAGRAMMI ---
elif menu == "📊 Diagrammi":
    st.header("Diagrammi")
    code = st.text_area("Sintassi Mermaid", "graph LR\nA-->B", height=150)
    st_mermaid(code)
