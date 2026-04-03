import streamlit as st
import fitz  # PyMuPDF
from PIL import Image
import io
import os
from pdf2docx import Converter
from deep_translator import GoogleTranslator
from streamlit_mermaid import st_mermaid

st.set_page_config(page_title="Gemini Master Tool 2026", layout="wide")

st.title("🚀 Gemini Master Tool: PDF & Diagrammi")

# Sidebar semplificata
menu = st.sidebar.radio("Scegli Funzione", ["📄 PDF Manager", "🌐 Traduttore PDF", "📊 Crea Diagrammi"])

# --- SEZIONE PDF MANAGER ---
if menu == "📄 PDF Manager":
    st.header("Gestione e Conversione PDF")
    uploaded_pdf = st.file_uploader("Carica un PDF", type="pdf")
    
    if uploaded_pdf:
        with open("temp.pdf", "wb") as f:
            f.write(uploaded_pdf.getbuffer())
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Azioni veloci")
            if st.button("Converti in Word (.docx)"):
                with st.spinner("Conversione in corso..."):
                    cv = Converter("temp.pdf")
                    cv.convert("output.docx")
                    cv.close()
                    with open("output.docx", "rb") as f:
                        st.download_button("📥 Scarica il file Word", f, "documento_convertito.docx")

            st.divider()
            st.subheader("Estrai Pagine")
            range_p = st.text_input("Inserisci intervallo (es: 1-5)", "1-1")
            if st.button("Estrai PDF"):
                try:
                    start, end = map(int, range_p.split('-'))
                    doc = fitz.open("temp.pdf")
                    new_doc = fitz.open()
                    new_doc.insert_pdf(doc, from_page=start-1, to_page=end-1)
                    buf = io.BytesIO()
                    new_doc.save(buf)
                    st.download_button("📥 Scarica Estratto PDF", buf.getvalue(), "estratto.pdf")
                except:
                    st.error("Formato range non valido. Usa 'inizio-fine'.")

        with col2:
            st.subheader("Anteprima Documento")
            doc = fitz.open("temp.pdf")
            page_num = st.slider("Sfoglia pagine", 1, len(doc), 1)
            page = doc[page_num-1]
            pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
            st.image(Image.open(io.BytesIO(pix.tobytes("png"))), use_container_width=True)

# --- SEZIONE TRADUTTORE ---
elif menu == "🌐 Traduttore PDF":
    st.header("Traduzione Integrale PDF")
    up_trans = st.file_uploader("Carica il PDF da tradurre", type="pdf", key="trans")
    lang = st.selectbox("Seleziona lingua di destinazione", ["it", "en", "fr", "es", "de"])
    
    if up_trans and st.button("Traduci Documento"):
        with st.spinner("Traduzione in corso... attendi..."):
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
            st.download_button("📥 Scarica PDF Tradotto", buf.getvalue(), "tradotto.pdf")

# --- SEZIONE DIAGRAMMI (Stile Visio/Mermaid) ---
elif menu == "📊 Crea Diagrammi":
    st.header("Generatore di Diagrammi (Stile Visio)")
    st.write("Usa la sintassi testuale per creare diagrammi professionali istantaneamente.")
    
    col_code, col_viz = st.columns([1, 1])
    
    with col_code:
        default_code = """graph TD
    A[Inizio Progetto] --> B{Approvato?}
    B -- Sì --> C[Sviluppo]
    B -- No --> D[Revisione]
    C --> E[Conclusione]"""
        
        diagram_code = st.text_area("Scrivi il codice del diagramma qui:", value=default_code, height=300)
        st.info("💡 Esempio: 'A --> B' crea una freccia tra due blocchi.")

    with col_viz:
        st.subheader("Visualizzazione")
        st_mermaid(diagram_code)

st.sidebar.markdown("---")
st.sidebar.info("Versione 2.5 - PDF & Diagrams")
