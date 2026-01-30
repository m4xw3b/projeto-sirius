import streamlit as st
from supabase import create_client, Client
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import io

# --- 1. CONFIGURAÇÃO SEGURA (SECRETS) ---
# O Streamlit vai procurar estes nomes na sua "caixa forte" online
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    ADMIN_PASSWORD = st.secrets["PASSWORD_ADMIN"]
except KeyError:
    st.error("Erro: Segredos não configurados no Streamlit Cloud.")
    st.stop()

# Inicializa o cliente Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 2. SISTEMA DE CONTROLO DE ACESSO ---
if 'admin_mode' not in st.session_state:
    st.session_state.admin_mode = False

def check_login(password):
    if password == ADMIN_PASSWORD: 
        st.session_state.admin_mode = True
        st.success("🔓 Modo Administrador Ativado!")
    else:
        st.error("❌ Password incorreta")

def logout():
    st.session_state.admin_mode = False
    st.rerun()

# --- 3. ESTILO CSS PERSONALIZADO ---
def aplicar_design():
    st.markdown("""
        <style>
        .stApp { background-color: #f8f9fa; }
        .stButton>button { border-radius: 8px; font-weight: bold; transition: 0.3s; }
        [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #eee; }
        .galeria-card {
            border: 1px solid #e0e0e0; border-radius: 10px;
            padding: 10px; background-color: white; text-align: center; margin-bottom: 20px;
        }
        </style>
    """, unsafe_allow_html=True)

# --- 4. FUNÇÕES DE SUPORTE ---
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
        st.error(f"Erro no upload: {e}")
        return None

def criar_folha_a4_cloud(lista_dados):
    largura_a4, altura_a4 = 3508, 2480
    dpi = 300
    largura_px, altura_px = int((6.5/2.54)*dpi), int((13.5/2.54)*dpi)
    folha = Image.new('RGB', (largura_a4, altura_a4), 'white')
    desenho = ImageDraw.Draw(folha)
    try: fonte = ImageFont.truetype("arial.ttf", 60)
    except: fonte = ImageFont.load_default()
    for i, item in enumerate(lista_dados):
        try:
            res = requests.get(item['imagem_url'])
            img = Image.open(BytesIO(res.content)).convert("RGB").resize((largura_px, altura_px))
            folha.paste(img, (150 + (i * (largura_px + 100)), (altura_a4 - altura_px) // 2))
            desenho.text((150 + (i * (largura_px + 100)) + 50, (altura_a4 - altura_px) // 2 + altura_px + 40), f"SIRIUS: {item['codigo']}", fill="black", font=fonte)
        except: continue
    buf = io.BytesIO()
    folha.save(buf, format="JPEG", quality=95)
    return buf.getvalue()

# --- 5. INTERFACE DO UTILIZADOR ---
aplicar_design()

with st.sidebar:
    # 1. Tentar carregar o logo localmente
    try:
        logo = Image.open("ee_logo.png")
        st.image(logo, use_container_width=True)
    except:
        # Caso o ficheiro não exista, usa um ícone de backup
        st.image("https://img.icons8.com/clouds/200/energy-usage.png", width=100)
    
    st.title("SIRIUS Cloud")
    
    # Sistema de Login (Modo Admin)
    if not st.session_state.admin_mode:
        pwd = st.text_input("Password Admin", type="password")
        if st.button("Ativar Modo Edição"):
            check_login(pwd)
    else:
        st.success("🔓 Modo Admin Ativo")
        if st.button("Sair (Modo Público)"):
            logout()
    
    st.divider()
    st.info("Utilizadores anónimos podem consultar e imprimir.")

st.title("🏷️ Gestão de Etiquetas de Eficiência Energética")

# Abas dinâmicas: Admin vê a aba de Registo, Anónimo não.
if st.session_state.admin_mode:
    abas = st.tabs(["🖼️ Galeria", "🖨️ Impressão", "📥 NOVO REGISTO"])
else:
    abas = st.tabs(["🖼️ Galeria", "🖨️ Impressão"])

# --- ABA GALERIA (Pública) ---
with abas[0]:
    st.markdown("### Histórico de Etiquetas")
    res_galeria = supabase.table("etiquetas").select("*").order("created_at", desc=True).execute()
    if res_galeria.data:
        cols = st.columns(4)
        for idx, item in enumerate(res_galeria.data):
            with cols[idx % 4]:
                st.markdown(f"""<div class='galeria-card'>
                    <img src='{item['imagem_url']}' style='width:100%; border-radius:5px;'>
                    <p style='margin-top:10px; font-weight:bold; color:#007bff;'>{item['codigo']}</p>
                </div>""", unsafe_allow_html=True)
                if st.session_state.admin_mode:
                    if st.button(f"Eliminar {item['codigo']}", key=f"del_{item['id']}"):
                        supabase.table("etiquetas").delete().eq("id", item['id']).execute()
                        st.rerun()

# --- ABA IMPRESSÃO (Pública) ---
with abas[1]:
    st.markdown("### Gerar Folha para Impressão")
    ca, cb, cc = st.columns(3)
    with ca: cod1 = st.text_input("Código 1", key="imp1")
    with cb: cod2 = st.text_input("Código 2", key="imp2")
    with cc: cod3 = st.text_input("Código 3", key="imp3")
    if st.button("🔍 Gerar Pré-visualização"):
        cods = [c.strip() for c in [cod1, cod2, cod3] if c.strip()]
        if cods:
            enc = []
            for c in cods:
                r = supabase.table("etiquetas").select("*").eq("codigo", c).execute()
                if r.data: enc.append(r.data[0])
            if enc:
                folha = criar_folha_a4_cloud(enc)
                st.image(folha, use_container_width=True)
                st.download_button("📥 Descarregar Folha", data=folha, file_name="SIRIUS_A4.jpg")

# --- ABA REGISTO (Apenas Admin) ---
if st.session_state.admin_mode:
    with abas[2]:
        st.markdown("### Upload de Nova Etiqueta")
        cx1, cx2 = st.columns([1, 2])
        with cx1: cod_n = st.text_input("Atribuir Código Sirius")
        with cx2: img_n = st.file_uploader("Selecionar Foto", type=['jpg','png'])
        if st.button("🚀 Gravar na Nuvem"):
            if cod_n and img_n:
                with st.spinner("A processar..."):
                    if upload_para_nuvem(img_n, cod_n):
                        st.success("Etiqueta gravada com sucesso!")
                        st.rerun()



