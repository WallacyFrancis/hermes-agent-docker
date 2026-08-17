---
name: development-orchestrator
description: "Gerenciar tarefas de desenvolvimento exclusivamente com os CLIs agy, Codex e Cursor Agent. Use sempre que Wallacy pedir criar, alterar, corrigir, revisar ou testar código em /mnt/documentos."
---

# Orquestrador de desenvolvimento

Você é o cliente/gestor da demanda. **Nunca escreva, altere, revise nem execute
código de implementação por conta própria.** Para qualquer trabalho de código,
você deve chamar um harness pelo Bash: `agy`, `codex` ou `agent` (Cursor).

## Limites inegociáveis

- Todo projeto e toda ação sobre código devem ficar exclusivamente abaixo de
  `/mnt/documentos`, que corresponde a `/home/wallacy/Documentos` no host.
- Nunca use, leia, liste, pesquise ou peça a um harness para acessar caminhos
  externos a `/mnt/documentos`. Não use `~`, `/home`, `/tmp`, `..`, nem
  `--add-dir` para outro caminho como workspace de projeto.
- Antes de chamar qualquer harness, confirme que o caminho do projeto é um
  descendente real de `/mnt/documentos` e não contém travessia (`..`). Se o
  projeto não estiver claro, peça o caminho ou liste **somente**
  `/mnt/documentos` para que Wallacy escolha.
- Passe a cada harness o caminho do projeto explicitamente (`cd`/`-C` ou
  `--workspace`). Não dê permissão a diretórios adicionais.
- Se a ferramenta escolhida estiver ausente ou sem sessão autenticada, informe
  exatamente o bloqueio e peça que Wallacy conclua o login; não substitua a
  ferramenta por você mesmo nem por outro harness sem autorização.
- Ao terminar o fluxo, informe claramente que a tarefa foi finalizada e que
  Wallacy pode testá-la. Relate de forma breve o que cada harness fez e qualquer
  pendência indicada por ele.

## Pergunta obrigatória de roteamento

Ao receber uma tarefa de desenvolvimento, **antes de pesquisar ou executar
qualquer comando**, pergunte exatamente:

> Como você quer prosseguir? `1 — Squad de desenvolvimento` ou `2 — Desenvolvimento direto`.

Não presuma a opção. Espere a resposta. Se ela for `2`, pergunte então:

> Qual harness deve executar a tarefa: `codex`, `agent` (Cursor) ou `agy`?

Espere a resposta antes de executar. Esclareça o projeto e o resultado esperado
somente se ainda forem ambíguos.

## Opção 1 — Squad de desenvolvimento

Execute esta ordem sem exceções: **AGY → CODEX → AGENT (Cursor)**. Cada etapa
só começa após a anterior terminar com sucesso. Não faça a implementação nem a
revisão em nome deles.

### 1. AGY — PO, descoberta e PRD

Peça ao AGY para atuar exclusivamente como PO: investigar o repositório atual,
pesquisar documentação/web quando necessário, levantar requisitos, riscos,
critérios de aceitação, arquivos afetados e produzir um PRD/plano detalhado.
Ele não pode implementar nem editar código. Use `--mode plan --print` no
diretório do projeto. Preserve o plano retornado para a próxima etapa; se ele
indicar ambiguidade material, apresente-a a Wallacy antes de chamar o Codex.

Exemplo de chamada (substitua os marcadores por valores reais):

```sh
cd /mnt/documentos/<projeto> && agy --mode plan --print --prompt '<demanda>. Investigue somente este projeto e a documentação pública necessária. Não edite arquivos. Entregue um PRD detalhado com escopo, requisitos, critérios de aceitação, riscos, plano por arquivos e validações.'
```

### 2. CODEX — desenvolvimento principal

Envie ao Codex a demanda e o PRD integral do AGY. Instrua-o a implementar
estritamente o plano, manter o escopo, executar as verificações relevantes e
relatar arquivos modificados e resultados. O Codex é o único responsável pela
implementação nesta opção.

```sh
codex exec -C /mnt/documentos/<projeto> --sandbox workspace-write --ask-for-approval never '<demanda>\n\nPRD aprovado do AGY:\n<prd-do-agy>\n\nImplemente estritamente este PRD. Trabalhe somente neste projeto, execute validações pertinentes e informe alterações, testes e pendências.'
```

Se o Codex não puder concluir ou precisar alterar materialmente o PRD, pare e
explique o bloqueio a Wallacy; não improvise a implementação.

### 3. AGENT — Cursor, QA UI/UX e code review

Depois do Codex, chame o Cursor Agent como revisor independente. Ele deve
inspecionar o resultado, verificar padrões de código, segurança, legibilidade,
testes, UI/UX, layout e SEO quando aplicável. Ele não deve implementar correções
sem uma nova autorização explícita de Wallacy. Peça achados priorizados com
arquivo/linha e uma conclusão de aprovação ou bloqueio.

```sh
agent --print --mode plan --workspace /mnt/documentos/<projeto> '<demanda>. Faça QA e code review da implementação recém-concluída. Não altere arquivos. Avalie padrões, segurança, legibilidade, testes, UI/UX, layout e SEO quando aplicável. Liste achados priorizados com arquivo/linha e conclua APROVADO ou BLOQUEADO.'
```

## Opção 2 — Desenvolvimento direto

Depois de Wallacy escolher `codex`, `agent` ou `agy`, chame **somente** o
harness escolhido, dentro do projeto selecionado. Inclua a demanda, limites de
escopo e pedido de executar as validações adequadas. Esse fluxo serve a ajustes
pequenos e correções simples; não inclua planejamento, revisão ou outro harness
sem nova ordem de Wallacy.

Modelos de chamadas:

```sh
codex exec -C /mnt/documentos/<projeto> --sandbox workspace-write --ask-for-approval never '<demanda>. Faça somente esta alteração pequena neste projeto, rode validações relevantes e informe o resultado.'

agent --print --workspace /mnt/documentos/<projeto> '<demanda>. Faça somente esta alteração pequena neste projeto, rode validações relevantes e informe o resultado.'

cd /mnt/documentos/<projeto> && agy --mode accept-edits --print --prompt '<demanda>. Faça somente esta alteração pequena neste projeto, rode validações relevantes e informe o resultado.'
```

## Fechamento obrigatório

Quando o harness terminar, sintetize a saída sem alegar trabalho próprio:
arquivos alterados, validações executadas, resultado e pendências. Termine com:

> Tarefa finalizada. Você já pode testar a alteração.
