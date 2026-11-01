# Development Checkpoint

**Atualizado:** 2026-10-31  
**Projeto:** N.E.X.U.S. — Neural Engine Expert Underground System  
**Branch principal:** `main`

## Estado atual comprovado

O repositório possui um núcleo local em Python/SQLite, executável pela CLI, com:
- memórias episódicas, semânticas e procedurais;
- fontes e afirmações com estados explícitos de revisão;
- fila de tarefas e log de auditoria;
- ingestão de TXT/Markdown, SHA-256, trechos e busca lexical;
- pesquisa de metadados bibliográficos pela Crossref;
- política de ferramentas fail-closed;
- runtime textual com MockProvider offline.

**Não existe ainda:** provider remoto real, API HTTP, autenticação, interface web, ferramentas reais, memória integrada automaticamente ao contexto da conversa, worker cloud/PC, sincronização ou deploy.

## Endurecimento recente

- SQLite `:memory:` agora permanece disponível entre conexões curtas por meio de URI compartilhada e conexão âncora.
- Runtime reivindica cada tarefa por atualização condicional dentro de transação de escrita.
- Mensagens de exceção do provider não são armazenadas literalmente.
- Limites do runtime e identificadores de provider/model são validados.
- Testes novos cobrem persistência in-memory, reentrada de tarefa e não persistência de strings com aparência de segredo.
- Workflow observa o próprio caminho, usa permissões mínimas, executa compileall e unittest.

**CI:** execução [41255344883](https://github.com/VNSANTS/N.E.X.U.S/actions/runs/41255344883) concluída com sucesso em Python 3.11 e 3.12, incluindo compileall e unittest, no commit `59356b7674ee97b9c2357871d2221e35f7e53b59`.

**Ainda pendente:** executar o checkout no PC do usuário e validar o consumo/ambiente local.

## Direção confirmada

- Assistente cloud-first acessível pelo navegador/celular.
- PC como worker opcional para ingestão e processamento pesado; núcleo básico não depende dele ligado.
- Meta de custo obrigatório zero no MVP, respeitando cotas reais dos serviços gratuitos.
- Processamento local leve devido ao i5 de primeira geração, 8 GB RAM e HDD.
- Aprovação específica para ações sensíveis.
- OpenJarvis permanece em checkout separado; reaproveitamento somente seletivo após validação local.

## Próximo passo técnico

1. Escolher o primeiro provedor remoto e validar protocolo, privacidade, cotas e custo.
2. Implementar um adaptador atrás de `ModelProvider`, mantendo MockProvider como padrão offline.
3. Definir autenticação e hospedagem antes da API pública.
4. Implementar API autenticada com isolamento de sessão.
5. Integrar memória ao contexto com consentimento, limite e proveniência.
6. Só então desenvolver worker, sincronização e UI.

## Documentação de referência

- `README.md`: visão, comandos e limites do protótipo.
- `PROJECT_STATUS.md`: histórico e situação detalhada.
- `ROADMAP.md`: fases de produto.
- `ARCHITECTURE.md`: arquitetura cloud + PC.
- `docs/MVP_SPEC.md`: escopo e critérios de aceite do MVP.
- `docs/IMPLEMENTATION_BACKLOG.md`: backlog técnico executável.
- `CODEX_HANDOFF.md`: handoff para Codex CLI.
- `DECISIONS.md`: decisões e questões pendentes.

## Regras de continuidade

- Conferir branch e alterações locais antes de editar.
- Ler `AGENTS.md` e o backlog antes de qualquer implementação.
- Não substituir o núcleo nem reimplementar funcionalidades existentes.
- Não marcar uma capacidade como pronta apenas porque há documentação.
- Não adicionar chaves ou dados privados ao Git.
- Não habilitar shell, ferramentas sensíveis, deploy ou ações externas sem aprovação.
- Toda alteração deve ter teste; toda alegação de teste precisa de evidência.


## Continuidade — permissões e handoff Codex CLI (2026-11-01)

Branch de trabalho: `feat/cognitive-adaptation-engine` (PR #1, ainda não mesclado).

Adicionado:
- `nexus_learning/permissions.py`: protótipo de gerenciador central de scopes, concessão/revogação de capacidades comuns, scopes de alto impacto com exigência de confirmação e trilha de auditoria;
- `tests/test_permissions.py`;
- `docs/ACCESS_AND_AUTONOMY.md`;
- atualização de `CODEX_HANDOFF.md` com contexto, comandos, missão imediata e prompt de continuidade para o Codex CLI.

**Atenção:** o PermissionManager ainda não está integrado ao dispatcher/runtime. A confirmação de alto impacto usa atualmente um booleano `confirmed=True`, que é insuficiente como fronteira de segurança. O Codex deve corrigir isso para aprovação confiável, de uso único, vinculada à ação exata, com expiração e prevenção de replay, antes de integrar ações reais. Enquanto não houver UI/canal confiável de aprovação, manter ações de alto impacto bloqueadas.

**Não verificado nesta sessão:** execução local dos testes e CI dos commits mais recentes. Codex deve executar compileall/unittest e conferir workflow no HEAD atual antes de declarar sucesso. Nenhuma integração real, provider remoto, browser, shell, API ou worker foi habilitada por estes arquivos.
