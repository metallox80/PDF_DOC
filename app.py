import streamlit as st
import fitz  # PyMuPDF
from PIL import Image
import io
import os
from pdf2docx import Converter
from deep_translator import GoogleTranslator
from streamlit_mermaid import st_mermaid

st.set_page_config(page_title="Gemini Master Tool 2026", layout="wide")

st.title("🚀 Gemini Master Tool: PDF Expert & Diagrammi")

# Sidebar
menu = st.sidebar.radio("Scegli Funzione", ["📄 PDF Manager", "🌐 Traduttore PDF", "📊 Crea Diagrammi"])

# --- SEZIONE PDF MANAGER ---
if menu == "📄 PDF Manager":
    st.header("Gestione Avanzata PDF")
    
    # Sottosezioni per non affollare la pagina
    tab1, tab2, tab3 = st.tabs(["🔄 Converti & Estrai", "➕ Unisci PDF", "🔃 Ruota Pagine"])

    # --- TAB 1: CONVERSIONE ED ESTRAZIONE ---
    with tab1:
        uploaded_pdf = st.file_uploader("Carica un PDF per conversione o estratto", type="pdf", key="pdf_conv")
        if uploaded_pdf:
            with open("temp.pdf", "wb") as f:
                f.write(uploaded_pdf.getbuffer())
            
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Converti in Word (.docx)"):
                    with st.spinner("Conversione..."):
                        cv = Converter("temp.pdf")
                        cv.convert("output.docx")
                        cv.close()
                        with open("output.docx", "rb") as f:
                            st.download_button("📥 Scarica Word", f, "documento.docx")
            with c2:
                range_p = st.text_input("Range da estrarre (es: 1-3)", "1-1")
                if st.button("Estrai Pagine"):
                    doc = fitz.open("temp.pdf")
                    start, end = map(int, range_p.split('-'))
                    new_doc = fitz.open()
                    new_doc.insert_pdf(doc, from_page=start-1, to_page=end-1)
                    buf = io.BytesIO()
                    new_doc.save(buf)
                    st.download_button("📥 Scarica Estratto", buf.getvalue(), "estratto.pdf")

    # --- TAB 2: UNIONE PDF ---
    with tab2:
        st.subheader("Unisci più file in uno solo")
        merge_files = st.file_uploader("Seleziona i file PDF da unire", type="pdf", accept_multiple_files=True)
        if merge_files and len(merge_files) > 1:
            if st.button("Avvia Unione"):
                merger = fitz.open()
                for up_file in merge_files:
                    with fitz.open(stream=up_file.read(), filetype="pdf") as part:
                        merger.insert_pdf(part)
                buf = io.BytesIO()
                merger.save(buf)
                st.download_button("📥 Scarica PDF Unito", buf.getvalue(), "pdf_unito_finale.pdf")
        elif merge_files:
            st.info("Carica almeno due file per sbloccare l'unione.")

    # --- TAB 3: ROTAZIONE ---
    with tab3:
        st.subheader("Ruota le pagine del PDF")
        rot_file = st.file_uploader("Carica PDF da ruotare", type="pdf", key="pdf_rot")
        if rot_file:
            angle = st.selectbox("Angolo di rotazione", [90, 180, 270], help="Rotazione in senso orario")
            if st.button("Ruota tutte le pagine"):
                doc = fitz.open(stream=rot_file.read(), filetype="pdf")
                for page in doc:
                    page.set_rotation(page.rotation + angle)
                buf = io.BytesIO()
                doc.save(buf)
                st.download_button("📥 Scarica PDF Ruotato", buf.getvalue(), "pdf_ruotato.pdf")

# --- SEZIONE TRADUTTORE ---
elif menu == "🌐 Traduttore PDF":
    st.header("Traduzione PDF")
    up_trans = st.file_uploader("Carica PDF", type="pdf", key="trans")
    lang = st.selectbox("Lingua", ["it", "en", "fr", "es", "de"])
    if up_trans and st.button("Traduci"):
        with st.spinner("Traduzione..."):
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
            st.download_button("📥 Scarica Tradotto", buf.getvalue(), "tradotto.pdf")

# --- SEZIONE DIAGRAMMI ---
elif menu == "📊 Crea Diagrammi":
    st.header("Diagrammi Mermaid")
    code = st.text_area("Sintassi (es. graph LR; A-->B)", "graph TD\nA[Start] --> B[Process]\nB --> C[End]", height=200)
    st_mermaid(code)

st.sidebar.markdown("---")
st.sidebar.info("Versione 2.6 - PDF Expert Mode")
