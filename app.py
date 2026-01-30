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
        .stApp { background-color: #f8f9fa; }
        .stButton>button {
            width: 100%; border-radius: 8px; height: 3em;
            background-color: #007bff; color: white; font-weight: bold;
            border: none; transition: 0.3s;
        }
        .stButton>button:hover { background-color: #0056b3; }
        [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #eee; }
        /* Estilo para os cartões da galeria */
        .galeria-card {
            border: 1px solid #e0e0e0;
            border-radius: 10px;
            padding: 10px;
            background-color: white;
            text-align: center;
            margin-bottom: 20px;
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
        except: continue
    buf = io.BytesIO()
    folha.save(buf, format="JPEG", quality=95)
    return buf.getvalue()

def upload_para_nuvem(imagem_file, codigo):
    try:
        nome_ficheiro = f"{codigo}.jpg"
        conteudo = imagem_file.getvalue()
        supabase.storage.from_("imagens_sirius").upload(
            path=nome_ficheiro, file=conteudo,
            file_options={"content-type": "image/jpeg", "upsert": "true"}
        )
        url_publica = supabase.storage.from_("imagens_sirius").get_public_url(nome_ficheiro)
        supabase.table("etiquetas").insert({"codigo": codigo, "imagem_url": url_publica}).execute()
        return url_publica
    except Exception as e:
        st.error(f"Erro: {e}")
        return None

# --- 4. INTERFACE DO UTILIZADOR ---
aplicar_design()

with st.sidebar:
    st.image("https://img.icons8.com/clouds/200/database.png", width=100)
    st.title("SIRIUS Cloud")
    st.info("Sistema de Gestão de Etiquetas v2.0")
    st.divider()
    if st.button("🔄 Atualizar Dados"):
        st.rerun()

st.title("🏷️ Gestão de Etiquetas Sirius")
tab_reg, tab_imp, tab_gal = st.tabs(["📥 Novo Registo", "🖨️ Área de Impressão", "🖼️ Galeria de Registos"])

with tab_reg:
    st.markdown("### Carregar Etiqueta")
    c1, c2 = st.columns([1, 2])
    with c1: cod_novo = st.text_input("Código Sirius", placeholder="Ex: 3988499")
    with c2: arq_novo = st.file_uploader("Upload da Imagem", type=['jpg', 'jpeg', 'png'])
    if st.button("Gravar na Base de Dados"):
        if cod_novo and arq_novo:
            with st.spinner("A enviar..."):
                if upload_para_nuvem(arq_novo, cod_novo):
                    st.success(f"Registo {cod_novo} concluído!")
        else: st.warning("Preencha todos os campos.")

with tab_imp:
    st.markdown("### Montar Folha A4")
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
                st.image(folha, use_container_width=True)
                st.download_button("📥 Descarregar JPEG", data=folha, file_name="SIRIUS_A4.jpg")

with tab_gal:
    st.markdown("### Histórico de Etiquetas")
    # Busca todos os registos ordenados pelo mais recente
    res_galeria = supabase.table("etiquetas").select("*").order("created_at", desc=True).execute()
    
    if res_galeria.data:
        # Criar uma grelha de 4 colunas para a galeria
        colunas_galeria = st.columns(4)
        for idx, item in enumerate(res_galeria.data):
            with colunas_galeria[idx % 4]:
                st.markdown(f"""<div class='galeria-card'>
                    <img src='{item['imagem_url']}' style='width:100%; border-radius:5px;'>
                    <p style='margin-top:10px; font-weight:bold; color:#007bff;'>{item['codigo']}</p>
                </div>""", unsafe_allow_html=True)
    else:
        st.info("Ainda não existem etiquetas registadas.")


