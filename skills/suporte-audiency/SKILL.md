---
name: suporte-audiency
description: "Operar os chamados do Suporte Audiency: autenticar, listar e filtrar cartões, criar chamados, alterar squad ou status, comentar e baixar anexos. Use quando o usuário pedir ações em suporte.audiency.io ou chamados Audiency."
---

# Suporte Audiency

Execute `python3 /opt/data/skills/suporte-audiency/scripts/suporte_audiency.py`.

O script acessa primeiro `/home`. Se não houver sessão válida, lê
`SUPORTE_AUDIENCY_EMAIL` e `SUPORTE_AUDIENCY_PASSWORD` de `/mnt/host/.env`,
autentica e continua. Nunca exiba token, senha ou conteúdo de `.env`.

Use leitura por padrão. Antes de criar chamado, adicionar/remover pessoa, enviar
comentário, mudar status ou baixar arquivos, confirme que a ação, o cartão e os
dados necessários foram solicitados. Para status, respeite o fluxo:
`a_fazer → em_desenvolvimento → revisao → concluido`; `pausado` exige motivo.

Comandos principais:

```sh
# cartões, com filtros opcionais
python3 .../suporte_audiency.py list --status em_desenvolvimento --assignee "Wallacy Developer"

# detalhes e mensagens
python3 .../suporte_audiency.py show TICKET_ID
python3 .../suporte_audiency.py comments TICKET_ID

# alterações somente após ordem explícita
python3 .../suporte_audiency.py create --title "..." --module suporte --type bug --description "..." --reproduction "..." --page-url "https://..."
python3 .../suporte_audiency.py assign TICKET_ID --developer-id ID
python3 .../suporte_audiency.py comment TICKET_ID --text "..."
python3 .../suporte_audiency.py advance TICKET_ID [--reason "..."]
python3 .../suporte_audiency.py download TICKET_ID --output /opt/data/downloads
```

Para detalhes de implementação, consulte o grafo somente quando necessário em
`/mnt/audiency-memory/suporte-next`.
