import os
import pandas as pd
from dotenv import load_dotenv
from google import genai
import time


load_dotenv()
chave = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=chave)

print("Iniciando a inteligência comercial B2B...")

caminho_entrada = "resultados_prospeccao/leads_limpos.csv"
df = pd.read_csv(caminho_entrada)


mensagens_vendas = []

# rodar apenas para os 3 primeiros leads para testar rápido e não gastar sua cota à toa.
# Quando você validar que ficou bom, podemos rodar para a tabela inteira!
limite_teste = 3

for index, row in df.head(limite_teste).iterrows():
    nome = row['title']
    site = row['website']
    
    print(f"Analisando: {nome}...")
    
    prompt = f"""
    Você é um consultor de tecnologia especialista em prospecção B2B via WhatsApp.
    Seu alvo agora é uma autoescola chamada "{nome}".
    O site atual deles é: "{site}".
    
    Regras da mensagem:
    1. Se o site for "Não informado", o foco principal da sua mensagem deve ser alertar que eles estão perdendo clientes por não terem um site/presença online, e oferecer a criação de um site + um sistema de atendimento automático.
    2. Se eles já tiverem um site (qualquer link), elogie a presença online deles e ofereça APENAS o nosso Sistema/Chatbot de Atendimento Automático, focando na dor de que "atender alunos manualmente no WhatsApp gasta muito tempo".
    3. Tem que ser curta (máximo 4 linhas) e casual, parecendo que foi escrita por um humano.
    4. Não se apresente com um nome falso, diga apenas que é da área de tecnologia.
    
    Responda APENAS com a mensagem de WhatsApp final, nada mais.
    """
    
    try:
        # Chama a API do Gemini
        resposta = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt,
        )
        mensagens_vendas.append(resposta.text.strip())
        
        # Pausa de 3 segundos para respeitar o limite de velocidade da API gratuita (5 RPM)
        time.sleep(3)
        
    except Exception as e:
        print(f"Erro na análise de {nome}: {e}")
        mensagens_vendas.append("Erro ao gerar mensagem")


#testando só os 3 primeiros, cortamos o dataframe para salvar
df_teste = df.head(limite_teste).copy()
df_teste['abordagem_whatsapp'] = mensagens_vendas

caminho_saida = "resultados_prospeccao/leads_prontos_venda.csv"
df_teste.to_csv(caminho_saida, index=False, encoding='utf-8-sig')

print(f"\nSucesso! Script gerou mensagens de venda para {limite_teste} leads.")
print(f"Arquivo final salvo em: {caminho_saida}")
