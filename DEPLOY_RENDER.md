# 🚀 Deploy do FinBot no Render

Guia completo do zero ao bot rodando em produção. Tempo estimado: **15 minutos**.

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

> 💡 O tier gratuito do Groq dá mais que o suficiente para uso pessoal: milhares de requisições por dia com Llama 3.3 70B.

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

> ⚠️ **Confirme que o `.env` NÃO foi enviado.** O `.gitignore` do projeto já protege isso, mas verifique no GitHub se o arquivo não está lá. Se aparecer, remova o repositório e refaça com o `.gitignore` correto.

---

## Passo 4 — Conectar o Render ao GitHub

1. Acesse [dashboard.render.com](https://dashboard.render.com).
2. No canto superior direito, clique em **New +** → **Blueprint**.
3. Clique em **Connect GitHub** (se for a primeira vez).
4. Autorize o Render a acessar seu repositório `finbot`.
5. Selecione o repositório `finbot` na lista e clique em **Connect**.

O Render lê automaticamente o arquivo `render.yaml` do projeto e mostra os recursos que vai criar:

- ✅ Um **Background Worker** chamado `finbot-telegram`
- ✅ Um **Persistent Disk** de 1GB montado em `/var/data` (para o SQLite sobreviver entre deploys)

Clique em **Apply** para confirmar.

---

## Passo 5 — Configurar as variáveis de ambiente

O Render vai criar o serviço, mas **vai falhar na primeira inicialização** porque faltam as chaves. Isso é esperado.

1. No dashboard, clique no serviço **finbot-telegram**.
2. No menu lateral, clique em **Environment**.
3. Você verá `TELEGRAM_TOKEN` e `GROQ_API_KEY` listadas como vazias. Clique em **Edit** em cada uma e cole os valores:
   - `TELEGRAM_TOKEN` → o token do BotFather (passo 1)
   - `GROQ_API_KEY` → a chave do Groq (passo 2)
4. Clique em **Save Changes**.

A variável `DATABASE_URL` já vem configurada automaticamente para `sqlite:////var/data/finbot.db` (no disk persistente).

---

## Passo 6 — Aguardar o deploy

Depois de salvar as variáveis, o Render reinicia o serviço automaticamente.

1. Vá em **Logs** no menu lateral do serviço.
2. Acompanhe o build. Você deve ver algo como:
   ```
   ==> Cloning from https://github.com/...
   ==> Installing dependencies...
   ==> Running 'python main.py'
   INFO - Bot iniciado. Aguardando mensagens...
   ```
3. Se aparecer **"Bot iniciado. Aguardando mensagens..."**, está no ar! 🎉

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

---

## Limitações do plano gratuito do Render

| Recurso | Plano Free |
|---|---|
| Horas de Worker/mês | 750h (suficiente pra rodar 24/7 um único serviço) |
| Hibernação | Workers podem hibernar após inatividade prolongada |
| Disk persistente | Incluído no `render.yaml` (1GB) |
| Build minutes | 500/mês |

> ⚠️ **Sobre hibernação:** Background Workers no plano free podem ficar inativos se não houver atividade. Quando você manda a primeira mensagem após um tempo, o bot pode demorar **20-40 segundos** pra responder enquanto "acorda". Depois disso fica responsivo normalmente.

**Se a hibernação incomodar**, alternativas gratuitas:
- **Fly.io** — tier free generoso, sem hibernação agressiva
- **Oracle Cloud Free Tier** — VM grátis pra sempre (4 vCPU ARM, 24GB RAM)
- **Seu próprio PC/Raspberry Pi** — `nohup python main.py &` e pronto

---

## Atualizando o bot

Sempre que você fizer um `git push` para a branch `main`, o Render detecta e faz redeploy automático. Os dados no SQLite ficam preservados porque estão no disk persistente.

```bash
# Após editar o código
git add .
git commit -m "Adicionando nova feature"
git push
```

Acompanhe o redeploy em **Logs** no dashboard.

---

## Troubleshooting

### "Bot não responde no Telegram"
- Verifique os **Logs** no Render. Procure por erros.
- Confirme que `TELEGRAM_TOKEN` está correto (sem espaços).
- Teste o token: acesse `https://api.telegram.org/botSEU_TOKEN/getMe` no navegador. Deve retornar dados do bot.

### "Erro 401 do Groq nos logs"
- A `GROQ_API_KEY` está errada ou expirada. Gere uma nova em console.groq.com.

### "Bot duplica respostas"
- Você tem **duas instâncias rodando** (provavelmente uma local + Render). O Telegram só permite uma conexão de polling por bot. Pare a instância local.

### "Disk full"
- 1GB do plano free é mais que suficiente pra anos de uso. Se ainda assim encher, edite `render.yaml` aumentando `sizeGB` (vira plano pago).

### Logs mostram "ImportError" ou erro de dependência
- O `requirements.txt` está incompleto. Confirme que ele tem as 4 linhas do projeto e refaça o push.

---

## Pronto!

Seu bot agora roda 24/7 na nuvem, gratuitamente. Os dados ficam salvos no disk persistente do Render — mesmo redeploys não apagam o histórico.

Se quiser evoluir o projeto, dá uma olhada na seção "Próximos passos sugeridos" do `README.md`.
