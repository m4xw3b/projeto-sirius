import streamlit as st
from supabase import create_client, Client
from PIL import Image, ImageDraw, ImageFont
import io

# --- CONFIGURAÇÃO DO SUPABASE ---
# Substitui com os dados que copiaste do teu painel API
SUPABASE_URL = "https://pfpfpdlugehsbqxwkgyj.supabase.co"
SUPABASE_KEY = "sb_publishable_NSDC9o5fCW2AxTnS_ZEjtw_358GaFpI"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def upload_etiqueta(imagem_file, codigo):
    """Guarda a imagem no Storage e o registo na Tabela."""
    try:
        nome_ficheiro = f"{codigo}.jpg"
        conteudo = imagem_file.getvalue()
        
        # 1. Upload para o Storage (Bucket: imagens_sirius)
        supabase.storage.from_("imagens_sirius").upload(
            path=f"{codigo}.jpg",
            file=conteudo,
            file_options={"content-type": "image/jpeg", "upsert": "true"}
        )
        
        # 2. Obter URL Pública
        url_publica = supabase.storage.from_("imagens_sirius").get_public_url(nome_ficheiro)
        
        # 3. Inserir na Tabela (Tabela: etiquetas)
        dados = {"codigo": codigo, "imagem_url": url_publica}
        supabase.table("etiquetas").insert(dados).execute()
        return url_publica
    except Exception as e:
        st.error(f"Erro no upload: {e}")
        return None

def buscar_etiquetas(lista_codigos):
    """Procura os códigos na base de dados."""
    resultados = []
    for cod in lista_codigos:
        res = supabase.table("etiquetas").select("*").eq("codigo", cod).execute()
        if res.data:
            resultados.append(res.data[0])
        else:
            st.warning(f"Código {cod} não encontrado na base de dados.")
    return resultados

# --- INTERFACE STREAMLIT ---
st.set_page_config(page_title="SIRIUS Cloud", layout="wide")
st.title("🏷️ Sistema SIRIUS Cloud v2.0")

tab_imp, tab_reg = st.tabs(["🖨️ Imprimir Etiquetas", "📥 Registar no Sistema"])

with tab_reg:
    st.subheader("Carregar nova etiqueta para a nuvem")
    c1, c2 = st.columns(2)
    with c1:
        novo_cod = st.text_input("Código Sirius (ex: S123):")
    with c2:
        nova_img = st.file_uploader("Foto da Etiqueta", type=['jpg', 'jpeg', 'png'])
    
    if st.button("Gravar na Base de Dados"):
        if novo_cod and nova_img:
            with st.spinner("A guardar..."):
                url = upload_etiqueta(nova_img, novo_cod)
                if url:
                    st.success(f"Sucesso! Código {novo_cod} guardado.")
                    st.image(url, width=200)
        else:
            st.error("Preencha o código e carregue uma imagem.")

with tab_imp:
    st.subheader("Gerar Folha A4 para Impressão")
    st.write("Introduza até 3 códigos que já estejam no sistema:")
    
    col_a, col_b, col_c = st.columns(3)
    cods_para_imprimir = []
    with col_a: c1 = st.text_input("Código 1:")
    with col_b: c2 = st.text_input("Código 2:")
    with col_c: c3 = st.text_input("Código 3:")
    
    botoes_codigos = [c for c in [c1, c2, c3] if c]

    if st.button("🔍 Gerar Pré-visualização"):
        if botoes_codigos:
            encontrados = buscar_etiquetas(botoes_codigos)
            if encontrados:
                st.write(f"Encontradas {len(encontrados)} imagens. A montar folha...")
                # Aqui podes inserir a tua função criar_a4_sirius anterior 
                # passando os links: encontrados[i]['imagem_url']
        else:
            st.error("Introduza pelo menos um código.")



