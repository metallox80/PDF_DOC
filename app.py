import streamlit as st
import fitz  # PyMuPDF
from PIL import Image
import io
import os
from pdf2docx import Converter
from deep_translator import GoogleTranslator
from streamlit_mermaid import st_mermaid

st.set_page_config(page_title="Gemini Master Tool 2026", layout="wide")

# --- INIZIALIZZAZIONE SESSIONE ---
if 'pdf_bytes' not in st.session_state:
    st.session_state['pdf_bytes'] = None
if 'last_uploaded' not in st.session_state:
    st.session_state['last_uploaded'] = None

# --- SIDEBAR: CARICAMENTO ---
st.sidebar.title("📁 Carica Documento")
uploaded_file = st.sidebar.file_uploader("Carica il PDF qui", type="pdf")

if uploaded_file:
    if st.session_state['last_uploaded'] != uploaded_file.name:
        st.session_state['pdf_bytes'] = uploaded_file.read()
        st.session_state['last_uploaded'] = uploaded_file.name
    st.sidebar.success(f"✅ {uploaded_file.name} pronto!")

# --- MENU ---
st.sidebar.markdown("---")
menu = st.sidebar.radio("Scegli Funzione", ["🏠 Dashboard", "🔄 Converti & Estrai", "🔃 Rotazione Multipla", "🔢 Riordina Pagine", "🌐 Traduttore", "📊 Diagrammi"])

if not st.session_state['pdf_bytes'] and menu != "📊 Diagrammi":
    st.warning("⚠️ Carica un file PDF nella sidebar per iniziare.")
    st.stop()

# --- 🏠 DASHBOARD ---
if menu == "🏠 Dashboard":
    st.header("Anteprima Documento")
    doc = fitz.open(stream=st.session_state['pdf_bytes'], filetype="pdf")
    p_idx = st.slider("Pagina", 1, len(doc), 1) - 1
    pix = doc[p_idx].get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
    st.image(Image.open(io.BytesIO(pix.tobytes("png"))), use_container_width=True)

# --- 🔄 CONVERTI & ESTRAI ---
elif menu == "🔄 Converti & Estrai":
    st.header("Conversione ed Estrazione")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Esporta in Word"):
            with open("temp.pdf", "wb") as f: f.write(st.session_state['pdf_bytes'])
            cv = Converter("temp.pdf"); cv.convert("out.docx"); cv.close()
            with open("out.docx", "rb") as f: st.download_button("📥 Scarica Word", f, "doc.docx")
    with col2:
        range_p = st.text_input("Range da estrarre (es: 1-2)", "1-1")
        if st.button("Estrai Pagine"):
            doc = fitz.open(stream=st.session_state['pdf_bytes'], filetype="pdf")
            try:
                s, e = map(int, range_p.split('-'))
                new = fitz.open(); new.insert_pdf(doc, from_page=s-1, to_page=e-1)
                buf = io.BytesIO(); new.save(buf)
                st.download_button("📥 Scarica Estratto", buf.getvalue(), "estratto.pdf")
            except: st.error("Formato range errato.")

# --- 🔃 ROTAZIONE MULTIPLA (AGGIORNATA) ---
elif menu == "🔃 Rotazione Multipla":
    st.header("Rotazione Avanzata")
    doc = fitz.open(stream=st.session_state['pdf_bytes'], filetype="pdf")
    
    col_ctrl, col_prev = st.columns([1, 1])
    
    with col_ctrl:
        mode = st.radio("Cosa vuoi ruotare?", ["Pagina Singola", "Tutto il PDF", "Range di Pagine"])
        angle = st.selectbox("Angolo di rotazione oraria:", [90, 180, 270], index=0)
        
        target_pages = []
        if mode == "Pagina Singola":
            p = st.number_input("Numero pagina", min_value=1, max_value=len(doc), value=1)
            target_pages = [p - 1]
        elif mode == "Tutto il PDF":
            target_pages = list(range(len(doc)))
        else:
            r = st.text_input("Inserisci range (es: 1-3 o 2,4,5)", "1-2")
            try:
                if "-" in r:
                    s, e = map(int, r.split('-'))
                    target_pages = list(range(s-1, e))
                else:
                    target_pages = [int(x.strip())-1 for x in r.split(',')]
            except: st.error("Formato range non valido.")

        if st.button("Applica Rotazione"):
            for p_idx in target_pages:
                if 0 <= p_idx < len(doc):
                    doc[p_idx].set_rotation((doc[p_idx].rotation + angle) % 360)
            
            buf = io.BytesIO()
            doc.save(buf)
            st.session_state['pdf_bytes'] = buf.getvalue()
            st.success("Rotazione applicata alla memoria del tool!")
            st.download_button("📥 Scarica PDF Modificato", buf.getvalue(), "pdf_elaborato.pdf")

    with col_prev:
        st.subheader("Anteprima Rapida")
        # Mostriamo la prima pagina del target selezionato
        if target_pages:
            p_to_show = target_pages[0]
            if 0 <= p_to_show < len(doc):
                pix = doc[p_to_show].get_pixmap(matrix=fitz.Matrix(angle))
                st.image(Image.open(io.BytesIO(pix.tobytes("png"))), caption=f"Anteprima Pagina {p_to_show+1} ruotata", use_container_width=True)

# --- 🔢 RIORDINA PAGINE ---
elif menu == "🔢 Riordina Pagine":
    st.header("Cambia Ordine")
    doc = fitz.open(stream=st.session_state['pdf_bytes'], filetype="pdf")
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
            st.session_state['pdf_bytes'] = buf.getvalue()
            st.success("Ordine aggiornato in memoria!")
            st.download_button("📥 Scarica Riordinato", buf.getvalue(), "riordinato.pdf")
        except: st.error("Errore nei numeri.")

# --- TRADUTTORE ---
elif menu == "🌐 Traduttore":
    st.header("Traduzione PDF")
    lang = st.selectbox("Verso:", ["it", "en", "fr", "es", "de"])
    if st.button("Avvia Traduzione"):
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
