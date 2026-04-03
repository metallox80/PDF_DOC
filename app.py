import streamlit as st
import fitz  # PyMuPDF
from PIL import Image, ImageDraw
import io
import os
import base64
from pdf2docx import Converter
from deep_translator import GoogleTranslator
from streamlit_mermaid import st_mermaid
from streamlit_drawable_canvas import st_canvas

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Gemini Master Tool 2026", layout="wide")

# --- FUNZIONI DI SUPPORTO ---

def render_canvas_image(pil_img):
    """Converte immagine PIL in stringa Base64 per il Canvas"""
    buffered = io.BytesIO()
    pil_img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

def get_page_image(pdf_bytes, p_idx, zoom=1.5):
    """Genera anteprima pagina PDF come oggetto PIL"""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[p_idx]
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    return Image.open(io.BytesIO(pix.tobytes("png")))

# --- INIZIALIZZAZIONE SESSIONE ---
if 'pdf_bytes' not in st.session_state:
    st.session_state['pdf_bytes'] = None
if 'last_uploaded' not in st.session_state:
    st.session_state['last_uploaded'] = None

# --- SIDEBAR: CARICAMENTO UNICO ---
st.sidebar.title("📁 PDF Master Central")
uploaded_file = st.sidebar.file_uploader("Carica il PDF base qui", type="pdf")

if uploaded_file:
    if st.session_state['last_uploaded'] != uploaded_file.name:
        st.session_state['pdf_bytes'] = uploaded_file.read()
        st.session_state['last_uploaded'] = uploaded_file.name
    st.sidebar.success(f"✅ {uploaded_file.name} pronto")

menu = st.sidebar.radio("Strumenti", [
    "🏠 Dashboard", 
    "✏️ Editor (Mouse Select)",
    "🔄 Converti & Estrai", 
    "➕ Unione PDF",
    "🔃 Rotazione Multipla", 
    "🔢 Riordina Pagine", 
    "🌐 Traduttore PDF",
    "📊 Diagrammi Mermaid"
])

# Controllo sicurezza
if not st.session_state['pdf_bytes'] and menu != "📊 Diagrammi Mermaid":
    st.warning("⚠️ Carica un file PDF nella barra laterale per iniziare.")
    st.stop()

# --- 🏠 DASHBOARD ---
if menu == "🏠 Dashboard":
    st.header("Visualizzatore Documento")
    doc = fitz.open(stream=st.session_state['pdf_bytes'], filetype="pdf")
    st.write(f"Pagine: {len(doc)}")
    p_idx = st.slider("Sfoglia", 1, len(doc), 1) - 1
    st.image(get_page_image(st.session_state['pdf_bytes'], p_idx), use_container_width=True)

# --- ✏️ EDITOR (MOUSE SELECT) ---
elif menu == "✏️ Editor (Mouse Select)":
    st.header("✏️ Clicca sulla pagina per posizionare il testo")
    doc = fitz.open(stream=st.session_state['pdf_bytes'], filetype="pdf")
    col_ctrl, col_canvas = st.columns([1, 2])
    
    with col_ctrl:
        p_edit = st.number_input("Pagina", 1, len(doc), 1) - 1
        txt_to_add = st.text_input("Testo", "Firma/Nota")
        f_size = st.slider("Dimensione", 10, 60, 24)
        f_color = st.color_picker("Colore", "#FF0000")
        st.info("Istruzioni: Clicca un punto a destra e premi 'Conferma'.")

    with col_canvas:
        pil_bg = get_page_image(st.session_state['pdf_bytes'], p_edit, zoom=1.5)
        w, h = pil_bg.size
        bg_url = render_canvas_image(pil_bg) # Fix errore 403/URL

        canvas_result = st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)",
            background_image=bg_url,
            update_streamlit=True,
            height=h, width=w,
            drawing_mode="point",
            point_display_radius=5,
            key="canvas_master",
        )

    if canvas_result.json_data and "objects" in canvas_result.json_data:
        objects = canvas_result.json_data["objects"]
        if objects:
            last_p = objects[-1]
            real_x, real_y = last_p["left"] / 1.5, last_p["top"] / 1.5
            if st.button("Conferma Inserimento"):
                rgb = tuple(int(f_color.lstrip('#')[i:i+2], 16)/255 for i in (0, 2, 4))
                page = doc[p_edit]
                page.insert_text((real_x, real_y), txt_to_add, fontsize=f_size, color=rgb)
                buf = io.BytesIO(); doc.save(buf); st.session_state['pdf_bytes'] = buf.getvalue()
                st.success("Testo inserito!")
                st.rerun()

# --- 🔄 CONVERTI & ESTRAI ---
elif menu == "🔄 Converti & Estrai":
    st.header("Esportazione")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Esporta in Word"):
            with open("temp.pdf", "wb") as f: f.write(st.session_state['pdf_bytes'])
            cv = Converter("temp.pdf"); cv.convert("out.docx"); cv.close()
            with open("out.docx", "rb") as f: st.download_button("📥 Scarica Word", f, "doc.docx")
    with c2:
        r = st.text_input("Range (es: 1-3)", "1-1")
        if st.button("Estrai PDF"):
            doc = fitz.open(stream=st.session_state['pdf_bytes'], filetype="pdf")
            s, e = map(int, r.split('-'))
            new = fitz.open(); new.insert_pdf(doc, from_page=s-1, to_page=e-1)
            buf = io.BytesIO(); new.save(buf); st.download_button("📥 Scarica Estratto", buf.getvalue(), "estratto.pdf")

# --- ➕ UNIONE PDF ---
elif menu == "➕ Unione PDF":
    st.header("Unisci altri file")
    files = st.file_uploader("Carica PDF aggiuntivi", type="pdf", accept_multiple_files=True)
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
    col1, col2 = st.columns([1, 1])
    with col1:
        mode = st.radio("Ambito", ["Singola", "Tutto", "Range"])
        ang = st.selectbox("Angolo Orario", [90, 180, 270])
        if mode == "Singola": t = [st.number_input("Pagina", 1, len(doc), 1) - 1]
        elif mode == "Tutto": t = list(range(len(doc)))
        else:
            r_str = st.text_input("Range (es: 1-2)", "1-2")
            t = list(range(int(r_str.split('-')[0])-1, int(r_str.split('-')[1])))
        if st.button("Ruota"):
            for p_idx in t: doc[p_idx].set_rotation((doc[p_idx].rotation + ang) % 360)
            buf = io.BytesIO(); doc.save(buf); st.session_state['pdf_bytes'] = buf.getvalue(); st.rerun()
    with col2:
        pix = doc[t[0]].get_pixmap(matrix=fitz.Matrix(ang))
        st.image(Image.open(io.BytesIO(pix.tobytes("png"))), caption="Anteprima", width=300)

# --- 🔢 RIORDINA PAGINE ---
elif menu == "🔢 Riordina Pagine":
    st.header("Riordino Visuale")
    doc = fitz.open(stream=st.session_state['pdf_bytes'], filetype="pdf")
    grid = st.columns(6)
    for i in range(len(doc)):
        with grid[i % 6]: st.image(get_page_image(st.session_state['pdf_bytes'], i, 0.2), caption=f"P.{i+1}")
    new_seq = st.text_input("Nuova sequenza (es: 2,1,3)", value=", ".join(map(str, range(1, len(doc)+1))))
    if st.button("Applica"):
        idxs = [int(x.strip()) - 1 for x in new_seq.split(",")]
        doc.select(idxs)
        buf = io.BytesIO(); doc.save(buf); st.session_state['pdf_bytes'] = buf.getvalue(); st.rerun()

# --- 🌐 TRADUTTORE PDF ---
elif menu == "🌐 Traduttore PDF":
    st.header("Traduzione Documento")
    lang = st.selectbox("Lingua", ["it", "en", "fr", "es", "de"])
    if st.button("Avvia"):
        with st.spinner("In corso..."):
            doc = fitz.open(stream=st.session_state['pdf_bytes'], filetype="pdf")
            out = fitz.open(); trans = GoogleTranslator(source='auto', target=lang)
            for page in doc:
                new_p = out.new_page(width=page.rect.width, height=page.rect.height)
                for b in page.get_text("blocks"):
                    if b[4].strip():
                        new_p.insert_text((b[0], b[1]), trans.translate(b[4][:4000]), fontsize=9)
            buf = io.BytesIO(); out.save(buf); st.session_state['pdf_bytes'] = buf.getvalue(); st.success("Fatto!")

# --- 📊 DIAGRAMMI ---
elif menu == "📊 Diagrammi Mermaid":
    st.header("Diagrammi")
    diag = st.text_area("Codice", "graph TD\nA-->B", height=150)
    st_mermaid(diag)

# --- TASTO DOWNLOAD FINALE ---
if st.session_state['pdf_bytes']:
    st.sidebar.markdown("---")
    st.sidebar.download_button("📥 SCARICA PDF FINALE", st.session_state['pdf_bytes'], "output.pdf", use_container_width=True)
