import streamlit as st
import fitz
from PIL import Image, ImageDraw
import io
from pdf2docx import Converter
from deep_translator import GoogleTranslator
from streamlit_mermaid import st_mermaid
from streamlit_drawable_canvas import st_canvas # <--- La magia è qui

st.set_page_config(page_title="Gemini Master Tool 2026", layout="wide")

# --- SESSION STATE ---
if 'pdf_bytes' not in st.session_state: st.session_state['pdf_bytes'] = None
if 'last_uploaded' not in st.session_state: st.session_state['last_uploaded'] = None

# --- SIDEBAR ---
st.sidebar.title("📁 PDF Master Central")
uploaded_file = st.sidebar.file_uploader("Carica il file base", type="pdf")
if uploaded_file:
    if st.session_state['last_uploaded'] != uploaded_file.name:
        st.session_state['pdf_bytes'] = uploaded_file.read()
        st.session_state['last_uploaded'] = uploaded_file.name
    st.sidebar.success(f"✅ {uploaded_file.name} pronto")

menu = st.sidebar.radio("Strumenti", ["🏠 Dashboard", "✏️ Editor (Mouse Select)", "🔄 Altri Tool"])

if not st.session_state['pdf_bytes'] and menu != "📊 Diagrammi":
    st.warning("⚠️ Carica un PDF a sinistra.")
    st.stop()

# --- ✏️ EDITOR CON SELEZIONE MOUSE ---
if menu == "✏️ Editor (Mouse Select)":
    st.header("Clicca sulla pagina per posizionare il testo")
    doc = fitz.open(stream=st.session_state['pdf_bytes'], filetype="pdf")
    
    col_ctrl, col_canvas = st.columns([1, 2])
    
    with col_ctrl:
        p_edit = st.number_input("Pagina", 1, len(doc), 1) - 1
        txt_to_add = st.text_input("Testo da inserire", "Firma qui")
        font_size = st.slider("Grandezza", 10, 50, 20)
        font_color = st.color_picker("Colore", "#000000")
        st.write("---")
        st.info("Istruzioni: Clicca un punto nell'immagine a destra, poi premi il tasto sotto.")

    with col_canvas:
        # Preparazione immagine per il Canvas
        page = doc[p_edit]
        pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
        bg_img = Image.open(io.BytesIO(pix.tobytes("png")))
        w, h = bg_img.size

        # Crea il Canvas interattivo
        canvas_result = st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)",  # Colore riempimento
            stroke_width=2,
            background_image=bg_img,
            update_streamlit=True,
            height=h,
            width=w,
            drawing_mode="point", # Modalità punto (clic)
            point_display_radius=5,
            key="canvas",
        )

    # Logica di inserimento dopo il clic
    if canvas_result.json_data is not None:
        # Recupera le coordinate dell'ultimo punto cliccato
        objects = canvas_result.json_data["objects"]
        if objects:
            last_point = objects[-1]
            # Convertiamo le coordinate del canvas (pixel) in punti PDF
            # Il canvas è 1.5x rispetto al PDF originale
            real_x = last_point["left"] / 1.5
            real_y = last_point["top"] / 1.5
            
            if st.button(f"Inserisci '{txt_to_add}' in questo punto"):
                rgb = tuple(int(font_color.lstrip('#')[i:i+2], 16)/255 for i in (0, 2, 4))
                page.insert_text((real_x, real_y), txt_to_add, fontsize=font_size, color=rgb)
                
                buf = io.BytesIO()
                doc.save(buf)
                st.session_state['pdf_bytes'] = buf.getvalue()
                st.success("Testo inserito! Torna alla Dashboard per vedere il risultato.")
                st.rerun()

# (Qui andrebbero gli altri moduli Dashboard, Unione ecc. come prima)
elif menu == "🏠 Dashboard":
    doc = fitz.open(stream=st.session_state['pdf_bytes'], filetype="pdf")
    p = st.slider("Pagina", 1, len(doc), 1) - 1
    st.image(Image.open(io.BytesIO(doc[p].get_pixmap(matrix=fitz.Matrix(1.5, 1.5)).tobytes("png"))))

if st.session_state['pdf_bytes']:
    st.sidebar.download_button("📥 SCARICA PDF", st.session_state['pdf_bytes'], "editato.pdf")
