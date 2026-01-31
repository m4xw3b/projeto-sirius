import streamlit as st
from supabase import create_client, Client
from PIL import Image
import requests
import io

# --- 1. CONFIGURAÇÃO SEGURA (SECRETS) ---
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    ADMIN_PASSWORD = st.secrets["PASSWORD_ADMIN"]
except KeyError:
    st.error("Erro: Segredos não configurados no Streamlit Cloud. Verifique o painel Secrets.")
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
        /* Centralização da Sidebar */
        [data-testid="stSidebarUserContent"] > div:first-child {
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        /* Input de Password */
        div[data-testid="stSidebar"] div[data-baseweb="input"] {
            border: 2px solid #007bff !important;
            border-radius: 10px !important;
            width: 180px !important;
            margin: 0 auto !important;
        }

        /* Botões da Sidebar */
        [data-testid="stSidebar"] .stButton {
            display: flex;
            justify-content: center;
            width: 100%;
            margin-top: 10px;
        }

        [data-testid="stSidebar"] .stButton button {
            width: auto !important;
            padding: 0 20px !important;
        }

        /* Rodapé Fixo */
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

        /* Cards da Galeria */
        .galeria-card {
            border: 1px solid #e0e0e0;
            border-radius: 10px;
            padding: 10px;
            background-color: white;
            text-align: center;
            margin-bottom: 20px;
            min-height: 320px;
        }

        /* Landing Page Hero */
        .landing-hero {
            background: linear-gradient(90deg, #007bff, #00c6ff);
            color: white;
            padding: 40px;
            border-radius: 15px;
            margin-bottom: 25px;
            text-align: center;
        }
        </style>
    """, unsafe_allow_html=True)

# --- 4. FUNÇÕES DE SUPORTE ---
def verificar_codigo_existente(codigo):
    res = supabase.table("etiquetas").select("codigo").eq("codigo", codigo).execute()
    return len(res.data) > 0

def upload_para_nuvem(imagem_file, codigo, descricao):
    try:
        if verificar_codigo_existente(codigo):
            st.error(f"❌ Erro: O código '{codigo}' já existe na base de dados.")
            return False
            
        nome_ficheiro = f"{codigo}.jpg"
        conteudo = imagem_file.getvalue()
        
        # Upload para Storage
        supabase.storage.from_("imagens_sirius").upload(
            path=nome_ficheiro, file=conteudo,
            file_options={"content-type": "image/jpeg", "upsert": "true"}
        )
        
        url_publica = supabase.storage.from_("imagens_sirius").get_public_url(nome_ficheiro)
        
        # Inserir na tabela (Certifica-te que a coluna 'descricao' existe no Supabase)
        supabase.table("etiquetas").insert({
            "codigo": codigo, 
            "imagem_url": url_publica,
            "descricao": descricao
        }).execute()
        return True
    except Exception as e:
        st.error(f"Erro no upload: {e}")
        return False

def imprimir_direto_html(lista_dados):
    html_content = """
    <html>
    <head>
        <style>
            @page { size: A4 landscape; margin: 0; }
            body { margin: 0; padding: 0; display: flex; justify-content: center; align-items: center; height: 100vh; background-color: white; }
            .container { display: flex; gap: 1.5cm; justify-content: center; align-items: flex-start; }
            .box { text-align: center; width: 6.5cm; }
            .img-etiqueta { width: 6.5cm; height: 13.5cm; object-fit: contain; border: 0.1px solid #ccc; }
            .legenda { font-family: Arial, sans-serif; font-size: 14pt; font-weight: bold; margin-top: 0.5cm; }
        </style>
    </head>
    <body>
        <div class="container">
    """
    for item in lista_dados:
        html_content += f"""
        <div class="box">
            <img class="img-etiqueta" src="{item['imagem_url']}">
            <div class="legenda">SIRIUS: {item['codigo']}</div>
        </div>
        """
    html_content += """
        </div>
        <script>window.onload = function() { setTimeout(function() { window.print(); }, 800); };</script>
    </body>
    </html>
    """
    return html_content

# --- 5. EXECUÇÃO DA INTERFACE ---
aplicar_design()

# --- SIDEBAR ---
with st.sidebar:
    col_esq, col_logo, col_dir = st.columns([1, 2, 1])
    with col_logo:
        try:
            st.image(Image.open("ee_logo.png"), width=150)
        except:
            st.image("https://img.icons8.com/clouds/200/energy-usage.png", width=100)
    
    st.title("EcoPrint Mobile")
    
    if not st.session_state.admin_mode:
        pwd = st.text_input("Password Admin", type="password")
        if st.button("Ativar Modo Edição"):
            check_login(pwd)
    else:
        st.success("🔓 Modo Admin Ativo")
        if st.button("Sair (Modo Público)"):
            logout()
    
    st.divider()
    st.markdown(f"""
        <div class="sidebar-footer">
            Projeto desenvolvido por <b>M4xW3b</b><br>
            📩 <i>Sugestões: geral@wintech.pt</i>
        </div>
    """, unsafe_allow_html=True)

# --- ABAS PRINCIPAIS ---
st.subheader("🏷️ Gestão de Etiquetas de Eficiência Energética")

if st.session_state.admin_mode:
    abas = st.tabs(["🏠 Início", "🖼️ Galeria", "🖨️ Impressão", "📥 Registo"])
else:
    abas = st.tabs(["🏠 Início", "🖼️ Galeria", "🖨️ Impressão"])

# --- ABA 0: LANDING PAGE ---
with abas[0]:
    st.markdown("""
        <div class="landing-hero">
            <h1>Projeto EcoPrint</h1>
            <p>Plataforma Centralizada para Impressão e Gestão SIRIUS</p>
        </div>
    """, unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 🎯 Finalidade")
        st.write("O **EcoPrint** visa otimizar o processo de etiquetagem energética, permitindo o acesso imediato a etiquetas normalizadas através da nuvem, eliminando erros de escala e facilitando a mobilidade dos técnicos.")
    with c2:
        st.markdown("### 🚀 Funcionamento")
        st.write("1. **Localize** o código SIRIUS na Galeria.\n2. **Introduza** o código na aba de Impressão.\n3. **Imprima** diretamente em A4 com medidas reais (6.5cm x 13.5cm).")

# --- ABA 1: GALERIA ---
with abas[1]:
    st.markdown("### Histórico de Etiquetas")
    res_galeria = supabase.table("etiquetas").select("*").order("created_at", desc=True).execute()
    if res_galeria.data:
        cols = st.columns(3)
        for idx, item in enumerate(res_galeria.data):
            with cols[idx % 3]:
                descricao = item.get('descricao', 'Sem descrição disponível')
                st.markdown(f"""<div class='galeria-card'>
                    <img src='{item['imagem_url']}' style='width:100%; border-radius:5px;'>
                    <p style='margin-top:10px; font-weight:bold; color:#007bff; margin-bottom:2px;'>{item['codigo']}</p>
                    <p style='font-size:0.85em; color:#666;'>{descricao}</p>
                </div>""", unsafe_allow_html=True)
                if st.session_state.admin_mode:
                    if st.button(f"Eliminar {item['codigo']}", key=f"del_{item['id']}"):
                        supabase.table("etiquetas").delete().eq("id", item['id']).execute()
                        st.rerun()

# --- ABA 2: IMPRESSÃO ---
with abas[2]:
    st.markdown("### Preparar Folha A4")
    col_a, col_b, col_c = st.columns(3)
    with col_a: c1 = st.text_input("Código 1", key="prn1")
    with col_b: c2 = st.text_input("Código 2", key="prn2")
    with col_c: c3 = st.text_input("Código 3", key="prn3")
    
    if st.button("🖨️ Abrir Janela de Impressão"):
        cods_selecionados = [c.strip() for c in [c1, c2, c3] if c.strip()]
        if cods_selecionados:
            lista_final = []
            for cod in cods_selecionados:
                r = supabase.table("etiquetas").select("*").eq("codigo", cod).execute()
                if r.data: lista_final.append(r.data[0])
            
            if lista_final:
                st.components.v1.html(imprimir_direto_html(lista_final), height=0, width=0)
                st.success("A preparar layout...")
            else:
                st.error("Nenhum dos códigos introduzidos foi encontrado.")

# --- ABA 3: REGISTO (ADMIN) ---
if st.session_state.admin_mode:
    with abas[3]:
        st.markdown("### Novo Registo de Etiqueta")
        reg_c1, reg_c2 = st.columns([1, 2])
        with reg_c1: novo_cod = st.text_input("Código Sirius")
        with reg_c2: nova_desc = st.text_input("Descrição / Equipamento")
        nova_img = st.file_uploader("Upload da Imagem", type=['jpg','jpeg','png'])
        
        if st.button("🚀 Gravar Dados"):
            if novo_cod and nova_img:
                with st.spinner("A validar e processar..."):
                    if upload_para_nuvem(nova_img, novo_cod, nova_desc):
                        st.success("Registo concluído!")
                        st.rerun()
            else:
                st.warning("Código e imagem são obrigatórios.")


