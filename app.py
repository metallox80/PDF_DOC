import streamlit as st
import fitz  # PyMuPDF
from PIL import Image, ImageDraw
import io
import os
from pdf2docx import Converter
from deep_translator import GoogleTranslator
from streamlit_mermaid import st_mermaid
from streamlit_drawable_canvas import st_canvas

st.set_page_config(page_title="Gemini Master Tool 2026", layout="wide")

# --- INIZIALIZZAZIONE SESSIONE ---
if 'pdf_bytes' not in st.session_state:
    st.session_state['pdf_bytes'] = None
if 'last_uploaded' not in st.session_state:
    st.session_state['last_uploaded'] = None

# --- SIDEBAR: CARICAMENTO UNICO ---
st.sidebar.title("📁 PDF Master Central")
uploaded_file = st.sidebar.file_uploader("Carica il PDF base per tutti i tool", type="pdf")

if uploaded_file:
    if st.session_state['last_uploaded'] != uploaded_file.name:
        st.session_state['pdf_bytes'] = uploaded_file.read()
        st.session_state['last_uploaded'] = uploaded_file.name
    st.sidebar.success(f"✅ {uploaded_file.name} in memoria")

menu = st.sidebar.radio("Scegli Strumento", [
    "🏠 Dashboard", 
    "✏️ Editor (Mouse Select)",
    "🔄 Converti & Estrai", 
    "➕ Unione PDF",
    "🔃 Rotazione Multipla", 
    "🔢 Riordina Pagine", 
    "🌐 Traduttore PDF",
    "📊 Diagrammi Mermaid"
])

# Controllo sicurezza: se non c'è il file, blocca i tool (tranne diagrammi)
if not st.session_state['pdf_bytes'] and menu != "📊 Diagrammi Mermaid":
    st.warning("⚠️ Per favore, carica un file PDF nella barra laterale a sinistra per iniziare.")
    st.stop()

# Funzione di supporto per ottenere immagini delle pagine
def get_page_image(pdf_bytes, p_idx, zoom=1.5):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[p_idx]
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    return Image.open(io.BytesIO(pix.tobytes("png")))

# --- 🏠 DASHBOARD ---
if menu == "🏠 Dashboard":
    st.header("Anteprima Documento Corrente")
    doc = fitz.open(stream=st.session_state['pdf_bytes'], filetype="pdf")
    st.write(f"Pagine totali: {len(doc)}")
    p_idx = st.slider("Sfoglia pagine", 1, len(doc), 1) - 1
    st.image(get_page_image(st.session_state['pdf_bytes'], p_idx), use_container_width=True)

# --- ✏️ EDITOR (MOUSE SELECT) ---
elif menu == "✏️ Editor (Mouse Select)":
    st.header("✏️ Clicca sulla pagina per posizionare il testo")
    doc = fitz.open(stream=st.session_state['pdf_bytes'], filetype="pdf")
    
    col_ctrl, col_canvas = st.columns([1, 2])
    
    with col_ctrl:
        p_edit = st.number_input("Pagina da editare", 1, len(doc), 1) - 1
        txt_to_add = st.text_input("Testo da inserire", "Firma/Nota qui")
        f_size = st.slider("Dimensione", 10, 60, 24)
        f_color = st.color_picker("Colore Testo", "#FF0000")
        st.info("Istruzioni: Clicca un punto nell'immagine a destra. Apparirà un puntino. Poi premi 'Conferma Inserimento'.")

    with col_canvas:
        bg_img = get_page_image(st.session_state['pdf_bytes'], p_edit, zoom=1.5)
        w, h = bg_img.size
        canvas_result = st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)",
            stroke_width=2,
            background_image=bg_img,
            update_streamlit=True,
            height=h, width=w,
            drawing_mode="point",
            point_display_radius=5,
            key="canvas_edit",
        )

    if canvas_result.json_data and "objects" in canvas_result.json_data:
        objects = canvas_result.json_data["objects"]
        if objects:
            last_p = objects[-1]
            real_x, real_y = last_p["left"] / 1.5, last_p["top"] / 1.5
            if st.button(f"Conferma Inserimento in ({int(real_x)}, {int(real_y)})"):
                rgb = tuple(int(f_color.lstrip('#')[i:i+2], 16)/255 for i in (0, 2, 4))
                page = doc[p_edit]
                page.insert_text((real_x, real_y), txt_to_add, fontsize=f_size, color=rgb)
                buf = io.BytesIO(); doc.save(buf); st.session_state['pdf_bytes'] = buf.getvalue()
                st.success("Testo inserito! Controlla la Dashboard.")
                st.rerun()

# --- 🔄 CONVERTI & ESTRAI ---
elif menu == "🔄 Converti & Estrai":
    st.header("Conversione ed Estrazione")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Esporta tutto in Word (.docx)"):
            with open("temp.pdf", "wb") as f: f.write(st.session_state['pdf_bytes'])
            cv = Converter("temp.pdf"); cv.convert("out.docx"); cv.close()
            with open("out.docx", "rb") as f: st.download_button("📥 Scarica Word", f, "documento.docx")
    with c2:
        r = st.text_input("Range da estrarre (es: 1-3)", "1-1")
        if st.button("Estrai PDF"):
            try:
                doc = fitz.open(stream=st.session_state['pdf_bytes'], filetype="pdf")
                s, e = map(int, r.split('-'))
                new = fitz.open(); new.insert_pdf(doc, from_page=s-1, to_page=e-1)
                buf = io.BytesIO(); new.save(buf); st.download_button("📥 Scarica Estratto", buf.getvalue(), "estratto.pdf")
            except: st.error("Formato range non valido.")

# --- ➕ UNIONE PDF ---
elif menu == "➕ Unione PDF":
    st.header("Unisci altri file al documento base")
    files = st.file_uploader("Carica file PDF aggiuntivi", type="pdf", accept_multiple_files=True)
    pos = st.radio("Dove aggiungerli?", ["In coda", "In testa"])
    if files and st.button("Esegui Unione"):
        base = fitz.open(stream=st.session_state['pdf_bytes'], filetype="pdf")
        merger = fitz.open()
        if pos == "In testa":
            for f in files:
                with fitz.open(stream=f.read(), filetype="pdf") as p: merger.insert_pdf(p)
            merger.insert_pdf(base)
        else:
            merger.insert_pdf(base)
            for f in files:
                with fitz.open(stream=f.read(), filetype="pdf") as p: merger.insert_pdf(p)
        buf = io.BytesIO(); merger.save(buf); st.session_state['pdf_bytes'] = buf.getvalue()
        st.success("File uniti correttamente!")

# --- 🔃 ROTAZIONE MULTIPLA ---
elif menu == "🔃 Rotazione Multipla":
    st.header("Rotazione Pagine")
    doc = fitz.open(stream=st.session_state['pdf_bytes'], filetype="pdf")
    col_rot, col_pre = st.columns([1, 1])
    with col_rot:
        mode = st.radio("Ambito", ["Singola", "Tutto", "Range"])
        ang = st.selectbox("Angolo Orario", [90, 180, 270])
        if mode == "Singola": t = [st.number_input("Pagina", 1, len(doc), 1) - 1]
        elif mode == "Tutto": t = list(range(len(doc)))
        else:
            r_str = st.text_input("Range (es: 1-2)", "1-2")
            t = list(range(int(r_str.split('-')[0])-1, int(r_str.split('-')[1])))
        if st.button("Applica Rotazione"):
            for p_idx in t: doc[p_idx].set_rotation((doc[p_idx].rotation + ang) % 360)
            buf = io.BytesIO(); doc.save(buf); st.session_state['pdf_bytes'] = buf.getvalue(); st.rerun()
    with col_pre:
        p_pre = doc[t[0]].get_pixmap(matrix=fitz.Matrix(ang))
        st.image(Image.open(io.BytesIO(p_pre.tobytes("png"))), caption="Anteprima Risultato", width=300)

# --- 🔢 RIORDINA PAGINE ---
elif menu == "🔢 Riordina Pagine":
    st.header("Riordino Visuale")
    doc = fitz.open(stream=st.session_state['pdf_bytes'], filetype="pdf")
    st.write("Trascina i numeri basandoti sulle anteprime sotto:")
    grid = st.columns(6)
    for i in range(len(doc)):
        with grid[i % 6]: st.image(get_page_image(st.session_state['pdf_bytes'], i, 0.2), caption=f"P.{i+1}")
    new_seq = st.text_input("Nuova sequenza (es: 3, 2, 1)", value=", ".join(map(str, range(1, len(doc)+1))))
    if st.button("Salva Nuovo Ordine"):
        try:
            idxs = [int(x.strip()) - 1 for x in new_seq.split(",")]
            doc.select(idxs)
            buf = io.BytesIO(); doc.save(buf); st.session_state['pdf_bytes'] = buf.getvalue(); st.rerun()
        except: st.error("Errore nella sequenza numerica.")

# --- 🌐 TRADUTTORE PDF ---
elif menu == "🌐 Traduttore PDF":
    st.header("Traduzione Integrale")
    lang = st.selectbox("Lingua Destinazione", ["it", "en", "fr", "es", "de"])
    if st.button("Avvia Traduzione"):
        with st.spinner("Traduzione in corso..."):
            doc = fitz.open(stream=st.session_state['pdf_bytes'], filetype="pdf")
            out = fitz.open(); trans = GoogleTranslator(source='auto', target=lang)
            for page in doc:
                new_p = out.new_page(width=page.rect.width, height=page.rect.height)
                for b in page.get_text("blocks"):
                    if b[4].strip():
                        new_p.insert_text((b[0], b[1]), trans.translate(b[4][:4000]), fontsize=9)
            buf = io.BytesIO(); out.save(buf); st.session_state['pdf_bytes'] = buf.getvalue(); st.success("Tradotto!")

# --- 📊 DIAGRAMMI MERMAID ---
elif menu == "📊 Diagrammi Mermaid":
    st.header("Generatore Diagrammi")
    diag = st.text_area("Codice Mermaid", "graph TD\nA[Inizio] --> B{Approva?}\nB -- Sì --> C[Fine]\nB -- No --> D[Riprova]", height=200)
    st_mermaid(diag)

# --- TASTO SCARICA SEMPRE VISIBILE ---
if st.session_state['pdf_bytes']:
    st.sidebar.markdown("---")
    st.sidebar.download_button("📥 SCARICA PDF FINALE", st.session_state['pdf_bytes'], "output_gemini_master.pdf", use_container_width=True)
