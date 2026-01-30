import streamlit as st
import os
from PIL import Image, ImageDraw, ImageFont
import io

# Configuração da Página
st.set_page_config(page_title="Sistema SIRIUS - Etiquetas", layout="wide")


def criar_a4_sirius(lista_dados):
    """Monta a folha A4 e retorna o buffer da imagem."""
    largura_a4, altura_a4 = 3508, 2480
    dpi = 300
    largura_px = int((6.5 / 2.54) * dpi)
    altura_px = int((13.5 / 2.54) * dpi)
    margem_e_espaco = 150

    folha = Image.new('RGB', (largura_a4, altura_a4), 'white')
    desenho = ImageDraw.Draw(folha)

    try:
        # No Streamlit Cloud, fontes .ttf devem estar na pasta do projeto
        fonte = ImageFont.truetype("arial.ttf", 60)
    except:
        fonte = ImageFont.load_default()

    for i, (img_file, cod) in enumerate(lista_dados):
        try:
            img = Image.open(img_file).convert("RGB").resize((largura_px, altura_px))
            pos_x = margem_e_espaco + (i * (largura_px + 100))
            pos_y = (altura_a4 - altura_px) // 2
            folha.paste(img, (pos_x, pos_y))
            texto_y = pos_y + altura_px + 40
            desenho.text((pos_x + 50, texto_y), f"SIRIUS: {cod}", fill="black", font=fonte)
        except Exception as e:
            st.error(f"Erro ao processar {cod}: {e}")

    # Salva em memória para download
    buf = io.BytesIO()
    folha.save(buf, format="JPEG", quality=95)
    byte_im = buf.getvalue()
    return byte_im


# --- Interface Streamlit ---
st.title("🏷️ Sistema SIRIUS v1.5 - Web Edition")
st.markdown("Gerador de folhas A4 para etiquetas de eficiência energética.")

aba1, aba2 = st.tabs(["🖨️ Gerar Impressão", "ℹ️ Instruções"])

with aba1:
    st.subheader("Selecione até 3 imagens")

    col1, col2, col3 = st.columns(3)
    imagens_selecionadas = []

    with col1:
        img1 = st.file_uploader("Imagem 1", type=['jpg', 'png', 'jpeg'], key="1")
        cod1 = st.text_input("Código Sirius 1", key="c1")
        if img1 and cod1: imagens_selecionadas.append((img1, cod1))

    with col2:
        img2 = st.file_uploader("Imagem 2", type=['jpg', 'png', 'jpeg'], key="2")
        cod2 = st.text_input("Código Sirius 2", key="c2")
        if img2 and cod2: imagens_selecionadas.append((img2, cod2))

    with col3:
        img3 = st.file_uploader("Imagem 3", type=['jpg', 'png', 'jpeg'], key="3")
        cod3 = st.text_input("Código Sirius 3", key="c3")
        if img3 and cod3: imagens_selecionadas.append((img3, cod3))

    if imagens_selecionadas:
        if st.button("🚀 Gerar Folha A4"):
            with st.spinner("A processar imagens..."):
                resultado_a4 = criar_a4_sirius(imagens_selecionadas)

                st.image(resultado_a4, caption="Pré-visualização da Folha A4", use_container_width=True)

                st.download_button(
                    label="📥 Descarregar Folha para Impressão",
                    data=resultado_a4,
                    file_name="Folha_SIRIUS_A4.jpg",
                    mime="image/jpeg"
                )

with aba2:
    st.info("""
    **Como usar:**
    1. Carregue as fotos das etiquetas diretamente do seu PC ou Telemóvel.
    2. Atribua o código correspondente.
    3. Clique em 'Gerar Folha A4'.
    4. Faça o download e imprima o ficheiro resultante.
    """)