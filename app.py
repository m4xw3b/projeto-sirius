import streamlit as st
from supabase import create_client, Client
from PIL import Image
import requests
from io import BytesIO
import io

# --- 1. CONFIGURAÇÃO SEGURA (SECRETS) ---
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
        st.rerun()
    else:
        st.error("❌ Password incorreta")

def logout():
    st.session_state.admin_mode = False
    st.rerun()

# --- 3. ESTILO CSS PERSONALIZADO ---
def aplicar_design():
    st.markdown("""
        <style>
        /* 1. Centralização global da sidebar */
        [data-testid="stSidebarUserContent"] > div:first-child {
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        /* 2. Redimensionar e centrar caixa de password */
        div[data-testid="stSidebar"] div[data-baseweb="input"] {
            border: 2px solid #007bff !important;
            border-radius: 10px !important;
            width: 180px !important;
            margin: 0 auto !important;
        }

        /* 3. Centrar botões da sidebar */
        [data-testid="stSidebar"] .stButton {
            display: flex;
            justify-content: center;
            width: 100%;
            margin-top: 10px;
        }

        [data-testid="stSidebar"] .stButton button {
            width: auto !important;
            padding-left: 20px !important;
            padding-right: 20px !important;
        }

        /* 4. Barra fixa no fundo da sidebar */
        .sidebar-footer {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            background-color: #f8f9fa;
            border-top: 1px solid #ddd;
            padding: 15px 0;
            text-align: center;
            font-size: 12px;
            color: #666;
            z-index: 999;
        }

        /* 5. Cartões da Galeria */
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

def imprimir_direto_html(lista_dados):
    """Gera HTML com script para abrir janela de impressão do browser"""
    html_content = """
    <html>
    <head>
        <style>
            @page { size: landscape; margin: 1cm; }
            body { display: flex; justify-content: space-around; align-items: center; height: 90vh; margin: 0; }
            .etiqueta { text-align: center; width: 30%; }
            img { width: 100%; height: auto; border: 1px solid #eee; }
            p { font-family: Arial, sans-serif; font-weight: bold; margin-top: 10px; }
        </style>
    </head>
    <body>
    """
    for item in lista_dados:
        html_content += f"""
        <div class="etiqueta">
            <img src="{item['imagem_url']}">
            <p>SIRIUS: {item['codigo']}</p>
        </div>
        """
    html_content += """
    <script>window.onload = function() { window.print(); }</script>
    </body>
    </html>
    """
    return html_content

# --- 5. INTERFACE DO UTILIZADOR ---
aplicar_design()

with st.sidebar:
    col_esq, col_logo, col_dir = st.columns([1, 2, 1])
    with col_logo:
        try:
            logo = Image.open("ee_logo.png")
            st.image(logo, width=150)
        except:
            st.image("https://img.icons8.com/clouds/200/energy-usage.png", width=100)
    
    st.title("Projeto EcoPrint")
    
    if not st.session_state.admin_mode:
        pwd = st.text_input("Introduza a password", type="password")
        if st.button(" Modo Administrativo "):
            check_login(pwd)
    else:
        st.success("🔓 Modo Admin Ativo")
        if st.button("Sair (Modo Público)"):
            logout()
    
    st.divider()
    st.info("Utilizadores anónimos podem consultar e imprimir.")

    # Rodapé fixo na Sidebar
    st.markdown("""
        <div class="sidebar-footer">
            Projeto desenvolvido por <b>M4xW3b</b><br>
            📩 <i>Sugestões: geral@wintech.pt</i>
        </div>
    """, unsafe_allow_html=True)

st.subheader("🏷️ Gestão de Etiquetas de Eficiência Energética")

if st.session_state.admin_mode:
    abas = st.tabs(["🖼️ Galeria", "🖨️ Impressão", "📥 NOVO REGISTO"])
else:
    abas = st.tabs(["🖼️ Galeria", "🖨️ Impressão"])

# --- ABA GALERIA ---
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

# --- ABA IMPRESSÃO ---
with abas[1]:
    st.markdown("### Enviar para Impressão")
    ca, cb, cc = st.columns(3)
    with ca: cod1 = st.text_input("Código 1", key="imp1")
    with cb: cod2 = st.text_input("Código 2", key="imp2")
    with cc: cod3 = st.text_input("Código 3", key="imp3")
    
    if st.button("🖨️ Preparar e Imprimir"):
        cods = [c.strip() for c in [cod1, cod2, cod3] if c.strip()]
        if cods:
            enc = []
            for c in cods:
                r = supabase.table("etiquetas").select("*").eq("codigo", c).execute()
                if r.data: enc.append(r.data[0])
            
            if enc:
                conteudo_html = imprimir_direto_html(enc)
                st.components.v1.html(conteudo_html, height=0, width=0)
                st.info("A processar janela de impressão...")
            else:
                st.error("Nenhum código encontrado na base de dados.")

# --- ABA REGISTO ---
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
