# N.E.X.U.S. — execução contínua

Este plano organiza o backlog restante por dependência. Os status são deliberadamente conservadores; código/testes prevalecem sobre documentação.

## Próxima tarefa

Retomar em **P2-02 — revisão independente e proveniência**. P2-01 tem limite de execução e CI aprovados; persistência/resume e fallback same-lane continuam pendentes.

## Plano ordenado

| ID | Prioridade | Tarefa / critério de aceite | Dependências | Estado |
|---|---|---|---|---|
| P0-01 | P0 | Segurança base: autenticação, fail-closed PolicyEngine, segredos fora de respostas/logs; regressões automatizadas | — | IMPLEMENTADO; suíte local cobre, requer revisão contínua |
| P0-02 | P0 | Worker durável: concorrência entre processos, lease/fencing, idempotência, retry e retomada testados | P0-01 | IMPLEMENTADO E TESTADO; operação remota não configurada |
| P1-01 | P1 | Conversa real, memória contextual limitada, histórico e fluxo de pesquisa com confirmação | P0-01 | IMPLEMENTADO localmente; providers externos dependem de configuração/autorização |
| P1-02 | P1 | Model routing manual/automático com disponibilidade, privacidade e orçamento | P1-01 | IMPLEMENTADO; catálogo manual e budget remoto fechado por padrão |
| P1-03 | P1 | Tool calling nativo bounded em Ollama/OpenAI-compatible/Gemini/Anthropic; schemas READ-only, continuidade preservada e sensíveis bloqueadas | P1-01 | IMPLEMENTADO COM MOCKS; sem teste de rede; capacidade por modelo exige allowlist manual |
| P1-04 | P1 | Configurar provider/modelo por especialista; verificar adapter/capacidade, permitir fallback no mesmo trust lane, aplicar orçamento e manter provider padrão quando não configurado | P1-02 | PARCIAL VALIDADO: mapa explícito por papel, ProviderManager e preflight agregado; CI Python 3.11/3.12 + browser E2E passou em d11adc7; falta descoberta de capacidade/disponibilidade e fallback same-lane |
| P1-05 | P1 | Skills versionadas, proposta/aprovação, integridade, descoberta/carregamento sob demanda e injeção limitada no chat real | P0-01 | PARCIAL: registry/API/aprovação/hash/injeção/chat e busca query implementados; novos limites estritos e busca literal adicionados; CI pendente; UI de administração e testes de conflito semântico ainda pendentes |
| P1-06 | P1 | Evidências: deliverable tipado separa afirmações/evidências, referências válidas, confiança limitada; Reviewer recusa claims sem fonte quando requerida | P1-01 | PARCIAL VALIDADO: claims tipadas, IDs S1–S3, referências desconhecidas/duplicadas rejeitadas, claims sem fonte omitidas deterministicamente quando há catálogo, instrução ao Reviewer/síntese; CI completo passou em commit 1834736 (193 testes por versão + 5/5 browser E2E); falta persistir proveniência, validar suporte semântico e revisão independente/humana |
| P2-01 | P2 | Delegação rastreável e isolada entre especialistas, limites de chamadas/tempo/budget, falha e retomada sem ciclos | P1-04 | PARCIAL VALIDADO: etapas fixas e sequenciais, seleção de modelo por papel, eventos metadata-only, timeout global de 90s (máx. 180s), falha interrompe etapas restantes; CI passou no commit 029389e (195 testes Python 3.11/3.12 + 5/5 browser E2E); ainda sem persistência/resume ou fallback same-lane |
| P2-02 | P2 | Revisão independente com contexto reduzido e proveniência, sem autoaprovação | P1-06 | PENDENTE |
| P2-03 | P2 | Execução de código/arquivos em sandbox real por tarefa, privilégio mínimo, mounts allowlisted, sem segredos e com limites | P0-01 | BLOQUEADA: ambiente atual não oferece sandbox isolada validada; sem executor/execução simulada |
| P2-04 | P2 | Eventos de ferramenta/agente na UI com APIs reais e estados de falha | P1-03, P2-01 | PENDENTE |
| P3-01 | P3 | Migrações versionadas, backup/restore e recuperação documentada/testada | P0-02 | PARCIAL; SQLite local tem criação/migrações aditivas, falta estratégia formal de backup |
| P3-02 | P3 | E2E navegador em fluxos principais, CI remoto verificado | P1-01 | E2E local existente; CI remoto depende de push/PR autorizado |
| P3-03 | P3 | Produção cloud/TLS, identidade multiusuário, retenção e observabilidade operacional | P3-01 | BLOQUEADA por decisões/infraestrutura do proprietário |

## Regras de execução

1. Escolha o menor ID desbloqueado que ainda não esteja concluído.
2. Implemente em código integrado, escreva testes que falham antes da correção e execute testes afetados.
3. Para providers remotos, use mocks. Chamadas reais, custos, credenciais, deploy, ações destrutivas ou permissões sensíveis continuam sujeitos à autorização aplicável.
4. Não introduza shell irrestrito. Skills são texto/instruções não confiáveis, não ferramentas nem privilégios.
5. Após cada marco, registre status/testes/arquivos no checkpoint com o script versionado.
6. Um bloqueio em uma tarefa não encerra a sequência: avance para outra tarefa independente e segura.
7. Não declare produto completo enquanto houver tarefas PENDENTES, PARCIAIS ou BLOQUEADAS.

## Como retomar

Abra o repositório no Codex. Leia `AGENTS.md`, este plano e a seção mais recente de `CHECKPOINT.md`; inicie no próximo ID desbloqueado. Após uma alteração validada:

```powershell
python tools/update_checkpoint.py --task P1-04 --status "EM ANDAMENTO" --summary "..." --tests "..." --files "..."
```
