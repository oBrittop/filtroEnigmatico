import pandas as pd
import pywhatkit
import time
import re

caminho = "resultados_prospeccao/leads_prontos_venda.csv"
df = pd.read_csv(caminho)

print("Iniciando o Agente do WhatsApp...")
print("⚠️ ATENÇÃO: Deixe o WhatsApp Web já logado no seu Google Chrome.")
print("Não mexa no teclado ou mouse enquanto a janela abrir e enviar a mensagem!\n")

for index, row in df.iterrows():
    telefone = str(row['phone'])
    mensagem = str(row['abordagem_whatsapp'])
    nome = str(row['title'])
    
    telefone_limpo = re.sub(r'[^0-9+]', '', telefone)
    
    # Pula se não tiver número válido ou se a IA falhou ao criar a mensagem
    if len(telefone_limpo) < 10 or mensagem == 'nan' or "Erro ao gerar" in mensagem:
        print(f"⏭️ Pulando: {nome} (Sem telefone válido ou mensagem vazia).")
        continue
        
    print(f"\nEnviando para {nome} ({telefone_limpo})...")
    
    try:
       
        pywhatkit.sendwhatmsg_instantly(
            phone_no=telefone_limpo, 
            message=mensagem, 
            wait_time=20, 
            tab_close=True, 
            close_time=5
        )
        print(f"✅ Enviado com sucesso para {nome}!")
        
        
        print("Pausando 15s para não ativar o bloqueio de spam do Meta...")
        time.sleep(15)
        
    except Exception as e:
        print(f"❌ Erro ao enviar para {nome}: {e}")

print("\n🚀 Disparos finalizados!")
