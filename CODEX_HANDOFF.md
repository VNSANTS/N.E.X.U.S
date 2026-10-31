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
