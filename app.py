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
        /* Sidebar e Inputs */
        [data-testid="stSidebarUserContent"] > div:first-child { display: flex; flex-direction: column; align-items: center; }
        div[data-testid="stSidebar"] div[data-baseweb="input"] { border: 2px solid #007bff !important; border-radius: 10px !important; width: 180px !important; margin: 0 auto !important; }
        [data-testid="stSidebar"] .stButton { display: flex; justify-content: center; width: 100%; margin-top: 10px; }
        [data-testid="stSidebar"] .stButton button { width: auto !important; padding: 0 20px !important; }
        
        /* Rodapé Fixo */
        .sidebar-footer { position: fixed; bottom: 0; left: 0; width: 100%; background-color: #f8f9fa; border-top: 1px solid #ddd; padding: 15px 0; text-align: center; font-size: 12px; color: #666; z-index: 999; }
        
        /* Galeria e Cards */
        .galeria-card { border: 1px solid #e0e0e0; border-radius: 10px; padding: 10px; background-color: white; text-align: center; margin-bottom: 20px; min-height: 330px; }
        
        /* Landing Page */
        .landing-hero { background: linear-gradient(90deg, #004aad, #00c6ff); color: white; padding: 40px; border-radius: 15px; margin-bottom: 25px; text-align: center; }
        </style>
    """, unsafe_allow_html=True)

# --- 4. FUNÇÕES DE SUPORTE ---
def verificar_codigo_existente(codigo, excluir_id=None):
    query = supabase.table("etiquetas").select("codigo").eq("codigo", codigo)
    if excluir_id:
        query = query.neq("id", excluir_id)
    res = query.execute()
    return len(res.data) > 0

def upload_para_nuvem(imagem_file, codigo, descricao):
    try:
        if verificar_codigo_existente(codigo):
            st.error(f"❌ Erro: O código '{codigo}' já existe.")
            return False
        nome_ficheiro = f"{codigo}.jpg"
        conteudo = imagem_file.getvalue()
        supabase.storage.from_("imagens_sirius").upload(path=nome_ficheiro, file=conteudo, file_options={"content-type": "image/jpeg", "upsert": "true"})
        url_publica = supabase.storage.from_("imagens_sirius").get_public_url(nome_ficheiro)
        supabase.table("etiquetas").insert({"codigo": codigo, "imagem_url": url_publica, "descricao": descricao}).execute()
        return True
    except Exception as e:
        st.error(f"Erro no upload: {e}"); return False

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
    <body><div class="container">
    """
    for item in lista_dados:
        html_content += f'<div class="box"><img class="img-etiqueta" src="{item["imagem_url"]}"><div class="legenda">SIRIUS: {item["codigo"]}</div></div>'
    html_content += '</div><script>window.onload = function() { setTimeout(function() { window.print(); }, 800); };</script></body></html>'
    return html_content

# --- 5. EXECUÇÃO DA INTERFACE ---
aplicar_design()

with st.sidebar:
    col_esq, col_logo, col_dir = st.columns([1, 2, 1])
    with col_logo:
        try: st.image(Image.open("ee_logo.png"), width=150)
        except: st.image("https://img.icons8.com/clouds/200/energy-usage.png", width=100)
    
    st.title("EcoPrint Mobile")
    if not st.session_state.admin_mode:
        pwd = st.text_input("Password Admin", type="password")
        if st.button("Ativar Modo Edição"): check_login(pwd)
    else:
        st.success("🔓 Modo Admin Ativo")
        if st.button("Sair (Modo Público)"): logout()
    
    st.divider()
    st.markdown('<div class="sidebar-footer">Projeto desenvolvido por <b>M4xW3b</b><br>📩 <i>geral@wintech.pt</i></div>', unsafe_allow_html=True)

# Definição das Abas (Aba Editar só aparece se for Admin)
if st.session_state.admin_mode:
    abas = st.tabs(["🏠 Início", "🖼️ Galeria", "🖨️ Impressão", "📥 Registo", "✏️ Editar"])
else:
    abas = st.tabs(["🏠 Início", "🖼️ Galeria", "🖨️ Impressão"])

# --- ABA 0: LANDING PAGE (APRESENTAÇÃO LEGAL) ---
with abas[0]:
    st.markdown("""
        <div class="landing-hero">
            <h1>EcoPrint: Conformidade Legal 2026</h1>
            <p>Implementação dos Regulamentos UE 2023/1670 e 2023/1669</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.info("""
    **Finalidade:** Este sistema responde à obrigatoriedade legal de etiquetagem energética para Smartphones e Tablets, 
    em vigor desde **20 de junho de 2025**. O EcoPrint garante que a informação de eficiência, reparabilidade e 
    durabilidade esteja visível e acessível em qualquer ponto de venda.
    """)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### ⚖️ Requisitos Obrigatórios")
        st.write("- **Classe Energética:** Escala A a G.\n- **Reparabilidade:** Índice de A a E.\n- **Bateria:** Ciclos de vida e autonomia.\n- **Resistência:** Proteção contra quedas e água.")
    with c2:
        st.markdown("### 🚀 Método de Funcionamento")
        st.write("1. **Consulta:** Localize o modelo na Galeria.\n2. **Seleção:** Introduza o código SIRIUS na aba de impressão.\n3. **Praticidade:** Imprima em formato A4 real a partir de qualquer telemóvel.")

# --- ABA 1: GALERIA ---
with abas[1]:
    st.markdown("### Histórico de Etiquetas")
    res = supabase.table("etiquetas").select("*").order("created_at", desc=True).execute()
    if res.data:
        cols = st.columns(3)
        for idx, item in enumerate(res.data):
            with cols[idx % 3]:
                st.markdown(f"""<div class='galeria-card'>
                    <img src='{item['imagem_url']}' style='width:100%; border-radius:5px;'>
                    <p style='margin-top:10px; font-weight:bold; color:#007bff; margin-bottom:2px;'>{item['codigo']}</p>
                    <p style='font-size:0.85em; color:#666;'>{item.get('descricao', 'S/ Descrição')}</p>
                </div>""", unsafe_allow_html=True)
                if st.session_state.admin_mode:
                    if st.button(f"🗑️ Eliminar {item['codigo']}", key=f"del_{item['id']}"):
                        supabase.table("etiquetas").delete().eq("id", item['id']).execute(); st.rerun()

# --- ABA 2: IMPRESSÃO ---
with abas[2]:
    st.markdown("### Preparar Folha de Impressão")
    ca, cb, cc = st.columns(3)
    with ca: c1 = st.text_input("Código 1", key="imp1")
    with cb: c2 = st.text_input("Código 2", key="imp2")
    with cc: c3 = st.text_input("Código 3", key="imp3")
    if st.button("🖨️ Gerar e Imprimir"):
        cods = [c.strip() for c in [c1, c2, c3] if c.strip()]
        if cods:
            lista = [r.data[0] for c in cods if (r := supabase.table("etiquetas").select("*").eq("codigo", c).execute()).data]
            if lista:
                st.components.v1.html(imprimir_direto_html(lista), height=0, width=0)
                st.info("A preparar layout de impressão...")
            else: st.error("Códigos não encontrados.")

# --- ABAS RESTRITAS A ADMIN ---
if st.session_state.admin_mode:
    # --- ABA 3: REGISTO ---
    with abas[3]:
        st.markdown("### Novo Registo de Etiqueta")
        r1, r2 = st.columns([1, 2])
        with r1: n_cod = st.text_input("Código Sirius")
        with r2: n_des = st.text_input("Descrição / Modelo")
        n_img = st.file_uploader("Upload da Imagem", type=['jpg','png','jpeg'])
        if st.button("🚀 Gravar Dados"):
            if n_cod and n_img:
                if upload_para_nuvem(n_img, n_cod, n_des): st.success("Registo concluído!"); st.rerun()
            else: st.warning("Por favor, preencha o código e carregue uma imagem.")

    # --- ABA 4: EDITAR ---
    with abas[4]:
        st.markdown("### Atualizar Dados Existentes")
        res_edit = supabase.table("etiquetas").select("*").order("codigo").execute()
        if res_edit.data:
            lista_codigos = [item['codigo'] for item in res_edit.data]
            selecionado = st.selectbox("Selecione a etiqueta para editar:", lista_codigos)
            dados_atuais = next(item for item in res_edit.data if item['codigo'] == selecionado)
            
            with st.form("form_edicao"):
                ed_codigo = st.text_input("Código Sirius", value=dados_atuais['codigo'])
                ed_desc = st.text_input("Descrição / Modelo", value=dados_atuais.get('descricao', ''))
                if st.form_submit_button("✅ Guardar Alterações"):
                    if verificar_codigo_existente(ed_codigo, excluir_id=dados_atuais['id']):
                        st.error("Este código já existe noutro registo.")
                    else:
                        supabase.table("etiquetas").update({
                            "codigo": ed_codigo,
                            "descricao": ed_desc
                        }).eq("id", dados_atuais['id']).execute()
                        st.success("Dados atualizados!"); st.rerun()

