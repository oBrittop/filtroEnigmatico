import pandas as pd
import os

print("Limpando a base de dados bruta...")
df_bruto = pd.read_csv("csv_brutos/autoescola2.csv")

colunas_desejadas = [
    'title',               # Nome do local
    'phone',               # Telefone formatado
    'address',             # Endereço completo
    'website',             # Site
    'categoryName',        # Categoria/Tipo principal do negócio
]


filtro_colunas = [col for col in colunas_desejadas if col in df_bruto.columns]
df = df_bruto[filtro_colunas].copy()

df = df.dropna(subset=['phone'])

df = df.fillna("Não informado")

os.makedirs("resultados_prospeccao", exist_ok=True)

caminho_salvo = "resultados_prospeccao/leads_limpos.csv"
df.to_csv(caminho_salvo, index=False, encoding='utf-8-sig')

print(f"Sucesso! {len(df)} leads limpos e salvos em: {caminho_salvo}")
print(df.head(3))