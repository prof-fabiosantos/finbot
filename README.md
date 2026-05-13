# 🤖 FinBot — Assistente Financeiro no Telegram

MVP de um bot do Telegram que registra gastos via linguagem natural usando Llama 3.3 70B (Groq) e SQLite.

## Como funciona

```
Usuário envia: "uber 27"
        ↓
   Bot Telegram
        ↓
   Groq (Llama 3.3 70B) → extrai {item, categoria, valor}
        ↓
   SQLite (SQLAlchemy)
        ↓
Bot responde: "✅ Gasto Registrado! Uber (Transporte) R$27,00"
```

## Pré-requisitos (gratuitos)

1. **Token do Telegram**: fale com [@BotFather](https://t.me/BotFather), use `/newbot`, copie o token.
2. **API key do Groq**: crie conta em [console.groq.com](https://console.groq.com) e gere uma chave.
3. **Conta no Render** (opcional, só pra deploy): [render.com](https://render.com).

## Rodar localmente

```bash
# 1. Clone e entre na pasta
cd finbot

# 2. Crie um ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Copie o .env e preencha
cp .env.example .env
# edite .env e cole o TELEGRAM_TOKEN e GROQ_API_KEY

# 5. Rode
python main.py
```

Mande mensagens no seu bot pelo Telegram e teste.

## Deploy no Render (gratuito)

O plano free do Render dá 750h/mês de worker — mais que suficiente.

### Passo a passo

1. Crie um repositório no GitHub e suba o código.
2. No Render, clique em **New → Blueprint** e aponte pro seu repo.
3. O Render lê o `render.yaml` automaticamente e cria:
   - um **Background Worker** rodando `python main.py`
   - um **Persistent Disk** de 1GB montado em `/var/data` (pro SQLite sobreviver a deploys)
4. No painel do serviço, vá em **Environment** e adicione:
   - `TELEGRAM_TOKEN`
   - `GROQ_API_KEY`
5. O deploy roda sozinho. Em ~2 minutos o bot está no ar.

### Por que Background Worker e não Web Service?

O bot usa **long polling** (não webhook), então não precisa expor porta HTTP. Background Worker é a escolha certa — não recebe tráfego externo, só roda o processo continuamente.

> ⚠️ **Importante:** o plano free do Render hiberna serviços ociosos depois de 15min. Pra Background Worker isso significa que o bot pode demorar pra responder na primeira mensagem após inatividade. Se isso incomodar, alternativas: Fly.io (free tier), Oracle Cloud Free Tier (VM grátis pra sempre), ou rodar num PC seu com `nohup`.

## Comandos do bot

| Comando | O que faz |
|---|---|
| `/start` ou `/ajuda` | Mensagem de boas-vindas |
| `/total` | Total gasto no mês corrente |
| `/categorias` | Soma por categoria no mês |
| `/recentes` | Últimos 10 gastos |
| `/desfazer` | Remove o último registro |

Qualquer outra mensagem é tratada como possível gasto e passa pelo LLM.

## Estrutura do projeto

```
finbot/
├── app/
│   ├── __init__.py
│   ├── bot.py          # handlers do Telegram
│   ├── database.py     # SQLAlchemy + modelo Expense
│   ├── llm.py          # chamada ao Groq
│   └── services.py     # lógica de negócio (salvar, consultar)
├── main.py             # entry point
├── requirements.txt
├── render.yaml         # config de deploy
├── .env.example
└── .gitignore
```

## Próximos passos sugeridos

- **Gráfico mensal**: gerar PNG com matplotlib e enviar como imagem
- **Consultas em linguagem natural**: "quanto gastei com comida?" → SQL via LLM
- **Lembretes**: APScheduler pra avisar de contas recorrentes
- **Export**: gerar CSV/PDF do mês sob demanda
- **Multi-moeda**: detectar USD, EUR etc.
- **Backup**: cron diário copiando o SQLite pro S3/R2
