import streamlit as st
from supabase import create_client, Client
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import io

# --- CONFIGURAÇÃO DO SUPABASE ---
# Substitui com os dados que copiaste do teu painel API
SUPABASE_URL = "https://pfpfpdlugehsbqxwkgyj.supabase.co"
SUPABASE_KEY = "sb_publishable_NSDC9o5fCW2AxTnS_ZEjtw_358GaFpI"

# Inicializa o cliente Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 2. ESTILO CSS PERSONALIZADO ---
def aplicar_design():
    st.markdown("""
        <style>
        /* Fundo da aplicação */
        .stApp {
            background-color: #f8f9fa;
        }
        /* Estilização dos botões */
        .stButton>button {
            width: 100%;
            border-radius: 8px;
            height: 3em;
            background-color: #007bff;
            color: white;
            font-weight: bold;
            border: none;
            transition: 0.3s;
        }
        .stButton>button:hover {
            background-color: #0056b3;
            border: none;
        }
        /* Estilização dos inputs e containers */
        .stTextInput>div>div>input {
            border-radius: 8px;
        }
        div[data-testid="stExpander"] {
            border-radius: 10px;
            background-color: white;
            border: 1px solid #e0e0e0;
        }
        /* Sidebar (Menu Lateral) */
        [data-testid="stSidebar"] {
            background-color: #ffffff;
            border-right: 1px solid #eee;
        }
        </style>
    """, unsafe_allow_html=True)

# --- 3. LÓGICA DE NEGÓCIO ---

def criar_folha_a4_cloud(lista_dados):
    largura_a4, altura_a4 = 3508, 2480
    dpi = 300
    largura_px = int((6.5 / 2.54) * dpi)
    altura_px = int((13.5 / 2.54) * dpi)
    
    folha = Image.new('RGB', (largura_a4, altura_a4), 'white')
    desenho = ImageDraw.Draw(folha)
    
    try:
        fonte = ImageFont.truetype("arial.ttf", 60)
    except:
        fonte = ImageFont.load_default()

    for i, item in enumerate(lista_dados):
        try:
            response = requests.get(item['imagem_url'])
            img = Image.open(BytesIO(response.content)).convert("RGB").resize((largura_px, altura_px))
            
            pos_x = 150 + (i * (largura_px + 100))
            pos_y = (altura_a4 - altura_px) // 2
            
            folha.paste(img, (pos_x, pos_y))
            desenho.text((pos_x + 50, pos_y + altura_px + 40), f"SIRIUS: {item['codigo']}", fill="black", font=fonte)
        except:
            continue

    buf = io.BytesIO()
    folha.save(buf, format="JPEG", quality=95)
    return buf.getvalue()

def upload_para_nuvem(imagem_file, codigo):
    try:
        nome_ficheiro = f"{codigo}.jpg"
        conteudo = imagem_file.getvalue()
        supabase.storage.from_("imagens_sirius").upload(
            path=nome_ficheiro,
            file=conteudo,
            file_options={"content-type": "image/jpeg", "upsert": "true"}
        )
        url_publica = supabase.storage.from_("imagens_sirius").get_public_url(nome_ficheiro)
        supabase.table("etiquetas").insert({"codigo": codigo, "imagem_url": url_publica}).execute()
        return url_publica
    except Exception as e:
        st.error(f"Erro no upload: {e}")
        return None

# --- 4. INTERFACE DO UTILIZADOR ---

aplicar_design()

# Barra Lateral (Menu)
with st.sidebar:
    st.image("https://img.icons8.com/clouds/200/database.png", width=200)
    st.title("EEs na Cloud")
    st.info("Sistema de Gestão de Etiquetas Energéticas v2.0")
    st.divider()
    st.write("🔧 **Status:** Conectado ao Supabase")
    st.write("📅 **Data:** 2026")

# Conteúdo Principal
st.title("🏷️ Gestão de Etiquetas Eficiência Energética")

tab_reg, tab_imp = st.tabs(["📥 Novo Registo", "🖨️ Área de Impressão"])

with tab_reg:
    with st.container():
        st.markdown("### Carregar Etiqueta")
        c1, c2 = st.columns([1, 2])
        with c1:
            cod_novo = st.text_input("Código Sirius", placeholder="Ex: 3988499")
        with c2:
            arq_novo = st.file_uploader("Upload da Imagem", type=['jpg', 'jpeg', 'png'])
        
        if st.button("Gravar na Base de Dados"):
            if cod_novo and arq_novo:
                with st.spinner("A enviar para a Cloud..."):
                    url = upload_para_nuvem(arq_novo, cod_novo)
                    if url:
                        st.success(f"Registo {cod_novo} concluído!")
                        st.image(url, width=200, caption="Imagem guardada na nuvem")

with tab_imp:
    st.markdown("### Montar Folha A4")
    with st.expander("Instruções de Impressão", expanded=False):
        st.write("Insira os códigos para gerar uma folha horizontal com até 3 etiquetas.")
    
    col_a, col_b, col_c = st.columns(3)
    with col_a: c1 = st.text_input("Código 1", key="i1")
    with col_b: c2 = st.text_input("Código 2", key="i2")
    with col_c: c3 = st.text_input("Código 3", key="i3")
    
    cods = [c.strip() for c in [c1, c2, c3] if c.strip()]
    
    if st.button("🔍 Gerar Pré-visualização"):
        if cods:
            encontrados = []
            for c in cods:
                res = supabase.table("etiquetas").select("*").eq("codigo", c).execute()
                if res.data: encontrados.append(res.data[0])
            
            if encontrados:
                folha = criar_folha_a4_cloud(encontrados)
                st.image(folha, caption="Visualização da Folha", use_container_width=True)
                st.download_button("📥 Descarregar Folha para Impressão", data=folha, file_name="SIRIUS_A4.jpg", mime="image/jpeg")


