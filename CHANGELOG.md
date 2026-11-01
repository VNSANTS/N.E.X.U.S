# Changelog

## 2026-10-31 — núcleo local executável e endurecimento

### Adicionado
- Núcleo SQLite para memórias episódicas, semânticas e procedurais.
- Cadastro de fontes e afirmações com estados explícitos de revisão.
- Fila de tarefas com pontuação heurística explicável e auditoria.
- Ingestão de TXT/Markdown, hash SHA-256, divisão em trechos e busca lexical.
- Política de ferramentas fail-closed e runtime textual com MockProvider offline.
- Cliente de metadados bibliográficos Crossref.
- Testes automatizados e workflow GitHub Actions para Python 3.11 e 3.12.
- Backlog técnico com a ordem de implementação e dependências pendentes.

### Endurecido nesta revisão
- SQLite `:memory:` compartilhado entre conexões curtas.
- Reivindicação condicional de tarefas para impedir execução duplicada.
- Persistência de erros sem mensagens potencialmente sensíveis do provider.
- Validação dos limites do runtime e do formato essencial da resposta.
- Testes de regressão para os casos acima.
- Workflow com path filter corrigido, permissões mínimas, timeout e compilação.

### Ainda não implementado
- Provider remoto de IA.
- API HTTP, autenticação e interface web.
- Memória automaticamente integrada ao contexto de conversa.
- Ferramentas reais, agentes paralelos ou execução de comandos.
- Cloud core, worker PC, sincronização e deploy.
- Voz, scheduler contínuo, embeddings e execução autônoma.

### Verificação
CI confirmado: execução [41255344883](https://github.com/VNSANTS/N.E.X.U.S/actions/runs/41255344883) passou em Python 3.11 e 3.12, incluindo compileall e unittest, no commit `59356b7674ee97b9c2357871d2221e35f7e53b59`. Testes no computador local também permanecem pendentes.


## 2026-10-31 — ambiente Codex multiagente

### Adicionado
- Perfis de projeto `orchestrator`, `architect`, `developer`, `researcher`, `tester` e `reviewer` em `.codex/agents/`.
- Configuração de projeto `.codex/config.toml` com multiagentes ativados e limite máximo de quatro threads simultâneas.
- Instruções persistentes de delegação em `AGENTS.md`.
- Prompt mestre de preparação que verifica o ambiente, protege o checkout, instala/valida a configuração, audita o N.E.X.U.S., executa testes e avança trabalho local desbloqueado.

### Limites
- Esta é infraestrutura de desenvolvimento do Codex, não funcionalidade do runtime N.E.X.U.S.
- Os agentes herdam autenticação, provedor e permissões da sessão principal.
- Nenhum provedor externo, credencial, serviço pago, publicação ou deploy foi configurado.


## 2026-11-01 — Cognitive Adaptation Engine (CAE)

### Adicionado
- Perfil cognitivo opt-in com SQLite, desativado por padrão.
- Preferências explícitas de comprimento, estilo de explicação, nível de desafio e estilo de discordância.
- Padrões de raciocínio propostos e só utilizados após confirmação do usuário.
- Hook opcional no TaskRuntime para incluir contexto de adaptação no prompt.
- Comandos CLI de ativação, consulta, definição de preferências e revisão de padrões.
- Testes de unidade e integração e documentação específica.

### Segurança e limites
- Sem ingestão automática de transcrições ou diagnóstico de personalidade/inteligência.
- Preferências não podem ser gravadas por inferência do modelo.
- Padrões rejeitados ou não revisados não entram no contexto.
- Desativar o CAE interrompe a injeção de contexto sem apagar o perfil.
- Integração atual testável apenas com o MockProvider; provider real permanece pendente.
- CI ainda precisa confirmar esta branch.
