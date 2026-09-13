import streamlit as st
import pandas as pd
import os
import re
import time
from dotenv import load_dotenv
from google import genai
import pywhatkit

load_dotenv()
chave = os.getenv("GEMINI_API_KEY")

if not chave:
    st.error("Chave da API do Gemini não encontrada no arquivo .env!")

st.set_page_config(page_title="Máquina de Vendas B2B", page_icon="🚀", layout="wide")
st.title("🚀 Máquina de Vendas B2B")

tab1, tab2, tab3 = st.tabs(["📂 1. Upload & Limpeza", "🧠 2. Inteligência Artificial", "📲 3. Disparo WhatsApp"])

if 'df_limpo' not in st.session_state:
    st.session_state.df_limpo = None
if 'df_com_ia' not in st.session_state:
    st.session_state.df_com_ia = None

# --- ABA 1: UPLOAD ---
with tab1:
    st.header("Upload da Planilha Bruta")
    st.write("Faça o upload do CSV gerado pelo extrator do Google Maps (Apify/Instant Data).")
    
    arquivo = st.file_uploader("Escolha um arquivo CSV", type=['csv'])
    
    if arquivo is not None:
        try:
            df_bruto = pd.read_csv(arquivo)
            st.success(f"Arquivo carregado com sucesso! ({len(df_bruto)} linhas)")
            
            colunas_desejadas = ['title', 'phone', 'address', 'website', 'categoryName']
            filtro_colunas = [col for col in colunas_desejadas if col in df_bruto.columns]
            df = df_bruto[filtro_colunas].copy()
            
            if 'phone' in df.columns:
                df = df.dropna(subset=['phone'])
            
            df = df.fillna("Não informado")
            st.session_state.df_limpo = df
            
            st.write(f"**Leads válidos (com telefone): {len(df)}**")
            st.dataframe(df)
            
        except Exception as e:
            st.error(f"Erro ao processar arquivo: {e}")

# --- ABA 2: IA ---
with tab2:
    st.header("Gerar Abordagem Personalizada com Gemini")
    
    if st.session_state.df_limpo is not None:
        df_ia = st.session_state.df_limpo.copy()
        
        limite = st.number_input("Quantos leads processar agora?", min_value=1, max_value=len(df_ia), value=min(3, len(df_ia)))
        
        if st.button("Iniciar Inteligência Artificial"):
            try:
                client = genai.Client(api_key=chave)
                mensagens_vendas = []
                
                barra = st.progress(0)
                status = st.empty()
                
                # Vamos iterar com limite
                df_processar = df_ia.head(limite).copy()
                total = len(df_processar)
                
                # Para consertar o bug do Streamlit index na hora de exibir a barra
                i = 0
                for index, row in df_processar.iterrows():
                    nome = row.get('title', 'Empresa')
                    site = row.get('website', 'Não informado')
                    
                    status.text(f"Analisando: {nome}...")
                    
                    prompt = f"""
                    Você é um consultor de tecnologia especialista em prospecção B2B via WhatsApp.
                    Seu alvo agora é uma autoescola chamada "{nome}". O site atual deles é: "{site}".
                    
                    Regras:
                    1. Se o site for "Não informado", focar em alertar a falta de presença online e oferecer criação de site + chatbot.
                    2. Se já tiverem site, elogie e ofereça apenas o Chatbot para agilizar o atendimento de alunos no WhatsApp.
                    3. Seja curto (máximo 4 linhas), casual (não seja robô).
                    4. Não use nomes falsos, diga apenas que é da área de tech.
                    
                    Responda APENAS com a mensagem final.
                    """
                    
                    resposta = client.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=prompt,
                    )
                    
                    mensagens_vendas.append(resposta.text.strip())
                    
                    i += 1
                    barra.progress(i / total)
                    time.sleep(3) # Limite de requisições da API
                
                df_processar['abordagem_whatsapp'] = mensagens_vendas
                st.session_state.df_com_ia = df_processar
                
                status.success("Abordagens geradas com sucesso!")
                st.dataframe(df_processar[['title', 'abordagem_whatsapp']])
                
                # Opção de download
                csv = df_processar.to_csv(index=False).encode('utf-8-sig')
                st.download_button("Baixar Planilha Pronta", data=csv, file_name="leads_prontos.csv", mime='text/csv')
                
            except Exception as e:
                st.error(f"Erro na API do Gemini: {e}")
    else:
        st.warning("Volte na Aba 1 e faça o upload da planilha limpa primeiro.")

# --- ABA 3: DISPARO WPP ---
with tab3:
    st.header("Disparador do WhatsApp Web")
    st.warning("ATENÇÃO: Este método exige que você não mexa no mouse ou teclado durante o envio. Deixe o WhatsApp Web logado no Chrome.")
    
    if st.session_state.df_com_ia is not None:
        df_disparo = st.session_state.df_com_ia.copy()
        st.write(f"Temos {len(df_disparo)} leads prontos para envio.")
        
        # Parâmetros de segurança para o PyWhatKit (Resolvendo o erro da bolinha vermelha)
        wait_time = st.slider("Tempo de espera para o Zap carregar (segundos)", 15, 40, 20)
        close_time = st.slider("Tempo de espera ANTES de fechar a aba (segundos) - *Aumente se der bolinha vermelha*", 3, 15, 6)
        
        if st.button("🚨 INICIAR DISPAROS"):
            status_envio = st.empty()
            
            for index, row in df_disparo.iterrows():
                telefone = str(row['phone'])
                mensagem = str(row.get('abordagem_whatsapp', ''))
                nome = str(row['title'])
                
                telefone_limpo = re.sub(r'[^0-9+]', '', telefone)
                
                if len(telefone_limpo) < 10 or mensagem == 'nan' or not mensagem:
                    st.toast(f"Pulado: {nome}")
                    continue
                
                status_envio.text(f"Enviando para {nome}...")
                
                try:
                    pywhatkit.sendwhatmsg_instantly(
                        phone_no=telefone_limpo, 
                        message=mensagem, 
                        wait_time=wait_time, 
                        tab_close=True, 
                        close_time=close_time
                    )
                    st.toast(f"Enviado: {nome}")
                    time.sleep(10)
                except Exception as e:
                    st.error(f"Erro ao enviar para {nome}: {e}")
            
            status_envio.success("Disparos finalizados!")
    else:
        st.warning("Você precisa gerar as mensagens na Aba 2 primeiro.")
