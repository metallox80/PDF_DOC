import streamlit as st
import fitz  # PyMuPDF
from PIL import Image, ImageDraw
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

# --- SIDEBAR: CARICAMENTO UNICO ---
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

# FUNZIONE DI SUPPORTO PER ANTEPRIMA VELOCE
def get_page_image(pdf_bytes, p_idx, zoom=1.2):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[p_idx]
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    return Image.open(io.BytesIO(pix.tobytes("png")))

# --- 🏠 DASHBOARD ---
if menu == "🏠 Dashboard":
    st.header("Visualizzatore Documento")
    doc = fitz.open(stream=st.session_state['pdf_bytes'], filetype="pdf")
    p_idx = st.slider("Sfoglia Pagine", 1, len(doc), 1) - 1
    st.image(get_page_image(st.session_state['pdf_bytes'], p_idx), use_container_width=True)

# --- ✏️ EDITOR ---
elif menu == "✏️ Editor (Testo & Firme)":
    st.header("Aggiungi Testo o Firme")
    doc = fitz.open(stream=st.session_state['pdf_bytes'], filetype="pdf")
    col_edit, col_prev = st.columns([1, 2])
    with col_edit:
        p_edit = st.number_input("Pagina", 1, len(doc), 1) - 1
        txt = st.text_input("Testo", "Esempio Firma")
        color = st.color_picker("Colore", "#000000")
        x = st.slider("X (Orizzontale)", 0, 600, 50)
        y = st.slider("Y (Verticale)", 0, 800, 50)
        size = st.slider("Font Size", 8, 72, 20)
        if st.button("Applica Modifica"):
            page = doc[p_edit]
            rgb = tuple(int(color.lstrip('#')[i:i+2], 16)/255 for i in (0, 2, 4))
            page.insert_text((x, y), txt, fontsize=size, color=rgb)
            buf = io.BytesIO(); doc.save(buf); st.session_state['pdf_bytes'] = buf.getvalue()
            st.rerun()
    with col_prev:
        img = get_page_image(st.session_state['pdf_bytes'], p_edit)
        draw = ImageDraw.Draw(img)
        draw.ellipse([x*1.2-5, y*1.2-5, x*1.2+5, y*1.2+5], outline="red", width=3)
        st.image(img, caption="Il mirino rosso indica la posizione", use_container_width=True)

# --- 🔄 CONVERTI & ESTRAI ---
elif menu == "🔄 Converti & Estrai":
    st.header("Esportazione")
    col_c, col_e = st.columns(2)
    with col_c:
        if st.button("Esporta in Word"):
            with open("temp.pdf", "wb") as f: f.write(st.session_state['pdf_bytes'])
            cv = Converter("temp.pdf"); cv.convert("out.docx"); cv.close()
            with open("out.docx", "rb") as f: st.download_button("📥 Scarica Word", f, "doc.docx")
    with col_e:
        r = st.text_input("Range (es: 1-2)", "1-1")
        if st.button("Estrai"):
            doc = fitz.open(stream=st.session_state['pdf_bytes'], filetype="pdf")
            s, e = map(int, r.split('-'))
            new = fitz.open(); new.insert_pdf(doc, from_page=s-1, to_page=e-1)
            buf = io.BytesIO(); new.save(buf); st.download_button("📥 Scarica Estratto", buf.getvalue(), "estratto.pdf")

# --- ➕ UNIONE PDF ---
elif menu == "➕ Unione PDF":
    st.header("Unisci Documenti")
    files = st.file_uploader("Aggiungi altri PDF", type="pdf", accept_multiple_files=True)
    pos = st.radio("Posizione", ["Fine", "Inizio"])
    if files and st.button("Unisci"):
        base = fitz.open(stream=st.session_state['pdf_bytes'], filetype="pdf")
        merger = fitz.open()
        if pos == "Inizio":
            for f in files:
                with fitz.open(stream=f.read(), filetype="pdf") as p: merger.insert_pdf(p)
            merger.insert_pdf(base)
        else:
            merger.insert_pdf(base)
            for f in files:
                with fitz.open(stream=f.read(), filetype="pdf") as p: merger.insert_pdf(p)
        buf = io.BytesIO(); merger.save(buf); st.session_state['pdf_bytes'] = buf.getvalue()
        st.success("Uniti!")

# --- 🔃 ROTAZIONE MULTIPLA ---
elif menu == "🔃 Rotazione Multipla":
    st.header("Rotazione")
    doc = fitz.open(stream=st.session_state['pdf_bytes'], filetype="pdf")
    col_sel, col_p = st.columns([1, 1])
    with col_sel:
        m = st.radio("Target", ["Singola", "Tutto", "Range"])
        ang = st.selectbox("Angolo", [90, 180, 270])
        if m == "Singola": t = [st.number_input("Pagina", 1, len(doc), 1)-1]
        elif m == "Tutto": t = list(range(len(doc)))
        else: 
            raw = st.text_input("Range", "1-2")
            t = list(range(int(raw.split('-')[0])-1, int(raw.split('-')[1])))
        if st.button("Ruota"):
            for p in t: doc[p].set_rotation((doc[p].rotation + ang) % 360)
            buf = io.BytesIO(); doc.save(buf); st.session_state['pdf_bytes'] = buf.getvalue(); st.rerun()
    with col_p:
        pix = doc[t[0]].get_pixmap(matrix=fitz.Matrix(ang/90 * 0.5)) # Anteprima ruotata
        st.image(Image.open(io.BytesIO(pix.tobytes("png"))), caption="Anteprima Rotazione")

# --- 🔢 RIORDINA PAGINE ---
elif menu == "🔢 Riordina Pagine":
    st.header("Riordino Visuale")
    doc = fitz.open(stream=st.session_state['pdf_bytes'], filetype="pdf")
    cols = st.columns(6)
    for i in range(len(doc)):
        with cols[i % 6]: st.image(get_page_image(st.session_state['pdf_bytes'], i, 0.2), caption=f"P.{i+1}")
    order = st.text_input("Nuova sequenza (es: 2,1,3)", value=", ".join(map(str, range(1, len(doc)+1))))
    if st.button("Applica Ordine"):
        idx = [int(x.strip()) - 1 for x in order.split(",")]
        doc.select(idx)
        buf = io.BytesIO(); doc.save(buf); st.session_state['pdf_bytes'] = buf.getvalue(); st.rerun()

# --- 🌐 TRADUTTORE ---
elif menu == "🌐 Traduttore":
    st.header("Traduzione con Anteprima")
    doc = fitz.open(stream=st.session_state['pdf_bytes'], filetype="pdf")
    st.image(get_page_image(st.session_state['pdf_bytes'], 0, 0.8), caption="Documento Originale")
    lang = st.selectbox("Lingua", ["it", "en", "fr", "es", "de"])
    if st.button("Traduci"):
        with st.spinner("Traduzione..."):
            out = fitz.open(); translator = GoogleTranslator(source='auto', target=lang)
            for page in doc:
                new_p = out.new_page(width=page.rect.width, height=page.rect.height)
                for b in page.get_text("blocks"):
                    if b[4].strip():
                        new_p.insert_text((b[0], b[1]), translator.translate(b[4][:4000]), fontsize=9)
            buf = io.BytesIO(); out.save(buf); st.session_state['pdf_bytes'] = buf.getvalue(); st.success("Tradotto!")

# --- 📊 DIAGRAMMI ---
elif menu == "📊 Diagrammi":
    st.header("Diagrammi")
    code = st.text_area("Mermaid Code", "graph TD\nA-->B", height=150)
    st_mermaid(code)

if st.session_state['pdf_bytes']:
    st.sidebar.download_button("📥 SCARICA PDF FINALE", st.session_state['pdf_bytes'], "output_gemini.pdf")
