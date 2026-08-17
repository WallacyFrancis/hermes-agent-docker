# 🤖 Hermes Agent Docker Setup

Setup completo do **Hermes Agent** em ambiente Docker com suporte a automação de navegador (Chromium headless + noVNC + CDP proxy), orquestrador de desenvolvimento de software em squad e skills especializadas.

---

## 🌟 Arquitetura dos Serviços

A composição (`compose.yaml`) é dividida em três serviços interdependentes:

```mermaid
graph TD
    User["👤 Usuário / Telegram / CLI"] --> Hermes["🐳 hermes-agent (Hermes Agent Core)"]
    Hermes --> CDPProxy["🐳 cdp-proxy (Socat 9222)"]
    CDPProxy --> Chromium["🐳 hermes-chromium (Chromium + noVNC 27027)"]
    Hermes --> Skills["📂 Skills (/opt/data/skills)"]
    Skills --> Audiency["🔗 Suporte & Relatórios Audiency"]
    Skills --> Squad["💻 Orquestrador (AGY / Codex / Cursor)"]
```

1. **`hermes-agent`**: Núcleo do Hermes Agent baseado em `nousresearch/hermes-agent:latest`, configurado para rodar como gateway (Telegram/CLI) com suporte a Python, GitHub CLI (`gh`) e wrapper de harnesses de desenvolvimento.
2. **`hermes-chromium`**: Instância Chromium gerenciada (`linuxserver/chromium`) com display virtual e interface **noVNC** na porta `127.0.0.1:27027` (útil para login manual, 2FA e resolução de CAPTCHA).
3. **`cdp-proxy`**: Proxy TCP `socat` isolado que expõe o Chrome DevTools Protocol (`CDP`) internamente para o Hermes na rede Docker privada `172.30.0.0/24`.

---

## 📦 Skills e Personalizações Incluídas

### 🎯 Skills Customizadas (`/skills`)

- **`development-orchestrator`**:
  - Orquestra desenvolvimento de software abaixo de `/mnt/documentos`.
  - Permite escolher entre:
    - **Opção 1 (Squad de Desenvolvimento):** `AGY` (PO & PRD) ➔ `CODEX` (Implementação) ➔ `AGENT` (Cursor - QA & Code Review).
    - **Opção 2 (Desenvolvimento Direto):** Execução pontual com a ferramenta escolhida.
- **`suporte-audiency`**:
  - CLI autenticado para o painel de chamados do Suporte Audiency (`https://suporte.audiency.io`).
  - Lista, filtra, detalha, comenta, transfere squads e atualiza status de tickets.
- **`activity-report-audiency`**:
  - Gera relatório diário das alterações de chamados (criação, início, pausa, revisão, conclusão) por desenvolvedor com histórico em snapshot (`reports/audiency-activity-state.json`) e envio automático para o Rocket.Chat.

### 🧠 Configurações e Memórias (`/config`)

- **`config.yaml`**: Configuração central do modelo (OpenRouter / NVIDIA), guardrails de ferramentas, memória contextual e compressão de prompt.
- **`SOUL.md`**: Definição de personalidade e diretrizes operacionais do agente.
- **`memories/`**: Memória de longo prazo (`USER.md` e `MEMORY.md`) preservando preferências e fluxos operacionais.
- **`plugins/.install-metadata.json`**: Metadados de plugins integrados (`superpowers`, `cognee`, `drawio-skill`, `open-design`, `Anthropic-Cybersecurity-Skills`).

---

## 🚀 Como Executar

### 1. Pré-requisitos
- Docker Engine 24+ e Docker Compose v2.
- Criação do volume Docker persistente (caso ainda não exista):

```bash
docker volume create hermes-agent-data
```

### 2. Configurar Variáveis de Ambiente
Copie o template `.env.example` para `hermes.env` (ou `.env`) e preencha suas chaves e credenciais:

```bash
cp .env.example hermes.env
```

> **Atenção:** Mantenha suas credenciais seguras. O arquivo `hermes.env` e `.env` estão devidamente incluídos no `.gitignore`.

### 3. Iniciar os Containers

```bash
# Construir a imagem customizada e subir os serviços em background
docker compose up -d --build
```

### 4. Verificar Status e Logs

```bash
docker compose ps
docker compose logs -f hermes
```

---

## 💬 Formas de Uso

### 📱 Via Telegram
Se a variável `TELEGRAM_BOT_TOKEN` estiver preenchida no arquivo de ambiente, o container iniciará automaticamente o gateway e responderá aos usuários autorizados em `TELEGRAM_ALLOWED_USERS`.

### 🖥️ Via Linha de Comando (CLI Interativo)
Você pode interagir diretamente com o agente no terminal usando:

```bash
docker compose exec -it hermes hermes chat
```

### 🌐 Acessando o Navegador noVNC (Chromium)
Para visualizar ou interagir manualmente com sessões de navegador abertas pelo agente:
- Abra no navegador do host: `http://127.0.0.1:27027`

---

## ⏰ Gerenciando Cronjobs / Agendamentos

O Hermes possui um agendador integrado para executar rotinas periódicas (por exemplo, envio diário de relatórios ou checagens).

### Criar uma tarefa agendada:
```bash
docker compose exec hermes hermes cron create \
  --schedule "0 9 * * 1-5" \
  --prompt "Gere e envie o relatório de atividades de desenvolvimento do dia anterior."
```

### Listar tarefas ativas:
```bash
docker compose exec hermes hermes cron list
```

Ou diretamente no chat do Telegram/CLI usando o comando `/cron`.

---

## 🔒 Segurança e Boas Práticas

- Todas as senhas e tokens são lidos exclusivamente das variáveis de ambiente (`/mnt/host/.env`).
- Redação automática de segredos ativa no Hermes para prevenir vazamento de credenciais em logs e prompts.
- Containers rodam com restrição de privilégios (`no-new-privileges:true`).
