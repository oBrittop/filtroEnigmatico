import streamlit as st
import pandas as pd
import os
import re
import time
from dotenv import load_dotenv
from google import genai
import pywhatkit
from apify_client import ApifyClient

# Carregar chaves
load_dotenv()
chave_gemini = os.getenv("GEMINI_API_KEY")
chave_apify = os.getenv("APIFY_API_TOKEN")

# Configuração da página
st.set_page_config(page_title="Máquina de Vendas B2B", page_icon="🚀", layout="wide")

def check_password():
    """Retorna True se o usuário tiver inserido a senha correta."""
    if st.session_state.get("password_correct", False):
        return True

    # Pega a senha do .env (Se não existir, usa 'admin123' como padrão provisório)
    senha_correta = os.getenv("APP_PASSWORD", "admin123")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🔒 Acesso Restrito")
        st.write("Faça login para acessar a Máquina de Vendas.")
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        
        if st.button("Entrar"):
            # Libera o acesso para 'admin' com a senha do .env
            if usuario == "admin" and senha == senha_correta:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("😕 Usuário ou senha incorretos.")
                
    return False

# Se a senha não estiver correta, para a execução do app aqui.
if not check_password():
    st.stop()

# ==========================================
# APP PRINCIPAL (Só roda se passar do login)
# ==========================================
st.title("🚀 Máquina de Vendas B2B")

if not chave_gemini:
    st.error("⚠️ Chave do Gemini (GEMINI_API_KEY) não encontrada no arquivo .env!")

# Abas do App
tab1, tab2, tab3 = st.tabs(["🔍 1. Buscar Leads (Apify)", "🧠 2. Inteligência Artificial", "📲 3. Disparo WhatsApp"])

# Inicializando variaveis de sessão
if 'df_limpo' not in st.session_state:
    st.session_state.df_limpo = None
if 'df_com_ia' not in st.session_state:
    st.session_state.df_com_ia = None

# --- ABA 1: UPLOAD OU APIFY ---
with tab1:
    st.header("Captura de Leads")
    
    modo = st.radio("Como você quer trazer os clientes hoje?", ["Busca Automática (Apify)", "Upload de Planilha CSV"])
    
    if modo == "Upload de Planilha CSV":
        arquivo = st.file_uploader("Escolha o arquivo CSV bruto", type=['csv'])
        if arquivo is not None:
            df_bruto = pd.read_csv(arquivo)
            st.success(f"Arquivo carregado com sucesso! ({len(df_bruto)} linhas)")
            
            colunas_desejadas = ['title', 'phone', 'address', 'website', 'categoryName']
            filtro_colunas = [col for col in colunas_desejadas if col in df_bruto.columns]
            df = df_bruto[filtro_colunas].copy()
            
            if 'phone' in df.columns:
                df = df.dropna(subset=['phone'])
            
            df = df.fillna("Não informado")
            st.session_state.df_limpo = df
            st.dataframe(df)

    elif modo == "Busca Automática (Apify)":
        if not chave_apify:
            st.warning("⚠️ Você precisa adicionar a APIFY_API_TOKEN no arquivo .env para usar este modo.")
        else:
            st.write("Digite o nicho e a região para que o robô busque no Google Maps em tempo real.")
            
            busca = st.text_input("Ex: 'Clínica Odontológica no Rio de Janeiro'")
            limite_leads = st.number_input("Máximo de empresas para buscar", min_value=1, max_value=200, value=20)
            
            if st.button("Iniciar Raspagem Automática"):
                if not busca:
                    st.error("Digite o que deseja buscar.")
                else:
                    with st.spinner(f"Acordando o robô da Apify e buscando por '{busca}'... (pode demorar 1-3 minutos)"):
                        try:
                            # Conecta na Apify
                            apify_client = ApifyClient(chave_apify)
                            
                            # Configura a busca para o Google Maps Scraper da Apify
                            run_input = {
                                "searchStringsArray": [busca],
                                "maxCrawledPlacesPerSearch": limite_leads,
                                "language": "pt",
                            }
                            
                            # Roda o Google Maps Scraper (Actor ID comum)
                            # O actor 'compass/crawler-google-places' é muito usado, mas 'drobnikj/crawler-google-places' também. 
                            # Se der erro de permissão, o usuário pode trocar para o ID do actor que ele alugou.
                            run = apify_client.actor("compass/crawler-google-places").call(run_input=run_input)
                            
                            # Extrai os resultados
                            itens = apify_client.dataset(run["defaultDatasetId"]).list_items().items
                            
                            df_bruto = pd.DataFrame(itens)
                            st.success(f"Extração concluída! {len(df_bruto)} locais encontrados.")
                            
                            # Limpeza e Padronização
                            # A Apify retorna colunas variáveis, vamos tentar pegar as principais
                            if not df_bruto.empty:
                                if 'title' not in df_bruto.columns: df_bruto['title'] = df_bruto.get('name', 'Sem nome')
                                if 'phone' not in df_bruto.columns: df_bruto['phone'] = df_bruto.get('phoneUnformatted', df_bruto.get('phoneNumber', ''))
                                
                                colunas_desejadas = ['title', 'phone', 'address', 'website', 'categoryName']
                                filtro_colunas = [col for col in colunas_desejadas if col in df_bruto.columns]
                                df = df_bruto[filtro_colunas].copy()
                                
                                if 'phone' in df.columns:
                                    df = df.dropna(subset=['phone'])
                                
                                df = df.fillna("Não informado")
                                st.session_state.df_limpo = df
                                st.write(f"**Leads válidos (com telefone): {len(df)}**")
                                st.dataframe(df)
                            else:
                                st.error("A busca retornou zero resultados.")
                        except Exception as e:
                            st.error(f"Erro na extração via Apify: {e}")
                            st.info("Dica: Verifique se a sua chave APIFY_API_TOKEN está correta ou se a conta tem limite disponível.")

# --- ABA 2: IA ---
with tab2:
    st.header("Gerar Abordagem Personalizada com Gemini")
    
    if st.session_state.df_limpo is not None and not st.session_state.df_limpo.empty:
        df_ia = st.session_state.df_limpo.copy()
        
        limite = st.number_input("Quantos leads processar com a IA agora?", min_value=1, max_value=len(df_ia), value=min(3, len(df_ia)))
        
        if st.button("Iniciar Inteligência Artificial"):
            try:
                client = genai.Client(api_key=chave_gemini)
                mensagens_vendas = []
                
                barra = st.progress(0)
                status = st.empty()
                
                df_processar = df_ia.head(limite).copy()
                total = len(df_processar)
                i = 0
                
                for index, row in df_processar.iterrows():
                    nome = row.get('title', 'Empresa')
                    site = row.get('website', 'Não informado')
                    
                    status.text(f"Analisando site de: {nome}...")
                    
                    prompt = f"""
                    Você é um consultor de tecnologia especialista em prospecção B2B via WhatsApp.
                    Seu alvo agora é uma empresa chamada "{nome}". O site atual deles é: "{site}".
                    
                    Regras:
                    1. Se o site for "Não informado", foque em alertar a falta de presença online (estão perdendo clientes) e ofereça a criação de um site + sistema de automação.
                    2. Se já tiverem site, elogie e ofereça apenas a Automação/Chatbot de WhatsApp para agilizar o atendimento.
                    3. Seja curto (máximo 4 linhas), direto e pareça humano.
                    4. Não use nomes falsos, diga apenas que trabalha com tecnologia.
                    
                    Responda APENAS com a mensagem final.
                    """
                    
                    resposta = client.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=prompt,
                    )
                    
                    mensagens_vendas.append(resposta.text.strip())
                    
                    i += 1
                    barra.progress(i / total)
                    time.sleep(3) # Pausa para evitar rate limit da cota grátis
                
                df_processar['abordagem_whatsapp'] = mensagens_vendas
                st.session_state.df_com_ia = df_processar
                
                status.success("Abordagens geradas com sucesso!")
                st.dataframe(df_processar[['title', 'abordagem_whatsapp']])
                
                csv = df_processar.to_csv(index=False).encode('utf-8-sig')
                st.download_button("Baixar Planilha de Vendas Pronta", data=csv, file_name="leads_prontos.csv", mime='text/csv')
                
            except Exception as e:
                st.error(f"Erro na API do Gemini: {e}")
    else:
        st.warning("Vá na Aba 1 e traga alguns leads primeiro.")

# --- ABA 3: DISPARO WPP ---
with tab3:
    st.header("Disparador do WhatsApp Web")
    st.warning("ATENÇÃO: Não mexa no mouse ou teclado durante o envio. O WhatsApp Web precisa estar logado.")
    
    if st.session_state.df_com_ia is not None:
        df_disparo = st.session_state.df_com_ia.copy()
        st.write(f"Temos {len(df_disparo)} leads prontos para envio.")
        
        wait_time = st.slider("Espera do Zap carregar (segundos)", 15, 40, 20)
        close_time = st.slider("Espera antes de fechar a aba (segundos) - Evita bolinha vermelha", 3, 15, 6)
        
        if st.button("🚨 INICIAR DISPAROS"):
            status_envio = st.empty()
            
            for index, row in df_disparo.iterrows():
                telefone = str(row['phone'])
                mensagem = str(row.get('abordagem_whatsapp', ''))
                nome = str(row['title'])
                
                telefone_limpo = re.sub(r'[^0-9+]', '', telefone)
                
                if len(telefone_limpo) < 10 or not mensagem or mensagem.lower() == 'nan':
                    st.toast(f"Pulado: {nome}")
                    continue
                
                status_envio.text(f"Disparando para {nome}...")
                
                try:
                    pywhatkit.sendwhatmsg_instantly(
                        phone_no=telefone_limpo, 
                        message=mensagem, 
                        wait_time=wait_time, 
                        tab_close=True, 
                        close_time=close_time
                    )
                    st.toast(f"✅ Enviado: {nome}")
                    time.sleep(10) # Imita o atraso de digitação/respiração humana
                except Exception as e:
                    st.error(f"Erro ao enviar para {nome}: {e}")
            
            status_envio.success("Disparos finalizados!")
    else:
        st.warning("Vá na Aba 2 e gere as mensagens primeiro.")
