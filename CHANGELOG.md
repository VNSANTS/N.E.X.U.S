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
