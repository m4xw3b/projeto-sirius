🏷️ EcoPrint Mobile: Conformidade Legal UE 2026
O EcoPrint Mobile é uma plataforma centralizada para gestão e impressão de etiquetas de eficiência energética, desenvolvida especificamente para responder aos Regulamentos Delegados (UE) 2023/1670 e 2023/1669.

Desde 20 de junho de 2025, smartphones e tablets comercializados na União Europeia são obrigados a exibir informações detalhadas sobre classe energética, índice de reparabilidade e durabilidade. Este projeto facilita o cumprimento desta norma através de uma interface móvel ágil.

🚀 Funcionalidades Principais
🏠 Landing Page Legal: Enquadramento jurídico automático para informar utilizadores sobre as obrigações da norma.

🖼️ Galeria Cloud: Visualização de todas as etiquetas armazenadas com descrições detalhadas dos equipamentos.

🖨️ Motor de Impressão Milimétrica: Geração de layouts em escala real (6.5cm x 13.5cm) otimizados para folha A4 em modo paisagem.

📥 Registo Administrativo: Upload de imagens e metadados diretamente do telemóvel para a base de dados.

✏️ Edição por Pesquisa Direta: Ferramenta exclusiva para administradores editarem descrições ou códigos através de pesquisa instantânea.

🔐 Segurança: Separação de privilégios entre utilizadores (consulta/impressão) e administradores (gestão de dados).

🛠️ Stack Tecnológica
Linguagem: Python 3.x

Framework UI: Streamlit

Base de Dados & Storage: Supabase (PostgreSQL + Object Storage)

Design: CSS3 Customizado para dispositivos móveis.

Deploy: Streamlit Cloud integrado com GitHub.

📦 Configuração e Instalação
Para correr este projeto localmente ou fazer deploy na sua própria infraestrutura:

Clonar o repositório:

Bash
git clone https://github.com/teu-utilizador/ecoprint-mobile.git
cd ecoprint-mobile
Instalar dependências:

Bash
pip install -r requirements.txt
Configurar Segredos (.streamlit/secrets.toml):

Ini, TOML
SUPABASE_URL = "a_tua_url_do_supabase"
SUPABASE_KEY = "a_tua_chave_api_anon"
PASSWORD_ADMIN = "a_tua_password_de_gestao"
⚖️ Conformidade e Medidas de Impressão
O sistema força via CSS que cada etiqueta impressa mantenha as proporções legais exigidas. Ao imprimir, certifique-se de:

Selecionar a orientação Paisagem (Landscape).

Definir a escala em 100% (sem ajuste à página).

Assegurar que a impressora suporta a resolução mínima para leitura dos QR Codes das etiquetas.

✒️ Autor e Suporte
Desenvolvido por M4xW3b. 📩 Contacto para sugestões ou suporte: geral@wintech.pt
