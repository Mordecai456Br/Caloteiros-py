# Calotiei — API de Gerenciamento de Empréstimos

<div align="center">
  <img src="assets/begodex-logo.png" alt="Logo Begodex" width="220" />
  <p><strong>Um produto do ecossistema Howny Payments • Grupo Begodex</strong></p>
</div>

---

##  Sobre o Projeto

O **Calotiei** é uma API RESTful desenvolvida em Python com **FastAPI** voltada para o **gerenciamento completo do ciclo de vida de empréstimos pessoais e recebíveis**. O sistema permite controlar desde o cadastro de clientes e análise de solicitações de crédito até a concessão de empréstimos, geração automatizada de parcelas, acompanhamento de vencimentos e baixa/conciliação de pagamentos via Pix.

### 🏛️ Ecossistema Howny Payments & Grupo Begodex

O **Calotiei** integra o projeto **Howny Payments** — uma plataforma e suíte de APIs projetada para lidar com grandes volumes de indicadores, métricas e operações numéricas, atuando especificamente como a **subdivisão financeira** responsável pelo controle de crédito, fluxo de recebíveis e adimplência.

Toda a iniciativa faz parte e é mantida pelo grupo **Begodex**, unindo padronização arquitetural, rastreabilidade financeira e automação de processos de cobrança.

---

##  Funcionalidades

- **👤 Gestão de Usuários (`/users`)**
  - Cadastro, consulta individual, atualização parcial e listagem paginada.
  - Filtros por nome (`name`), busca textual em múltiplos campos (`search` em nome, telefone e e-mail) e intervalo de datas de cadastro.
- **📝 Solicitações de Empréstimo (`/loan-requests`)**
  - Abertura de solicitações informando valor pretendido, chave Pix, quantidade de parcelas e data do primeiro vencimento.
  - Fluxo dedicado de decisão de crédito com endpoints exclusivos para **aprovar** (`PATCH /loan-requests/{id}/approve`) e **negar** (`PATCH /loan-requests/{id}/deny`), impedindo alterações indevidas de status.
  - **Automação na aprovação:** ao aprovar uma solicitação, o sistema cria automaticamente o contrato de empréstimo (`Loan`) com status `open` e gera todas as parcelas (`Installments`) com cálculo automático de centavos e datas de vencimento mensais.
- **💰 Contratos de Empréstimo (`/loans`)**
  - Registro e acompanhamento do valor principal (`principal_amount`), total contratado a receber (`total_to_receive`), montante já recebido (`amount_received`) e evolução automática de status (`open` → `in progress` → `paid`).
  - Filtros combináveis por cliente (`user_id`), faixa de valores (`min_amount`, `max_amount`), período de concessão e situação (`active`, `open`, `in progress`, `paid`).
- **📅 Controle de Parcelas / Contas a Receber (`/installments`)**
  - Visão independente de todas as parcelas para facilitar telas de cobrança e contas a receber.
  - Filtros inteligentes por situação: `open`, `partially_paid`, `paid`, além dos filtros dinâmicos `pending` (em aberto ou parcialmente pagas) e `overdue` (parcelas vencidas e não quitadas).
  - Atualização de valor ou data de vencimento com recálculo automático do saldo total do empréstimo.
- **🧾 Registro e Conciliação de Pagamentos (`/payments`)**
  - Registro de pagamentos totais ou parciais vinculados às parcelas, com chave de comprovante (`receipt_key`) e chave Pix do pagador (`sender_pix_key`).
  - **Sincronização financeira automática:** cada pagamento registrado (ou estornado via `DELETE`) recalcula imediatamente o status da parcela (`open`, `partially_paid`, `paid`), a soma recebida (`amount_received`) e o status geral do empréstimo.
  - Trava de segurança contra pagamentos acima do saldo devedor da parcela.
- **🛡️ Padronização de Erros, Paginação e Observabilidade**
  - Respostas paginadas padronizadas (`items` + `pagination: { page, limit, total, pages }`).
  - Tratamento centralizado de exceções HTTP (`RESOURCE_NOT_FOUND`, `VALIDATION_ERROR`, `BUSINESS_RULE_VIOLATION`, `RESOURCE_CONFLICT`, `DATABASE_UNAVAILABLE`) sem expor detalhes internos do banco.
  - Middleware transversal com injeção de `X-Request-ID` e tempo de processamento (`X-Process-Time`).

---

## 🛠️ Stack Tecnológica

- **Linguagem:** Python 3.12+
- **Framework Web:** [FastAPI](https://fastapi.tiangolo.com/) + [Uvicorn](https://www.uvicorn.org/)
- **ORM & Banco de Dados:** [SQLAlchemy 2.0](https://www.sqlalchemy.org/) + PostgreSQL ([Supabase](https://supabase.com/) via Session Pooler IPv4)
- **Validação e Configurações:** [Pydantic v2](https://docs.pydantic.dev/) & `pydantic-settings`
- **Testes Automatizados:** [Pytest](https://docs.pytest.org/) + `FastAPI TestClient` (`httpx`) com banco em memória isolado
- **Qualidade & CI/CD:** Flake8 (PEP 8) + GitLab CI (`build`, `test`, `lint`)

### Arquitetura em Camadas

```text
app/
├── core/          # Configurações (.env), conexão com banco e exceções padronizadas
├── models/        # Entidades ORM do SQLAlchemy (mapeamento das tabelas do PostgreSQL)
├── schemas/       # Contratos de entrada/saída e paginação com Pydantic v2
├── repositories/  # Camada de acesso a dados e filtros SQL combináveis
├── services/      # Regras de negócio, validações financeiras e orquestração
├── routers/       # Endpoints HTTP REST organizados por domínio
└── main.py        # Ponto de entrada da aplicação, middlewares e exception handlers
```

---

##  Passo a Passo: Como Rodar o Projeto

### 1. Pré-requisitos
- **Python 3.11+** (recomendado Python 3.12)
- Acesso a uma instância PostgreSQL / projeto no **Supabase**

### 2. Clonar o repositório e criar o ambiente virtual

No terminal (PowerShell no Windows ou Bash no Linux/macOS):

```powershell
# Clonar o repositório
git clone <URL_DO_REPOSITORIO>
cd caloteiros-py

# Criar o ambiente virtual
python -m venv .venv

# Ativar o ambiente virtual (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Ou no Linux/macOS:
# source .venv/bin/activate
```

### 3. Instalar as dependências

```powershell
pip install -r requirements.txt
```

### 4. Configurar as variáveis de ambiente (`.env`)

Copie o arquivo de exemplo `.env.example` para `.env` na raiz do projeto:

```powershell
Copy-Item .env.example .env
```

Edite o arquivo `.env` com as credenciais do seu banco no Supabase (utilizando o host do **Session Pooler** para compatibilidade com IPv4):

```env
DB_HOST=aws-0-us-east-1.pooler.supabase.com
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres.hlcbbucomceymrcoqecp
DB_PASSWORD=sua_senha_aqui
```

### 5. Executar a aplicação

Você pode iniciar o servidor de desenvolvimento de qualquer uma das formas abaixo:

```powershell
# Opção 1: Executando o módulo principal
.\.venv\Scripts\python.exe -m app.main

# Opção 2: Executando o arquivo main.py da raiz
.\.venv\Scripts\python.exe main.py

# Opção 3: Diretamente via Uvicorn com hot-reload
.\.venv\Scripts\uvicorn.exe app.main:app --reload
```

O servidor ficará disponível em: `http://127.0.0.1:8000`

---

## 📚 Como Consultar a Documentação da API

Com a aplicação rodando localmente, o FastAPI disponibiliza automaticamente a documentação interativa completa com todos os endpoints, schemas, filtros e códigos de resposta:

1. **Swagger UI (Interativa — permite testar as rotas pelo navegador):**
   👉 [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
2. **ReDoc (Documentação visual detalhada):**
   👉 [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
3. **Especificação OpenAPI (JSON):**
   👉 [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)
4. **Coleção de Requisições HTTP (PyCharm / VS Code REST Client):**
   O arquivo [`test_main.http`](test_main.http) na raiz do projeto contém exemplos prontos de chamadas para todos os recursos e combinações de filtros (`query params`).
5. **Healthcheck da API e Banco de Dados:**
   👉 [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## 🧪 Como Rodar os Testes e o Linter

Os testes automatizados utilizam um banco de dados isolado em memória (`SQLite` via `dependency_overrides`), garantindo que nenhuma execução afete os dados reais do Supabase.

```powershell
# Executar toda a suíte de testes (38 testes)
.\.venv\Scripts\python.exe -m pytest -v

# Executar a verificação de estilo e sintaxe (Flake8)
.\.venv\Scripts\python.exe -m flake8 app tests
```

---

<div align="center">
  <sub>Desenvolvido para o projeto <strong>Howny Payments</strong> • <strong>Grupo Begodex</strong></sub>
</div>
