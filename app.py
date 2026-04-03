import streamlit as st
import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont
import io
import os
from pdf2docx import Converter
from deep_translator import GoogleTranslator
from streamlit_mermaid import st_mermaid

st.set_page_config(page_title="Gemini Master Tool 2026", layout="wide")

# --- SESSION STATE ---
if 'pdf_bytes' not in st.session_state:
    st.session_state['pdf_bytes'] = None
if 'last_uploaded' not in st.session_state:
    st.session_state['last_uploaded'] = None

# --- SIDEBAR ---
st.sidebar.title("📁 PDF Master Central")
uploaded_file = st.sidebar.file_uploader("Carica il file base", type="pdf")

if uploaded_file:
    if st.session_state['last_uploaded'] != uploaded_file.name:
        st.session_state['pdf_bytes'] = uploaded_file.read()
        st.session_state['last_uploaded'] = uploaded_file.name
    st.sidebar.success(f"✅ {uploaded_file.name} pronto")

menu = st.sidebar.radio("Strumenti", [
    "🏠 Dashboard", 
    "✏️ Editor (Testo & Firme)",
    "🔄 Converti & Estrai", 
    "➕ Unione PDF",
    "🔃 Rotazione Multipla", 
    "🔢 Riordina Pagine", 
    "🌐 Traduttore", 
    "📊 Diagrammi"
])

if not st.session_state['pdf_bytes'] and menu != "📊 Diagrammi":
    st.warning("⚠️ Carica un PDF a sinistra per sbloccare i tool.")
    st.stop()

# --- 🏠 DASHBOARD ---
if menu == "🏠 Dashboard":
    st.header("Visualizzatore")
    doc = fitz.open(stream=st.session_state['pdf_bytes'], filetype="pdf")
    p_idx = st.slider("Pagina", 1, len(doc), 1) - 1
    pix = doc[p_idx].get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
    st.image(Image.open(io.BytesIO(pix.tobytes("png"))), use_container_width=True)

# --- ✏️ EDITOR (NUOVA SEZIONE) ---
elif menu == "✏️ Editor (Testo & Firme)":
    st.header("Editor: Aggiungi Testo o Firme")
    st.info("Scegli la pagina, scrivi il testo e decidi la posizione (X, Y).")
    
    doc = fitz.open(stream=st.session_state['pdf_bytes'], filetype="pdf")
    col_edit, col_prev = st.columns([1, 2])
    
    with col_edit:
        p_edit = st.number_input("Pagina da modificare", 1, len(doc), 1) - 1
        txt = st.text_input("Testo da aggiungere", "Tua Firma o Nota")
        color = st.color_picker("Colore testo", "#FF0000")
        
        # Coordinate (i PDF usano punti, 0,0 è in alto a sinistra)
        st.write("Posizionamento (Coordinate):")
        pos_x = st.slider("Posizione Orizzontale (X)", 0, 600, 50)
        pos_y = st.slider("Posizione Verticale (Y)", 0, 800, 50)
        size = st.slider("Dimensione carattere", 8, 72, 20)
        
        if st.button("Applica Modifica alla Pagina"):
            page = doc[p_edit]
            # Converte colore hex in RGB decimale (0-1)
            rgb = tuple(int(color.lstrip('#')[i:i+2], 16)/255 for i in (0, 2, 4))
            
            page.insert_text((pos_x, pos_y), txt, fontsize=size, color=rgb)
            
            buf = io.BytesIO()
            doc.save(buf)
            st.session_state['pdf_bytes'] = buf.getvalue()
            st.success("Testo inserito!")
            st.rerun()

    with col_prev:
        # Anteprima in tempo reale
        preview_page = doc[p_edit]
        pix = preview_page.get_pixmap(matrix=fitz.Matrix(1.2, 1.2))
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        # Disegniamo un mirino per aiutare l'utente
        draw = ImageDraw.Draw(img)
        # Scaliamo le coordinate per l'anteprima (approssimativo)
        draw.ellipse([pos_x*1.2-5, pos_y*1.2-5, pos_x*1.2+5, pos_y*1.2+5], outline="blue", width=3)
        st.image(img, caption="Il cerchio blu indica dove apparirà il testo", use_container_width=True)
        st.download_button("📥 Scarica PDF Editato", st.session_state['pdf_bytes'], "editato.pdf")

# --- 🔄 CONVERTI & ESTRAI ---
elif menu == "🔄 Converti & Estrai":
    st.header("Esportazione")
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
            except: st.error("Errore range.")

# --- ➕ UNIONE PDF ---
elif menu == "➕ Unione PDF":
    st.header("Unisci altri file")
    files_to_add = st.file_uploader("Seleziona PDF", type="pdf", accept_multiple_files=True)
    pos = st.radio("Posizione", ["Fine", "Inizio"])
    if files_to_add and st.button("Unisci"):
        base = fitz.open(stream=st.session_state['pdf_bytes'], filetype="pdf")
        merger = fitz.open()
        if pos == "Inizio":
            for f in files_to_add:
                with fitz.open(stream=f.read(), filetype="pdf") as p: merger.insert_pdf(p)
            merger.insert_pdf(base)
        else:
            merger.insert_pdf(base)
            for f in files_to_add:
                with fitz.open(stream=f.read(), filetype="pdf") as p: merger.insert_pdf(p)
        buf = io.BytesIO(); merger.save(buf); st.session_state['pdf_bytes'] = buf.getvalue()
        st.download_button("📥 Scarica", buf.getvalue(), "unito.pdf")

# --- 🔃 ROTAZIONE MULTIPLA ---
elif menu == "🔃 Rotazione Multipla":
    st.header("Rotazione")
    doc = fitz.open(stream=st.session_state['pdf_bytes'], filetype="pdf")
    mode = st.radio("Target", ["Singola", "Tutto", "Range"])
    angle = st.selectbox("Angolo", [90, 180, 270])
    if st.button("Applica"):
        targets = []
        if mode == "Singola": targets = [st.number_input("Pagina", 1, len(doc), 1)-1]
        elif mode == "Tutto": targets = list(range(len(doc)))
        else:
            r = st.text_input("Range", "1-2")
            targets = list(range(int(r.split('-')[0])-1, int(r.split('-')[1])))
        for p in targets: doc[p].set_rotation((doc[p].rotation + angle) % 360)
        buf = io.BytesIO(); doc.save(buf); st.session_state['pdf_bytes'] = buf.getvalue()
        st.success("Ruotato!")

# --- 🔢 RIORDINA PAGINE ---
elif menu == "🔢 Riordina Pagine":
    st.header("Riordino")
    doc = fitz.open(stream=st.session_state['pdf_bytes'], filetype="pdf")
    order = st.text_input("Nuova sequenza", value=", ".join(map(str, range(1, len(doc)+1))))
    if st.button("Applica"):
        idx = [int(x.strip()) - 1 for x in order.split(",")]
        doc.select(idx)
        buf = io.BytesIO(); doc.save(buf); st.session_state['pdf_bytes'] = buf.getvalue()
        st.success("Ordinato!")

# --- 🌐 TRADUTTORE ---
elif menu == "🌐 Traduttore":
    st.header("Traduzione")
    lang = st.selectbox("Lingua", ["it", "en", "fr", "es", "de"])
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
            buf = io.BytesIO(); out.save(buf); st.download_button("📥 Scarica", buf.getvalue(), "tradotto.pdf")

# --- 📊 DIAGRAMMI ---
elif menu == "📊 Diagrammi":
    st.header("Diagrammi")
    code = st.text_area("Mermaid Code", "graph TD\nA-->B", height=150)
    st_mermaid(code)
