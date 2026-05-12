# 🧠 Focus Log API

> Backend de Log de Performance e Produtividade — Desafio Técnico

API REST desenvolvida em **Django + Django REST Framework** para registrar sessões de trabalho e analisar o nível de produtividade do desenvolvedor ou estudante.

---

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Tecnologias](#tecnologias)
- [Arquitetura](#arquitetura)
- [Como Rodar](#como-rodar)
- [Endpoints da API](#endpoints-da-api)
- [Exemplos de Uso](#exemplos-de-uso)
- [Testes](#testes)
- [Docker](#docker)
- [Estrutura de Pastas](#estrutura-de-pastas)
- [Decisões Técnicas](#decisões-técnicas)

---

## Visão Geral

O Focus Log API permite que desenvolvedores e estudantes registrem blocos de trabalho com informações sobre nível de foco, duração e contexto. Com base nos registros, a API entrega um **diagnóstico inteligente** com métricas, feedback personalizado e dicas de melhoria.

### Funcionalidades principais

- Registrar sessões de trabalho com nível de foco (1–5), duração e comentário
- Categorizar sessões (coding, reunião, estudo, etc.) e adicionar tags
- Receber diagnóstico completo com média de foco, tempo total, distribuição por nível, pontuação de produtividade e dicas personalizadas
- Filtrar registros por categoria e nível de foco

---

## Tecnologias

| Tecnologia | Versão | Uso |
|---|---|---|
| Python | 3.11+ | Linguagem principal |
| Django | 5.0.6 | Framework web |
| Django REST Framework | 3.15.2 | API REST |
| python-decouple | 3.8 | Variáveis de ambiente |
| SQLite | — | Banco de dados (dev) |
| Docker | — | Containerização |
| GitHub Actions | — | CI/CD |

---

## Arquitetura

O projeto segue uma arquitetura em camadas (Layered Architecture):

```
Cliente HTTP
     ↓
urls.py          → Roteamento de endpoints
     ↓
views.py         → Recebe request, orquestra, retorna response
     ↓
serializers.py   → Validação e transformação de dados
     ↓
services.py      → Lógica de negócio (diagnóstico)
     ↓
models.py        → Camada de dados (Django ORM)
     ↓
SQLite (banco)
```

**Por que essa separação?**
- **views.py** finas: só orquestram, não têm regras de negócio
- **services.py**: toda lógica de negócio, testável sem HTTP
- **serializers.py**: validação centralizada com mensagens claras

---

## Como Rodar

### Pré-requisitos

- Python 3.11 ou superior
- pip

### 1. Clone o repositório

```bash
git clone 
cd focus-log-api
```

### 2. Crie e ative o ambiente virtual

```bash
# Criar ambiente virtual
python -m venv venv

# Ativar (Linux/Mac)
source venv/bin/activate

# Ativar (Windows)
venv\Scripts\activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite o .env com seus valores (o padrão já funciona para dev)
```

### 5. Execute as migrations

```bash
python manage.py migrate
```

### 6. Inicie o servidor

```bash
python manage.py runserver
```

A API estará disponível em: **http://localhost:8000**

### (Opcional) Crie um superusuário para o Admin

```bash
python manage.py createsuperuser
# Acesse: http://localhost:8000/admin/
```

---

## Endpoints da API

### Base URL: `http://localhost:8000/api/v1`

---

### `POST /registro-foco`

Registra um novo bloco de trabalho.

**Request Body:**

```json
{
  "nivel_foco": 4,
  "tempo_minutos": 90,
  "comentario": "Implementei a autenticação JWT com testes.",
  "categoria": "coding",
  "tags": ["backend", "jwt", "sprint-3"]
}
```

**Campos:**

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `nivel_foco` | inteiro (1–5) | ✅ | 1=muito distraído, 5=estado de flow |
| `tempo_minutos` | inteiro (1–1440) | ✅ | Duração em minutos |
| `comentario` | string (min 5 chars) | ✅ | O que foi feito ou o que causou distração |
| `categoria` | string (choices) | ❌ | `coding`, `reuniao`, `estudo`, `escrita`, `revisao`, `outro` |
| `tags` | lista de strings | ❌ | Ex: `["sprint", "bug-fix"]` |

**Categorias válidas:**
- `coding` — Programação
- `reuniao` — Reunião
- `estudo` — Estudo
- `escrita` — Escrita/Documentação
- `revisao` — Revisão de Código
- `outro` — Outro (padrão)

**Response 201 Created:**

```json
{
  "sucesso": true,
  "mensagem": "Registro de foco criado com sucesso!",
  "dados": {
    "id": 1,
    "nivel_foco": 4,
    "tempo_minutos": 90,
    "comentario": "Implementei a autenticação JWT com testes.",
    "categoria": "coding",
    "tags": ["backend", "jwt", "sprint-3"],
    "data_criacao": "2025-05-12T10:30:00-03:00",
    "data_atualizacao": "2025-05-12T10:30:00-03:00",
    "nivel_descricao": "Bem focado",
    "tempo_formatado": "1h 30min"
  }
}
```

**Response 400 Bad Request (dados inválidos):**

```json
{
  "sucesso": false,
  "erro": {
    "mensagem": "Dados inválidos. Verifique os campos.",
    "detalhes": {
      "nivel_foco": ["O nível de foco deve ser entre 1 e 5. Você enviou: 10"]
    }
  }
}
```

---

### `GET /registro-foco`

Lista todos os registros. Suporta filtros por query params.

**Query Params opcionais:**

| Param | Exemplo | Descrição |
|---|---|---|
| `categoria` | `?categoria=coding` | Filtra por categoria |
| `nivel_foco` | `?nivel_foco=5` | Filtra por nível |
| `limit` | `?limit=10` | Limita resultados (padrão: 50, max: 100) |

---

### `GET /diagnostico-produtividade`

Retorna diagnóstico inteligente baseado em todos os registros.

**Response 200 OK:**

```json
{
  "sucesso": true,
  "diagnostico": {
    "total_registros": 12,
    "media_nivel_foco": 3.75,
    "tempo_total_minutos": 720,
    "tempo_total_formatado": "12h",
    "nivel_predominante": "Nível 4 — Bem focado",
    "categoria_mais_frequente": "Programação",
    "message_feedback": "Bom nível de foco! Você está produtivo e no caminho certo...",
    "pontuacao_produtividade": 69.0,
    "distribuicao_niveis": {
      "1": 0, "2": 2, "3": 3, "4": 5, "5": 2
    },
    "distribuicao_categorias": {
      "coding": 8,
      "estudo": 3,
      "reuniao": 1
    },
    "periodo": {
      "primeiro_registro": "10/05/2025 09:00",
      "ultimo_registro": "12/05/2025 18:30"
    },
    "dicas": [
      "Tente aumentar seus blocos de foco para 45-50 minutos.",
      "Pratique meditação ou respiração profunda antes das sessões.",
      "Organize suas tarefas do dia anterior — chegue com um plano."
    ]
  }
}
```

**Lógica do `message_feedback`:**

| Média de foco | Mensagem |
|---|---|
| < 1.5 | Dificuldade de concentração — sugestões de eliminação de distração |
| 1.5 – 2.5 | Abaixo do ideal — sugere técnica Pomodoro |
| 2.5 – 3.5 | Foco moderado — sugere blocos de tempo maiores |
| 3.5 – 4.5 | Bom nível — incentivo a manter rotina |
| > 4.5 | Maratona produtiva de alto nível! 🚀 |

---

## Exemplos de Uso

### Usando cURL

```bash
# Criar um registro
curl -X POST http://localhost:8000/api/v1/registro-foco \
  -H "Content-Type: application/json" \
  -d '{
    "nivel_foco": 5,
    "tempo_minutos": 120,
    "comentario": "Implementei toda a API do desafio técnico em estado de flow!",
    "categoria": "coding",
    "tags": ["django", "drf", "desafio"]
  }'

# Ver diagnóstico
curl http://localhost:8000/api/v1/diagnostico-produtividade

# Listar apenas sessões de coding
curl "http://localhost:8000/api/v1/registro-foco?categoria=coding&limit=5"
```

### Usando Python (requests)

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Criar registro
response = requests.post(f"{BASE_URL}/registro-foco", json={
    "nivel_foco": 4,
    "tempo_minutos": 90,
    "comentario": "Revisão de código com o time.",
    "categoria": "revisao",
    "tags": ["code-review", "sprint-4"],
})
print(response.json())

# Ver diagnóstico
diagnostico = requests.get(f"{BASE_URL}/diagnostico-produtividade")
print(diagnostico.json())
```

---

## Testes

### Rodar todos os testes

```bash
python manage.py test registros.tests.test_models \
                       registros.tests.test_serializers \
                       registros.tests.test_views \
                       --verbosity=2
```

### Com cobertura de código

```bash
pip install coverage
coverage run manage.py test registros.tests.test_models registros.tests.test_serializers registros.tests.test_views
coverage report
```

**Cobertura atual: 34 testes (models + serializers + views)**

---

## Docker

### Rodar com Docker Compose

```bash
# Build e start
docker compose up --build

# Em background
docker compose up -d

# Parar
docker compose down
```

### Rodar apenas o container

```bash
docker build -t focus-log-api .
docker run -p 8000:8000 \
  -e SECRET_KEY=sua-chave \
  -e DEBUG=True \
  focus-log-api
```

---

## Estrutura de Pastas

```
focus_log_api/
│
├── core/                    # Configurações do projeto Django
│   ├── settings.py          # Todas as configurações
│   ├── urls.py              # URLs principais (roteador central)
│   └── wsgi.py              # Interface WSGI para deploy
│
├── registros/               # App principal
│   ├── models.py            # Modelo de dados RegistroFoco
│   ├── serializers.py       # Validação e serialização
│   ├── views.py             # Endpoints HTTP
│   ├── services.py          # Lógica de diagnóstico
│   ├── exceptions.py        # Handler de erros customizado
│   ├── admin.py             # Configuração do painel admin
│   ├── urls.py              # URLs do app
│   ├── migrations/          # Histórico de alterações no banco
│   └── tests/
│       ├── test_models.py   # Testes unitários do model
│       ├── test_serializers.py  # Testes de validação
│       └── test_views.py    # Testes de integração (HTTP)
│
├── .github/
│   └── workflows/
│       └── ci.yml           # Pipeline CI/CD automático
│
├── .env.example             # Template de variáveis de ambiente
├── .gitignore               # Arquivos ignorados pelo Git
├── Dockerfile               # Imagem Docker da aplicação
├── docker-compose.yml       # Orquestração de containers
├── manage.py                # CLI do Django
├── requirements.txt         # Dependências Python
└── README.md                # Esta documentação
```

---

## Decisões Técnicas

### Por que Django em vez de FastAPI/Flask?

Django oferece um ecossistema completo: ORM, Admin, migrations, validações — tudo integrado. Para uma API de negócio com persistência de dados, Django + DRF reduz o boilerplate e acelera o desenvolvimento sem sacrificar organização.

### Por que separar Services das Views?

Views devem ser finas — apenas recebem e respondem. Toda lógica de negócio em `services.py`:
- **Testabilidade**: testamos a lógica sem HTTP
- **Reutilização**: a mesma lógica pode ser usada por workers, tasks, outros endpoints
- **Manutenção**: mudanças na regra de negócio ficam em um lugar só

### Por que python-decouple?

Seguimos o princípio **12-Factor App**: configuração via variáveis de ambiente. Nunca hardcodamos segredos no código. `python-decouple` lê automaticamente do `.env` em desenvolvimento e das variáveis reais em produção.

### Por que SQLite?

Para o escopo do desafio, SQLite é ideal — zero configuração, portátil, suficiente para milhares de registros. A troca para PostgreSQL em produção requer apenas alterar `settings.py` (o ORM abstrai isso).

---

## Uso de IA no Desenvolvimento

Este projeto foi desenvolvido com auxílio do Claude (Anthropic). Os artefatos gerados pela IA estão presentes nos commits do repositório, conforme requisito do desafio. A IA foi utilizada para:

- Scaffolding da estrutura de arquivos
- Geração de testes automatizados
- Revisão da lógica de negócio do diagnóstico
- Melhoria dos comentários e documentação

Todas as decisões de arquitetura, revisão de código e validação funcional foram feitas pelo desenvolvedor.
