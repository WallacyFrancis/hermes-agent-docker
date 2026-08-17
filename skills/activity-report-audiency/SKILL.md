---
name: activity-report-audiency
description: "Gerar e enviar o relatório diário de desenvolvimento Audiency para Wallacy, Henrique e Júlia. Use quando pedirem resumo de atividades, alterações de chamados ou relatório do dia anterior no Rocket.Chat."
---

# Relatório de atividades Audiency

Execute o relatório pelo script. Ele usa a skill `suporte-audiency`, compara o
Kanban atual com `/opt/data/reports/audiency-activity-state.json` e registra a
data da observação. A primeira execução cria uma linha de base e usa os campos
de criação/atualização do dia anterior; as próximas usam o diff do snapshot.

```sh
python3 /opt/data/skills/activity-report-audiency/scripts/activity_report.py --preview
python3 /opt/data/skills/activity-report-audiency/scripts/activity_report.py --send
```

`--send` encaminha exatamente o texto gerado, entre blocos de código, à conversa
privada configurada. Nunca exponha credenciais, tokens ou o JSON de estado.
Se o Rocket.Chat não tiver sessão, o script usa `ROCKETCHAT_EMAIL` e
`ROCKETCHAT_PASSWORD` em `/mnt/host/.env`; se estiverem ausentes, informe o
bloqueio sem atualizar o snapshot.

O snapshot contém todos os cartões, mesmo os que não pertencem às três pessoas.
Use `--sync-state` somente para migrar ou reparar esse arquivo, sem enviar
mensagem.

Inclua somente ações observáveis de cartões criados, iniciados, pausados, em
revisão ou concluídos, com pessoa, ID e título. Não invente autoria quando o
snapshot não permite determiná-la.
