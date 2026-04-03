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
st.sidebar.title("📁 Carica Documento Principale")
uploaded_file = st.sidebar.file_uploader("Il file base per tutti i tool", type="pdf")

if uploaded_file:
    if st.session_state['last_uploaded'] != uploaded_file.name:
        st.session_state['pdf_bytes'] = uploaded_file.read()
        st.session_state['last_uploaded'] = uploaded_file.name
    st.sidebar.success(f"✅ {uploaded_file.name} in memoria")

# --- MENU ---
st.sidebar.markdown("---")
menu = st.sidebar.radio("Scegli Funzione", [
    "🏠 Dashboard", 
    "🔄 Converti & Estrai", 
    "➕ Unione PDF",
    "🔃 Rotazione Multipla", 
    "🔢 Riordina Pagine", 
    "🌐 Traduttore", 
    "📊 Diagrammi"
])

if not st.session_state['pdf_bytes'] and menu != "📊 Diagrammi":
    st.warning("⚠️ Carica un file PDF nella sidebar per iniziare.")
    st.stop()

# --- 🏠 DASHBOARD ---
if menu == "🏠 Dashboard":
    st.header("Anteprima Documento Corrente")
    doc = fitz.open(stream=st.session_state['pdf_bytes'], filetype="pdf")
    st.write(f"Pagine totali: {len(doc)}")
    p_idx = st.slider("Pagina", 1, len(doc), 1) - 1
    pix = doc[p_idx].get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
    st.image(Image.open(io.BytesIO(pix.tobytes("png"))), use_container_width=True)

# --- 🔄 CONVERTI & ESTRAI ---
elif menu == "🔄 Converti & Estrai":
    st.header("Esportazione")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Esporta in Word (.docx)"):
            with open("temp.pdf", "wb") as f: f.write(st.session_state['pdf_bytes'])
            cv = Converter("temp.pdf"); cv.convert("out.docx"); cv.close()
            with open("out.docx", "rb") as f: st.download_button("📥 Scarica Word", f, "documento.docx")
    with col2:
        range_p = st.text_input("Range da estrarre (es: 1-2)", "1-1")
        if st.button("Estrai Pagine"):
            doc = fitz.open(stream=st.session_state['pdf_bytes'], filetype="pdf")
            try:
                s, e = map(int, range_p.split('-'))
                new = fitz.open(); new.insert_pdf(doc, from_page=s-1, to_page=e-1)
                buf = io.BytesIO(); new.save(buf)
                st.download_button("📥 Scarica Estratto", buf.getvalue(), "estratto.pdf")
            except: st.error("Errore range.")

# --- ➕ UNIONE PDF (NUOVA SEZIONE) ---
elif menu == "➕ Unione PDF":
    st.header("Unisci altri file al documento corrente")
    st.info("Il file che hai caricato nella sidebar è il 'Documento Base'. Qui puoi aggiungerne altri.")
    
    files_to_add = st.file_uploader("Seleziona uno o più PDF da aggiungere", type="pdf", accept_multiple_files=True)
    position = st.radio("Dove vuoi aggiungere i nuovi file?", ["In coda (alla fine)", "In testa (all'inizio)"])
    
    if files_to_add and st.button("Unisci i Documenti"):
        base_doc = fitz.open(stream=st.session_state['pdf_bytes'], filetype="pdf")
        new_merger = fitz.open()
        
        if position == "In testa (all'inizio)":
            for f in files_to_add:
                with fitz.open(stream=f.read(), filetype="pdf") as p: new_merger.insert_pdf(p)
            new_merger.insert_pdf(base_doc)
        else:
            new_merger.insert_pdf(base_doc)
            for f in files_to_add:
                with fitz.open(stream=f.read(), filetype="pdf") as p: new_merger.insert_pdf(p)
        
        buf = io.BytesIO()
        new_merger.save(buf)
        st.session_state['pdf_bytes'] = buf.getvalue() # Aggiorna memoria
        st.success("Documenti uniti con successo!")
        st.download_button("📥 Scarica PDF Unito", buf.getvalue(), "pdf_unito.pdf")

# --- 🔃 ROTAZIONE MULTIPLA ---
elif menu == "🔃 Rotazione Multipla":
    st.header("Rotazione")
    doc = fitz.open(stream=st.session_state['pdf_bytes'], filetype="pdf")
    col1, col2 = st.columns([1, 1])
    with col1:
        mode = st.radio("Target", ["Singola", "Tutto", "Range"])
        angle = st.selectbox("Angolo", [90, 180, 270])
        if mode == "Singola":
            targets = [st.number_input("Pagina", 1, len(doc), 1) - 1]
        elif mode == "Tutto":
            targets = list(range(len(doc)))
        else:
            r = st.text_input("Range (es: 1-3)", "1-2")
            targets = list(range(int(r.split('-')[0])-1, int(r.split('-')[1])))
            
        if st.button("Applica Rotazione"):
            for p in targets: doc[p].set_rotation((doc[p].rotation + angle) % 360)
            buf = io.BytesIO(); doc.save(buf); st.session_state['pdf_bytes'] = buf.getvalue()
            st.success("Ruotato!")
    with col2:
        pix = doc[targets[0]].get_pixmap(matrix=fitz.Matrix(angle))
        st.image(Image.open(io.BytesIO(pix.tobytes("png"))), caption="Anteprima", use_container_width=True)

# --- 🔢 RIORDINA PAGINE ---
elif menu == "🔢 Riordina Pagine":
    st.header("Riordino")
    doc = fitz.open(stream=st.session_state['pdf_bytes'], filetype="pdf")
    cols = st.columns(6)
    for i in range(len(doc)):
        pix = doc[i].get_pixmap(matrix=fitz.Matrix(0.1, 0.1))
        with cols[i % 6]: st.image(Image.open(io.BytesIO(pix.tobytes("png"))), caption=f"P.{i+1}")
    order = st.text_input("Nuova sequenza", value=", ".join(map(str, range(1, len(doc)+1))))
    if st.button("Applica Ordine"):
        idx = [int(x.strip()) - 1 for x in order.split(",")]
        doc.select(idx)
        buf = io.BytesIO(); doc.save(buf); st.session_state['pdf_bytes'] = buf.getvalue()
        st.download_button("📥 Scarica", buf.getvalue(), "ordinato.pdf")

# --- 🌐 TRADUTTORE ---
elif menu == "🌐 Traduttore":
    st.header("Traduzione")
    lang = st.selectbox("Lingua", ["it", "en", "fr", "es", "de"])
    if st.button("Traduci ora"):
        with st.spinner("Lavoro in corso..."):
            doc = fitz.open(stream=st.session_state['pdf_bytes'], filetype="pdf")
            out = fitz.open()
            translator = GoogleTranslator(source='auto', target=lang)
            for page in doc:
                new_p = out.new_page(width=page.rect.width, height=page.rect.height)
                for b in page.get_text("blocks"):
                    if b[4].strip():
                        new_p.insert_text((b[0], b[1]), translator.translate(b[4][:4000]), fontsize=9)
            buf = io.BytesIO(); out.save(buf); st.download_button("📥 Scarica", buf.getvalue(), "tradotto.pdf")

# --- 📊 DIAGRAMMI ---
elif menu == "📊 Diagrammi":
    st.header("Diagrammi")
    code = st.text_area("Mermaid Code", "graph TD\nA-->B", height=150)
    st_mermaid(code)
