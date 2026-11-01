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


## Revisão de continuidade — CAE e permissões (2026-11-01)

### Contexto do usuário e objetivo

O usuário autorizou amplo acesso às capacidades comuns do N.E.X.U.S.: memória, perfil cognitivo, pesquisa, conhecimentos, criação de skills, agentes, ferramentas, arquivos autorizados, execução local e gerenciamento de projetos. A intenção é um assistente pessoal com autonomia ampla para pesquisar, aprender, organizar, planejar e executar tarefas comuns dentro das permissões concedidas.

Essa autorização não cria integrações nem credenciais automaticamente. O sistema deve usar apenas adaptadores realmente implementados e permissões concedidas pelo sistema operacional/serviço. Ações de alto impacto continuam com confirmação específica, verificável e vinculada à ação.

### Estado adicionado nesta branch

- `nexus_learning/cognitive.py`: CAE com preferências explícitas e padrões revisados pelo usuário.
- `nexus_learning/permissions.py`: primeira versão de `PermissionManager`, scopes comuns, scopes de confirmação, revogação e auditoria.
- `docs/COGNITIVE_ADAPTATION.md` e `docs/ACCESS_AND_AUTONOMY.md`.
- `tests/test_cognitive.py`, `tests/test_cognitive_runtime.py` e `tests/test_permissions.py`.
- PR de trabalho: https://github.com/VNSANTS/N.E.X.U.S/pull/1
- Branch de trabalho: `feat/cognitive-adaptation-engine`.

### Limitação de segurança que deve ser corrigida antes de integrar

A versão atual de `PermissionManager.authorize(scope, confirmed=True)` aceita um booleano como sinal de confirmação. Isso é útil apenas como protótipo de API e **não é uma fronteira de segurança suficiente**: um agente/modelo não pode ter a capacidade de passar esse sinal. Substitua por aprovação de uso único emitida por uma fronteira confiável, vinculada ao usuário, ferramenta, parâmetros/ação exata, escopo, expiração e nonce; consuma-a atomicamente e impeça replay. Se a UI confiável ainda não existir, mantenha as ações de confirmação bloqueadas. Não simule aprovação.

O PermissionManager também ainda não está integrado ao runtime ou ao despacho de ferramentas. Não afirme que os scopes liberaram recursos reais. Integre a política central antes de adicionar ferramentas executáveis.

### Missão imediata para o Codex CLI

1. Preserve o estado local: `git status --short --branch`; não descarte alterações.
2. Sincronize a branch sem operações destrutivas:
   ```bash
   git fetch origin
   git switch feat/cognitive-adaptation-engine
   git pull --ff-only
   ```
3. Leia `AGENTS.md`, `README.md`, `PROJECT_STATUS.md`, `ROADMAP.md`, `ARCHITECTURE.md`, `DECISIONS.md`, `CHECKPOINT.md`, `docs/IMPLEMENTATION_BACKLOG.md`, `docs/ACCESS_AND_AUTONOMY.md` e `docs/COGNITIVE_ADAPTATION.md`.
4. Inspecione diff e código real. Execute:
   ```bash
   python --version
   python -m compileall -q nexus_learning tests
   python -m unittest discover -s tests -v
   python -m nexus_learning --help
   ```
5. Verifique o CI do HEAD atual; a execução anterior citada em documentos pode não incluir os commits mais recentes.
6. Faça auditoria independente do CAE e PermissionManager, incluindo migração, SQLite, concorrência, revogação, auditoria, autorização de scopes e abuso de aprovação.
7. Implemente aprovação de uso único, confiável, vinculada à ação exata e com proteção contra replay. Integre o gerenciador ao dispatcher central de ferramentas. Continue fail-closed.
8. Adicione testes positivos, negativos, adversariais e de regressão. Não use dados pessoais reais.
9. Atualize status, checkpoint, changelog e backlog somente com fatos comprovados.

### Próxima entrega vertical sugerida

Após estabilizar as permissões, preparar o primeiro provider real atrás de `ModelProvider`, mas só depois de pesquisar opções atuais de preço, cotas, privacidade, termos e compatibilidade. MockProvider deve continuar padrão de testes e modo offline. Segredos devem ser configurados localmente pelo usuário; nunca pedir para colar chave no chat nem gravar no Git. Não implementar API/cloud/worker antes das decisões de autenticação e hospedagem.

### Prompt de início para o Codex CLI

> Continue o N.E.X.U.S. a partir do estado real do repositório. Leia integralmente AGENTS.md e os documentos de continuidade. Preserve alterações locais. Audite a branch atual, o CAE e o PermissionManager; execute compileall, a suíte unittest e verifique CI. A prioridade é corrigir a aprovação sensível: o booleano confirmed=True atual não é seguro. Projete e implemente aprovação verificável, de uso único, emitida por uma fronteira confiável, vinculada à ação exata, com expiração, nonce e prevenção de replay. Integre a autorização ao dispatcher central antes de criar ferramentas reais. Não deixe o modelo conceder privilégios a si próprio. Não invente integrações, credenciais ou testes. Mantenha o padrão fail-closed, adicione testes positivos/negativos/adversariais, atualize documentação e entregue relatório final com funcionalidades comprovadas, limitações, testes executados e próximos passos. Não faça merge, deploy ou ações externas irreversíveis sem aprovação explícita.
