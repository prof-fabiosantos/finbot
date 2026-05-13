# 🚀 Deploy do FinBot no Render (Plano Free)

Guia completo do zero ao bot rodando em produção, **100% gratuito**. Tempo estimado: **15-20 minutos**.

> ℹ️ Este guia já considera as restrições atuais do plano free do Render: **Background Workers e Persistent Disks são pagos**. Por isso usamos **Web Service** (gratuito) com um servidor HTTP mínimo que satisfaz a exigência do Render.

---

## Pré-requisitos

Antes de começar, tenha em mãos:

- ✅ Conta no [GitHub](https://github.com) (gratuita)
- ✅ Conta no [Render](https://render.com) (gratuita, faça login com o GitHub)
- ✅ **Token do Telegram** — obtido com [@BotFather](https://t.me/BotFather)
- ✅ **API key do Groq** — gerada em [console.groq.com](https://console.groq.com)
- ✅ `git` instalado na sua máquina

---

## Passo 1 — Obter o Token do Telegram

1. Abra o Telegram e procure por **@BotFather**.
2. Inicie a conversa e envie `/newbot`.
3. Escolha um **nome** para o bot (ex: "Meu FinBot").
4. Escolha um **username** terminando em `bot` (ex: `meu_finbot_bot`).
5. O BotFather responde com uma mensagem contendo o **token**, algo como:
   ```
   123456789:ABCdefGHIjklMNOpqrsTUVwxyz
   ```
6. **Copie e guarde esse token.** Você vai precisar dele no passo 5.

> 🔒 Trate o token como uma senha. Quem tiver o token controla o bot.

---

## Passo 2 — Obter a API Key do Groq

1. Acesse [console.groq.com](https://console.groq.com) e faça login (Google ou e-mail).
2. No menu lateral, clique em **API Keys**.
3. Clique em **Create API Key**, dê um nome (ex: "finbot") e confirme.
4. Copie a chave (começa com `gsk_...`). **Ela só aparece uma vez.**

> 💡 O tier gratuito do Groq é generoso: milhares de requisições por dia com Llama 3.3 70B. Mais que suficiente para uso pessoal.

---

## Passo 3 — Subir o código para o GitHub

1. No GitHub, clique em **New repository**.
2. Nome sugerido: `finbot`. Pode deixar **privado**.
3. **Não** marque "Add README" — o projeto já tem um.
4. Crie o repositório.

Agora no seu terminal, dentro da pasta `finbot` que você descompactou:

```bash
cd finbot

git init
git add .
git commit -m "MVP inicial do FinBot"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/finbot.git
git push -u origin main
```

> ⚠️ **Confirme que o `.env` NÃO foi enviado.** O `.gitignore` do projeto já protege isso. Pra ter certeza, rode `git status` antes do commit — `.env` não deve aparecer na lista.

---

## Passo 4 — Conectar o Render ao GitHub

1. Acesse [dashboard.render.com](https://dashboard.render.com).
2. No canto superior direito, clique em **New +** → **Blueprint**.
3. Clique em **Connect GitHub** (se for a primeira vez).
4. Autorize o Render a acessar seu repositório `finbot`.
5. Selecione o repositório `finbot` na lista e clique em **Connect**.

O Render lê o arquivo `render.yaml` do projeto e mostra o recurso que vai criar:

- ✅ Um **Web Service** chamado `finbot-telegram` (plano free)

Clique em **Apply** para confirmar.

> 💡 **Por que Web Service e não Background Worker?** No plano free do Render, Background Workers viraram recurso pago. Web Services continuam gratuitos, mas exigem que o app responda em uma porta HTTP. O FinBot resolve isso subindo um endpoint `/health` minúsculo em paralelo com o bot — você nem precisa pensar nisso, já está configurado.

---

## Passo 5 — Configurar as variáveis de ambiente

O Render vai criar o serviço, mas **vai falhar na primeira inicialização** porque faltam as chaves. Isso é esperado.

1. No dashboard, clique no serviço **finbot-telegram**.
2. No menu lateral, clique em **Environment**.
3. Você verá `TELEGRAM_TOKEN` e `GROQ_API_KEY` listadas como vazias. Clique em **Edit** em cada uma e cole os valores:
   - `TELEGRAM_TOKEN` → o token do BotFather (passo 1)
   - `GROQ_API_KEY` → a chave do Groq (passo 2)
4. Clique em **Save Changes**.

As variáveis `DATABASE_URL` e `PORT` já vêm configuradas automaticamente pelo `render.yaml`.

---

## Passo 6 — Aguardar o deploy

Depois de salvar as variáveis, o Render reinicia o serviço automaticamente.

1. Vá em **Logs** no menu lateral do serviço.
2. Acompanhe o build. Você deve ver algo como:
   ```
   ==> Cloning from https://github.com/...
   ==> Installing dependencies...
   ==> Running 'python main.py'
   INFO - Servidor HTTP escutando na porta 10000
   INFO - Bot iniciado. Aguardando mensagens...
   ==> Your service is live 🎉
   ```
3. Quando aparecer **"Your service is live"** e **"Bot iniciado"**, está tudo no ar.

O Render também mostra uma URL pública do serviço (algo como `https://finbot-telegram-xxxx.onrender.com`). Acessa ela no navegador — deve aparecer a mensagem `FinBot is running`. Essa URL é o health check e vai ser usada no passo 8.

---

## Passo 7 — Testar o bot

1. No Telegram, procure pelo username do seu bot (ex: `@meu_finbot_bot`).
2. Clique em **Start** ou envie `/start`.
3. Mande mensagens de teste:
   ```
   uber 27
   almoço 35,90
   netflix 39.90
   ```
4. Use os comandos:
   - `/total` — total do mês
   - `/categorias` — gastos agrupados
   - `/recentes` — últimos 10 gastos
   - `/desfazer` — remove o último registro

Se o bot responder, **deploy concluído** 🎉

---

## Passo 8 — Manter o bot acordado (IMPORTANTE)

O Web Service gratuito do Render tem um comportamento chato: **hiberna após 15 minutos sem requisições HTTP**. Quando dorme, o bot para de responder no Telegram até alguém acessar a URL e "acordá-lo".

A solução é fazer um **ping automático** na URL do bot a cada poucos minutos. O serviço gratuito mais usado pra isso é o **UptimeRobot**.

### Configurando o UptimeRobot

1. Crie uma conta gratuita em [uptimerobot.com](https://uptimerobot.com).
2. No dashboard, clique em **+ New monitor**.
3. Preencha:
   - **Monitor Type:** `HTTP(s)`
   - **Friendly Name:** `FinBot Render`
   - **URL:** a URL pública do seu serviço no Render (ex: `https://finbot-telegram-xxxx.onrender.com/health`)
   - **Monitoring Interval:** `5 minutes` (mínimo do plano free)
4. Clique em **Create Monitor**.

Pronto. O UptimeRobot vai pingar seu bot a cada 5 minutos, mantendo-o acordado 24/7. Como bônus, ele te avisa por e-mail se o serviço cair.

> 💡 **Alternativas ao UptimeRobot:** [cron-job.org](https://cron-job.org), [Better Stack](https://betterstack.com), ou o próprio [GitHub Actions](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#schedule) com um workflow agendado.

---

## ⚠️ Limitação importante: dados são perdidos a cada deploy

Como o plano free **não permite disk persistente**, o arquivo `finbot.db` é recriado a cada deploy ou reinício do serviço. Ou seja:

- ❌ Se você fizer `git push` com uma atualização → dados perdidos
- ❌ Se o Render reiniciar o serviço por manutenção → dados perdidos
- ✅ Durante operação normal (sem reinício) → dados persistem

**Pra um MVP de testes, isso é ok.** Quando quiser usar de verdade, migre pra um banco gratuito externo:

- **[Supabase](https://supabase.com)** — Postgres com 500MB grátis
- **[Neon](https://neon.tech)** — Postgres com 0.5GB grátis
- **[Turso](https://turso.tech)** — SQLite distribuído com 9GB grátis

A migração é simples: cria o banco, copia a connection string, troca `DATABASE_URL` no Render. **Nenhuma linha de código muda** — o SQLAlchemy detecta o tipo de banco automaticamente.

---

## Atualizando o bot

Sempre que fizer `git push` para a branch `main`, o Render detecta e faz redeploy automático.

```bash
git add .
git commit -m "Adicionando nova feature"
git push
```

Acompanhe o redeploy em **Logs** no dashboard.

> ⚠️ Lembrando: cada deploy zera o banco SQLite. Se já estiver com dados importantes, migre pro Postgres antes (Supabase/Neon).

---

## Troubleshooting

### "Bot não responde no Telegram"
- Verifique os **Logs** no Render. Procure por erros.
- Confirme que `TELEGRAM_TOKEN` está correto (sem espaços extras).
- Teste o token: acesse `https://api.telegram.org/botSEU_TOKEN/getMe` no navegador. Deve retornar dados do bot.
- Se o serviço estiver hibernando, configure o UptimeRobot (passo 8).

### "Erro 401 do Groq nos logs"
- A `GROQ_API_KEY` está errada ou expirada. Gere uma nova em console.groq.com e atualize a env var no Render.

### "Bot duplica respostas / responde 2x cada mensagem"
- Você tem **duas instâncias rodando** (provavelmente uma local + Render). O Telegram só permite uma conexão de polling por bot. Pare a instância local com `Ctrl+C` ou desligue uma das duas.

### "Address already in use" nos logs
- A variável `PORT` está com valor inválido ou tem duas instâncias do bot no mesmo serviço. Verifique no painel **Environment** se `PORT` está definida como `10000`.

### "service type is not available for this plan"
- O `render.yaml` está com `type: worker`. Confirme que está como `type: web` (já corrigido neste projeto).

### "disks are not supported for free tier services"
- O `render.yaml` ainda tem um bloco `disk:`. Remova-o (já removido neste projeto).

### Bot fica lento na primeira mensagem após um tempo
- Está hibernando. Configure o UptimeRobot (passo 8) e o problema some.

---

## Pronto!

Seu bot agora roda 24/7 na nuvem, gratuitamente. Resumo da arquitetura:

```
Telegram → long polling → FinBot (Render Web Service)
                              ├─ Servidor HTTP /health (Render exige)
                              ├─ Groq API (Llama 3.3 70B)
                              └─ SQLite local (efêmero)

UptimeRobot → ping /health a cada 5min → mantém serviço acordado
```

Se quiser evoluir o projeto, dá uma olhada na seção "Próximos passos sugeridos" do `README.md`.
