# Plataforma de Prospecção B2B Automática

Uma aplicação web desenvolvida em Streamlit para automatizar o processo de prospecção de vendas B2B (Business-to-Business) de ponta a ponta. 

O sistema realiza a extração de potenciais clientes do Google Maps, analisa a presença online de cada lead para gerar abordagens de venda personalizadas usando Inteligência Artificial e automatiza o envio das mensagens via WhatsApp Web.

## Arquitetura do Projeto

O fluxo de funcionamento da plataforma é dividido em três módulos principais:

1. **Captura de Leads (Apify):** Integração com a API da Apify para buscar empresas no Google Maps por nicho e região, retornando dados de contato (telefone) e presença digital (site).
2. **Inteligência Artificial (Google Gemini):** Avalia os dados extraídos de cada cliente. Se o cliente não possui site, gera um script de vendas focado em criação de sites e automação. Se possui, foca apenas na oferta do sistema/chatbot.
3. **Disparo Automático (PyWhatKit):** Interface conectada ao WhatsApp Web no navegador local para enviar as mensagens geradas de forma automatizada, respeitando pausas lógicas para evitar bloqueios de spam.

## Pré-requisitos

- Python 3.10 ou superior
- Google Chrome instalado (necessário para a automação do WhatsApp)
- WhatsApp com conta ativa conectada no WhatsApp Web
- Chave de API do Google Gemini
- Chave de API da Apify (Plano gratuito)

## Instalação

1. Clone ou baixe este repositório.
2. Navegue até a pasta raiz do projeto.
3. Instale as dependências executando o comando abaixo no terminal:

```bash
pip install -r requirements.txt
```

## Configuração

Crie um arquivo chamado `.env` na raiz do projeto e adicione suas chaves de API:

```text
GEMINI_API_KEY=sua_chave_do_gemini_aqui
APIFY_API_TOKEN=sua_chave_da_apify_aqui
```

## Como Usar

Para iniciar a interface web, execute o seguinte comando no terminal:

```bash
streamlit run app.py
```

O painel será aberto automaticamente no seu navegador. 
Siga o fluxo das três abas disponíveis no topo da página:
1. **Buscar Leads:** Defina o nicho e inicie a raspagem.
2. **Inteligência Artificial:** Defina a quantidade de contatos e gere as abordagens.
3. **Disparo WhatsApp:** Antes de clicar em Iniciar, garanta que seu WhatsApp Web está logado no Chrome e não mova o mouse durante os envios.

## Observações de Uso

- **Segurança da Conta:** O método de envio (PyWhatKit) simula o teclado e o mouse humano para evitar restrições pesadas do Meta. No entanto, é recomendado evitar envios em massas excessivas (centenas por hora) usando números novos ou pessoais sem aquecimento prévio.
- **Confiabilidade:** O disparo depende da performance do seu navegador. Se o carregamento das conversas no WhatsApp Web estiver muito lento, aumente o tempo de espera nas configurações disponíveis dentro da própria plataforma.
