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
    
    tab1, tab2, tab3, tab4 = st.tabs(["🔄 Converti & Estrai", "➕ Unisci PDF", "🔃 Ruota", "🔢 Riordina con Anteprima"])

    # --- TAB 1, 2, 3 (Codice invariato per brevità, mantieni quello precedente) ---
    with tab1:
        uploaded_pdf = st.file_uploader("Carica un PDF", type="pdf", key="pdf_conv")
        if uploaded_pdf:
            with open("temp_c.pdf", "wb") as f: f.write(uploaded_pdf.getbuffer())
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Converti in Word"):
                    cv = Converter("temp_c.pdf"); cv.convert("out.docx"); cv.close()
                    with open("out.docx", "rb") as f: st.download_button("📥 Scarica Word", f, "doc.docx")
            with c2:
                range_p = st.text_input("Range (es: 1-3)", "1-1")
                if st.button("Estrai"):
                    doc = fitz.open("temp_c.pdf")
                    s, e = map(int, range_p.split('-'))
                    new = fitz.open(); new.insert_pdf(doc, from_page=s-1, to_page=e-1)
                    buf = io.BytesIO(); new.save(buf)
                    st.download_button("📥 Scarica Estratto", buf.getvalue(), "estratto.pdf")

    with tab2:
        merge_files = st.file_uploader("Seleziona PDF da unire", type="pdf", accept_multiple_files=True)
        if merge_files and len(merge_files) > 1:
            if st.button("Unisci file"):
                merger = fitz.open()
                for f in merge_files:
                    with fitz.open(stream=f.read(), filetype="pdf") as p: merger.insert_pdf(p)
                buf = io.BytesIO(); merger.save(buf)
                st.download_button("📥 Scarica PDF Unito", buf.getvalue(), "unito.pdf")

    with tab3:
        rot_file = st.file_uploader("Carica PDF da ruotare", type="pdf", key="pdf_rot")
        if rot_file:
            angle = st.selectbox("Angolo", [90, 180, 270])
            if st.button("Ruota tutto"):
                doc = fitz.open(stream=rot_file.read(), filetype="pdf")
                for p in doc: p.set_rotation(p.rotation + angle)
                buf = io.BytesIO(); doc.save(buf)
                st.download_button("📥 Scarica Ruotato", buf.getvalue(), "ruotato.pdf")

    # --- TAB 4: RIORDINA PAGINE CON ANTEPRIME ---
    with tab4:
        st.subheader("Visualizza e Riordina")
        reorder_file = st.file_uploader("Carica il PDF per vedere le anteprime", type="pdf", key="pdf_reorder")
        
        if reorder_file:
            doc = fitz.open(stream=reorder_file.read(), filetype="pdf")
            num_pages = len(doc)
            
            # Mostra anteprime in una griglia
            st.write("### Anteprima Pagine")
            cols = st.columns(5) # 5 miniature per riga
            for i in range(num_pages):
                page = doc[i]
                pix = page.get_pixmap(matrix=fitz.Matrix(0.2, 0.2)) # Qualità bassa per velocità
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                with cols[i % 5]:
                    st.image(img, caption=f"Pagina {i+1}", use_container_width=True)
            
            st.divider()
            
            # Input per il riordino
            new_order_str = st.text_input("Inserisci il nuovo ordine (es: 2, 1, 4, 3)", 
                                         value=", ".join(map(str, range(1, num_pages + 1))))
            
            if st.button("Applica e Genera PDF"):
                try:
                    new_order = [int(x.strip()) - 1 for x in new_order_str.split(",")]
                    if len(new_order) != num_pages:
                        st.error(f"Devi inserire tutti i {num_pages} numeri delle pagine.")
                    else:
                        doc.select(new_order)
                        buf = io.BytesIO()
                        doc.save(buf)
                        st.download_button("📥 Scarica PDF Riordinato", buf.getvalue(), "riordinato.pdf")
                        st.success("Ordine applicato!")
                except Exception as e:
                    st.error(f"Errore: controlla i numeri inseriti.")

# --- SEZIONE TRADUTTORE ---
elif menu == "🌐 Traduttore PDF":
    st.header("Traduzione PDF")
    up_trans = st.file_uploader("Carica PDF", type="pdf")
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
            buf = io.BytesIO(); out_doc.save(buf)
            st.download_button("📥 Scarica Tradotto", buf.getvalue(), "tradotto.pdf")

# --- SEZIONE DIAGRAMMI ---
elif menu == "📊 Crea Diagrammi":
    st.header("Diagrammi Mermaid")
    code = st.text_area("Sintassi", "graph TD\nA[Inizio] --> B[Fine]", height=200)
    st_mermaid(code)

st.sidebar.markdown("---")
st.sidebar.info("Versione 2.8 - Visual PDF Editor")
