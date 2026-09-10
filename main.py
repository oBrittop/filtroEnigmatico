import os 
from dotenv import load_dotenv
from langchain_community.tools import DuckDuckGoSearchRun
from crewai.tools import BaseTool
from crewai import Agent, Task, Crew, LLM

pasta_resultados = 'resultados_prospeccao'
if not os.path.exists(pasta_resultados):
    os.makedirs(pasta_resultados)
    print(f" Pasta '{pasta_resultados}' criada com sucesso!")
    
    
load_dotenv()
chave_api = os.getenv("GEMINI_API_KEY")

cerebro_gemini = LLM(
    model="gemini-3.6-flash",
    api_key=chave_api
)


#  O Jeito Nativo: Criando a ferramenta como uma Classe do CrewAI
class PesquisaWebTool(BaseTool):
    name: str = "Pesquisa na Web"
    description: str = "Útil para pesquisar informações atualizadas, sites e contatos de empresas na internet."

    def _run(self, query: str) -> str:
        buscador = DuckDuckGoSearchRun()
        return buscador.run(query)

ferramenta_busca = PesquisaWebTool()


agente_pesquisador = Agent(
    role='Especialista em Inteligência de Mercado Local',
    goal='Encontrar empresas na internet, identificar se possuem site e extrair informações de contato',
    backstory='Você é um estrategista de vendas B2B implacável. Sua especialidade é varrer a internet para encontrar negócios locais, analisar rapidamente se eles têm um site profissional ou um perfil bem estruturado no Google, e separar os contatos para a equipe de prospecção.',
    verbose=True,
    allow_delegation=False,
    tools=[ferramenta_busca], 
    llm=cerebro_gemini,
    max_rpm=4
)

caminho_arquivo = os.path.join(pasta_resultados, 'leads_autoescolas.csv')

tarefa_mineracao = Task(
    description='Pesquise na internet por 2 autoescolas na região do Riacho Fundo, no Distrito Federal. Para cada empresa encontrada, você deve identificar: 1. O nome da empresa. 2. Se ela possui um site próprio ativo. 3. O telefone de contato ou WhatsApp.',
    expected_output='Um arquivo estruturado em CSV contendo as seguintes colunas: Nome da Empresa, Possui Site? (Sim/Não), URL do Site, Telefone. Formate o resultado estritamente em CSV, separado por vírgulas, sem textos adicionais, para ser lido no Excel.',
    agent=agente_pesquisador,
    output_file=caminho_arquivo # O resultado do agente será salvo aqui!
)


equipe_prospeccao = Crew(
    agents=[agente_pesquisador],
    tasks=[tarefa_mineracao],
    verbose=True
)

print(" Iniciando a pesquisa autônoma...")
resultado = equipe_prospeccao.kickoff()
print(f" Pesquisa concluída! Arquivo salvo em: {caminho_arquivo}")