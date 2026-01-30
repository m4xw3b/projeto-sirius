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

# --- 2. FUNÇÕES DE SUPORTE (LÓGICA) ---

def criar_folha_a4_cloud(lista_dados):
    """Monta a folha A4 usando URLs da nuvem."""
    largura_a4, altura_a4 = 3508, 2480
    dpi = 300
    largura_px = int((6.5 / 2.54) * dpi)
    altura_px = int((13.5 / 2.54) * dpi)
    margem_e_espaco = 150

    folha = Image.new('RGB', (largura_a4, altura_a4), 'white')
    desenho = ImageDraw.Draw(folha)

    try:
        fonte = ImageFont.truetype("arial.ttf", 60)
    except:
        fonte = ImageFont.load_default()

    for i, item in enumerate(lista_dados):
        try:
            # item['imagem_url'] vem da base de dados
            response = requests.get(item['imagem_url'])
            img = Image.open(BytesIO(response.content)).convert("RGB").resize((largura_px, altura_px))
            
            pos_x = margem_e_espaco + (i * (largura_px + 100))
            pos_y = (altura_a4 - altura_px) // 2
            
            folha.paste(img, (pos_x, pos_y))
            
            texto_y = pos_y + altura_px + 40
            desenho.text((pos_x + 50, texto_y), f"SIRIUS: {item['codigo']}", fill="black", font=fonte)
        except Exception as e:
            st.error(f"Erro ao processar imagem {i+1}: {e}")

    # Converte para bytes para o Streamlit permitir download
    buf = io.BytesIO()
    folha.save(buf, format="JPEG", quality=95)
    return buf.getvalue()

def upload_para_nuvem(imagem_file, codigo):
    """Faz o upload para o Storage e guarda o link na Tabela SQL."""
    try:
        nome_ficheiro = f"{codigo}.jpg"
        conteudo = imagem_file.getvalue()
        
        # Upload para o Bucket (imagens_sirius)
        supabase.storage.from_("imagens_sirius").upload(
            path=nome_ficheiro,
            file=conteudo,
            file_options={"content-type": "image/jpeg", "upsert": "true"}
        )
        
        # Obter URL pública
        url_publica = supabase.storage.from_("imagens_sirius").get_public_url(nome_ficheiro)
        
        # Inserir na tabela (etiquetas)
        dados = {"codigo": codigo, "imagem_url": url_publica}
        supabase.table("etiquetas").insert(dados).execute()
        return url_publica
    except Exception as e:
        st.error(f"Erro no processo de upload: {e}")
        return None

# --- 3. INTERFACE UTILIZADOR (STREAMLIT) ---

st.set_page_config(page_title="SIRIUS Cloud v2.0", layout="wide")
st.title("🏷️ Sistema SIRIUS - Etiquetas Energéticas")

tab_reg, tab_imp = st.tabs(["📥 Registar Nova Etiqueta", "🖨️ Gerar Impressão A4"])

# ABA DE REGISTO
with tab_reg:
    st.header("Upload para a Base de Dados")
    col1, col2 = st.columns(2)
    
    with col1:
        cod_novo = st.text_input("Atribuir Código Sirius:", placeholder="Ex: 3988499")
    with col2:
        arq_novo = st.file_uploader("Selecionar Imagem:", type=['jpg', 'jpeg', 'png'])
        
    if st.button("🚀 Gravar na Nuvem"):
        if cod_novo and arq_novo:
            with st.spinner("A processar e a guardar..."):
                url_res = upload_para_nuvem(arq_novo, cod_novo)
                if url_res:
                    st.success(f"Etiqueta {cod_novo} guardada com sucesso!")
                    st.image(url_res, width=300)
        else:
            st.warning("Por favor, preencha o código e selecione uma imagem.")

# ABA DE IMPRESSÃO
with tab_imp:
    st.header("Consulta e Impressão")
    st.write("Introduza até 3 códigos para montar a folha A4:")
    
    c_a, c_b, c_c = st.columns(3)
    with c_a: cod1 = st.text_input("Código 1", key="imp1")
    with c_b: cod2 = st.text_input("Código 2", key="imp2")
    with c_c: cod3 = st.text_input("Código 3", key="imp3")
    
    codigos_busca = [c.strip() for c in [cod1, cod2, cod3] if c.strip()]
    
    if st.button("🔍 Gerar Folha para Impressão"):
        if codigos_busca:
            with st.spinner("A consultar base de dados e a montar folha..."):
                dados_encontrados = []
                for cb in codigos_busca:
                    res = supabase.table("etiquetas").select("*").eq("codigo", cb).execute()
                    if res.data:
                        dados_encontrados.append(res.data[0])
                    else:
                        st.error(f"O código {cb} não foi encontrado na base de dados.")
                
                if dados_encontrados:
                    folha_final = criar_folha_a4_cloud(dados_encontrados)
                    st.image(folha_final, caption="Pré-visualização do A4", use_container_width=True)
                    
                    st.download_button(
                        label="📥 Descarregar JPEG para Imprimir",
                        data=folha_final,
                        file_name="etiquetas_sirius_a4.jpg",
                        mime="image/jpeg"
                    )
        else:
            st.info("Introduza pelo menos um código válido.")
