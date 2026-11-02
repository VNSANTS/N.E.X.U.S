# N.E.X.U.S. — tarefas reservadas ao Codex CLI

Este arquivo é o handoff operacional. O trabalho já implementado no repositório não deve ser refeito. O Codex deve primeiro auditar o estado atual e executar as tarefas abaixo com commits pequenos.

## Estado conhecido
- Núcleo SQLite de memórias, fontes, afirmações, tarefas e auditoria.
- Ingestão local de TXT/Markdown com hash, chunking e busca lexical.
- Política fail-closed e contrato de provedor + mock offline.
- Runtime inicial de conversa com estados e trilha de eventos.
- CI com unittest em Python 3.11 e 3.12.

## Missão do Codex CLI
1. Clonar/abrir o repositório e ler `ARCHITECTURE.md`, `PROJECT_STATUS.md`, `ROADMAP.md` e este arquivo.
2. Conferir o código real e executar `python -m unittest discover -s tests -v`. Não afirmar que passou sem saída de sucesso.
3. Corrigir falhas com testes de regressão, sem remover funcionalidades nem enfraquecer a política.
4. Executar `python -m compileall -q nexus_learning tests`.
5. Verificar o CLI: `python -m nexus_learning --help`, inicialização do banco e ingestão/busca de um TXT/MD temporário.
6. Adicionar adaptador real de IA somente depois de confirmar o provedor escolhido e suas condições. Não inventar chave, endpoint ou modelo. Ler segredo de variável de ambiente; nunca registrar segredo ou incluí-lo no Git.
7. Criar configuração por variáveis de ambiente com validação, limites de tokens/timeout e erros seguros. Manter MockProvider como modo padrão/offline.
8. Construir API HTTP mínima apenas após escolher framework e autenticação. Preferir dependências pequenas. Não expor o banco SQLite, painel administrativo ou worker sem autenticação.
9. Construir worker de PC com conexão de saída autenticada, polling limitado, allowlist de tipos de tarefa, heartbeat, lease/timeout, retry limitado, cancelamento e sincronização versionada. Nunca abrir shell remoto, porta de entrada pública ou execução arbitrária de comandos.
10. Criar instalação e execução documentadas para Windows/Linux, com opção sem modelo local e consumo baixo de RAM/CPU.
11. Adicionar testes de segurança: prompt injection em conteúdo externo, ferramenta não allowlisted, falta de aprovação, segredo ausente, timeout, falha do provedor, cancelamento, retry e corrupção de estado.
12. Atualizar `PROJECT_STATUS.md` e `ROADMAP.md` com fatos comprovados, limitações e comandos executados.

## Regras obrigatórias
- Não executar ações externas, compras, mensagens, publicações, exclusões ou deploy sem aprovação explícita.
- Não permitir que saída de LLM conceda permissões, altere política, instale skills ou execute código.
- Não implementar autoedição/autotreinamento de pesos.
- Não coletar dados pessoais além do necessário.
- Não tornar Ollama, Docker, GPU dedicada ou modelo local grande obrigatórios.
- Não adicionar custos recorrentes nem exigir cartão no MVP.
- Não adicionar chaves, bancos de dados, logs pessoais ou documentos privados ao repositório.
- Toda mudança deve incluir testes; toda alegação de teste deve ter evidência de execução.
- Se faltar uma decisão humana (provedor, domínio, credencial, política de dados), deixar interface/configuração preparada e documentar a decisão pendente em vez de adivinhar.

## Critérios de aceite
- Testes existentes continuam passando.
- Runtime com MockProvider funciona sem internet e sem credenciais.
- Política nega por padrão ferramentas não cadastradas e ações sensíveis sem aprovação.
- Nenhuma ferramenta real é executada pelo modelo.
- Documentação separa claramente implementado, protótipo e pendente.


## Revisão de continuidade — 2026-10-31

Antes de iniciar qualquer módulo novo:
1. Leia `docs/IMPLEMENTATION_BACKLOG.md`; ele é a ordem operacional atual.
2. Leia `CHECKPOINT.md` e confirme a branch/commit local.
3. Execute `python -m compileall -q nexus_learning tests`.
4. Execute `python -m unittest discover -s tests -v`.
5. Confirme que o teste `tests/test_runtime_hardening.py` cobre SQLite `:memory:`, erro sensível de provider e reivindicação duplicada de tarefa.
6. Não implemente API, provider remoto ou worker antes de registrar as decisões de provedor, credenciais, autenticação e hospedagem.
7. Preserve MockProvider como padrão offline e mantenha mensagens de erro sem conteúdo sensível.

CI de referência para o hardening: https://github.com/VNSANTS/N.E.X.U.S/actions/runs/41255344883 (Python 3.11 e 3.12: compileall e unittest com sucesso).


## Reliability foundation — 2026-11-02

- Created development branch `dev/reliability-zero-cost-foundation` from the audited `main` commit `852131e52f454175c501e6f36bcea2c04a73e9e7`. Main remains unchanged.
- Removed the duplicate `ProviderBudget.can_reserve` definition.
- Added conservative UTF-8 byte-based text estimates and per-message framing allowance; used the shared estimator in provider accounting and automatic routing. These are safety estimates, not tokenizer-exact counts. Provider usage returned by a provider remains preferred when available.
- Expired 401 sessions now clear the stale browser `sessionStorage` token before showing login again.
- Added unit tests for estimator behavior and malformed input.
- Validation is pending GitHub Actions on this branch. No live provider calls, paid requests, deployment, or local-machine changes were performed.
- Remaining hardening: task-aware preflight accounting, provider-specific tokenizers/usage normalization, robust tests for browser session lifecycle, and per-claim citation support validation.


### Additional budget hardening — 2026-11-02

- The remote-provider budget now rejects non-integer, boolean, or negative token reservations before writing usage records.
- Routing preflight and the atomic reservation gate both fail closed when either configured model token price is zero or invalid, including legacy/corrupted settings.
- Added regression tests for corrupted zero output pricing and invalid token reservations. GitHub Actions is being re-run against the final branch head; the earlier successful run covered the preceding code revision, not these last regression tests.


### Phase 2 — Evidence quality foundation (2026-11-02)

- Added deterministic claim evidence assessment: linked source count, HTTP(S) URL validity, non-empty excerpt coverage, distinct-domain count, and explicit issue codes.
- Claim promotion to `validated` now requires every linked source to have a valid HTTP(S) URL and a non-empty excerpt. Claims with no source, local-only URI, or missing excerpts remain unvalidated.
- Confidence validation rejects booleans, non-numeric values, NaN, infinity, and values outside 0–1. Claim creation/review input types are hardened.
- Claim detail/list API now exposes `evidence_quality`; the Knowledge dashboard shows completeness and warnings.
- The system explicitly reports that provenance/completeness checks do not prove an excerpt semantically supports a claim. Semantic entailment and contradiction review remain future work and must not be automated as fact without a verifiable method.
- GitHub Actions passed on the phase code/UI head: 127 tests on Python 3.11 and 127 on Python 3.12; compileall succeeded.


### Phase 3 — Memory retrieval and governance (in progress, 2026-11-02)

- Memory writes now validate title/body types and size, require object-shaped JSON metadata, reject NaN/infinity/non-JSON values, and cap metadata at 8 KiB. Search query and limit types are checked.
- Context retrieval now ranks lexical matches with title weighting, groups multiple sources for the same validated claim, returns matched terms and retrieval-method metadata, and exposes bounded diagnostics via `retrieve_detailed` while preserving the existing `retrieve` interface.
- Added an authenticated `/api/v1/context/preview` endpoint and a dashboard preview that explicitly uses lexical-only retrieval, avoiding embedding/provider calls and cost during inspection.
- Fixed the memory category selector to offer only the supported episodic, semantic and procedural values (the previous UI default `note` was invalid).
- Added context and memory boundary tests. The latest full CI run is queued behind an older GitHub Actions run that has not reported job steps; do not treat Phase 3 as validated until the latest branch-head run completes successfully.


### Continuidade verificada — 2026-11-02

- Corrigido o diagnóstico da recuperação lexical: termos encontrados somente no título agora aparecem em `matched_terms`, alinhando explicabilidade e pontuação.
- Contratos de agentes agora validam IDs, papéis, operações, contexto permitido, estados de resultado e limites inteiros de passos (1–10). Isso fortalece a delegação determinística; **não** transforma os papéis em agentes LLM independentes nem habilita colaboração autônoma.
- Registro de ferramentas agora rejeita nomes/descrições/esquemas inválidos, classes de risco desconhecidas e permissões menos restritivas que o risco declarado.
- GitHub Actions passou no commit `26c77c3d0e3b7140e9bde3c1569d3c42e5443f6b`: **138 testes** em Python 3.11 e **138 testes** em Python 3.12; compilação dos módulos Python também passou.
- Os trabalhos continuam na branch de desenvolvimento. `main` permanece intacta; nenhum deploy, serviço remoto, provedor pago ou cobrança foi ativado.
