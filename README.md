

### 1. Documentação Técnica Inicial

Antes de instalar qualquer coisa, definimos as "Regras do Jogo" (Requisitos Técnicos e Funcionais).

#### 1.1 Fluxo de Dados (Architecture)

O sistema funcionará como um **middleware** inteligente. Ele recebe a mensagem, pensa, consulta dados e responde.

**O Fluxo:**

1. **Cliente** envia mensagem no WhatsApp.
2. **API de Conexão** (WPPConnect/Evolution) recebe e envia um POST (Webhook) para o nosso Backend.
3. **Backend (Python/FastAPI)** processa a mensagem.
4. **Agente AI (Gemini)** analisa a intenção (Dúvida? Pedido? Reclamação?).
* *Se for pedido:* A IA estrutura os dados.
* *Se for dúvida:* A IA responde baseada no contexto do cardápio.


5. **Banco de Dados** registra o pedido ou log da conversa.
6. **Backend** devolve a resposta texto para o WhatsApp do cliente.

#### 1.2 Stack Tecnológica Definida

* **Linguagem:** Python 3.10+
* **Web Framework:** FastAPI (Mais rápido e moderno que Flask, ideal para APIs assíncronas).
* **LLM (Cérebro):** Google Gemini API (`google-generativeai`).
* **Banco de Dados:** PostgreSQL (Produção) ou SQLite (Desenvolvimento inicial).
* **ORM (Gerenciador de Banco):** SQLAlchemy ou SQLModel.

---

### 2. Estrutura de Pastas (Scaffolding)

Para manter o projeto organizado ("Clean Architecture"), não faremos tudo em um arquivo só. A estrutura sugerida é:

```text
burger_bot/
│
├── .env                # Onde ficam as chaves secretas (API Key do Gemini, Senha do Banco)
├── .gitignore          # Para não subir arquivos sensíveis pro GitHub
├── requirements.txt    # Lista de dependências
├── README.md           # Documentação do projeto
│
├── src/
│   ├── main.py         # Ponto de entrada da aplicação (FastAPI app)
│   │
│   ├── config/         # Configurações globais (Conexão com Banco, Config da IA)
│   │   └── database.py
│   │   └── settings.py
│   │
│   ├── models/         # Tabelas do Banco de Dados (ORM)
│   │   └── pedido_model.py
│   │   └── produto_model.py
│   │
│   ├── services/       # A lógica pesada
│   │   ├── ai_service.py    # Onde o Gemini "mora"
│   │   └── order_service.py # Regras de negócio (Cálculo de total, estoque)
│   │
│   └── routes/         # As rotas da API (Webhooks do WhatsApp)
│       └── whatsapp_webhook.py

```

---

### 3. O arquivo `requirements.txt`

Essas são as bibliotecas que precisamos instalar para fazer essa máquina girar.

```text
# Framework Web (API)
fastapi==0.109.0
uvicorn==0.27.0      # Servidor para rodar o FastAPI
python-multipart     # Necessário para lidar com formulários/uploads se houver

# Inteligência Artificial (Gemini)
google-generativeai==0.3.2

# Banco de Dados
sqlalchemy==2.0.25
psycopg2-binary==2.9.9 # Driver para PostgreSQL
# aiosqlite            # Opcional: Se formos começar com SQLite

# Utilitários
python-dotenv==1.0.1   # Para ler o arquivo .env
pydantic==2.5.3        # Para validação de dados (Fundamental com IA)
requests==2.31.0       # Para fazer chamadas HTTP externas

```

---

### 4. Configuração Inicial do Ambiente

Agora, mão na massa no terminal. Se você estiver usando Windows (PowerShell) ou Linux/Mac, os comandos são levemente diferentes.

**Passo 1: Criar a pasta e o ambiente virtual**

```bash
mkdir burger_bot
cd burger_bot
python -m venv venv

```

**Passo 2: Ativar o ambiente virtual**

* *Windows:* `.\venv\Scripts\activate`
* *Linux/Mac:* `source venv/bin/activate`

**Passo 3: Criar o arquivo requirements e instalar**
Crie o arquivo `requirements.txt` com o conteúdo acima e rode:

```bash
pip install -r requirements.txt

```

---

### 5. Teste de Conexão com Gemini (POC)

Para validar se o ambiente está pronto, vamos criar um script simples (`test_gemini.py`) na raiz só para ver se ele responde como um atendente de hamburgueria.

Você precisará de uma API Key do Google AI Studio.

```python
# test_gemini.py
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Configuração da API (Você colocará sua chave no arquivo .env)
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("ERRO: Chave API não encontrada no .env")
    exit()

genai.configure(api_key=api_key)

# Configuração do Modelo
model = genai.GenerativeModel('gemini-1.5-flash')

# O Contexto (Prompt do Sistema)
prompt_sistema = """
Você é o atendente virtual da 'BurgerKing do Futuro'.
Seu tom é jovem e descolado.
Responda de forma breve.
O cliente acabou de dizer: 'Oi, tem lanche vegano?'
"""

response = model.generate_content(prompt_sistema)

print("RESPOSTA DO GEMINI:")
print(response.text)

```

---

### Próximo Passo

O ambiente está desenhado e documentado.

Para continuarmos, **você gostaria que eu criasse o arquivo `.env` de exemplo e o script para inicializarmos o Banco de Dados (agora sim o SQL/SQLAlchemy)**, ou prefere testar essa conexão com o Gemini primeiro?
