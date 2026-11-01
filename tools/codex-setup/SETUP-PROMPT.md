# Prompt único de instalação

Cole o texto abaixo no Codex CLI com o repositório N.E.X.U.S. aberto na raiz. O Codex deve executar a instalação no computador atual, não apenas explicar como fazer.

---

Você é o responsável por preparar o ambiente local de desenvolvimento multiagente do N.E.X.U.S. Execute a instalação de ponta a ponta, com cuidado e sem alterar o código da aplicação.

1. Confirme que o diretório atual é a raiz do repositório N.E.X.U.S. e que existem os seis arquivos em `.codex/agents/`. Se não estiver na raiz ou os arquivos não existirem, pare e explique o bloqueio.
2. Verifique o sistema operacional, a versão do Codex CLI e a documentação/ajuda local disponível. Confirme os caminhos e opções compatíveis com esta versão. Não invente comandos.
3. Faça backup dos arquivos existentes que serão alterados. Nunca sobrescreva silenciosamente configurações pessoais.
4. No Windows, instale os seis arquivos TOML em `$env:USERPROFILE\.codex\agents\`. Preserve agentes pessoais de mesmo nome: compare conteúdos e faça backup antes de substituir. Se houver conflito não seguro, pare e peça confirmação.
5. Verifique `$env:USERPROFILE\.codex\config.toml`. Preserve todas as configurações existentes. Garanta `agents.enabled = true` e configure `agents.max_concurrent_threads_per_session = 4` apenas se a versão instalada aceitar essa opção. Se já existir seção [agents], atualize somente a chave necessária; não crie uma segunda seção. Faça backup antes de editar. Não altere modelo, autenticação, provedor, sandbox ou política de aprovação.
6. Não instale Gemini, API keys, extensões, pacotes externos ou ferramentas pagas. A autenticação continuará sendo a sessão nativa já configurada no Codex.
7. Valide a sintaxe TOML, confirme que os seis agentes estão no diretório correto e use somente comandos de diagnóstico suportados pela versão instalada. Não alegue que agentes foram executados se não tiver iniciado uma tarefa real.
8. Se o Codex precisar ser reiniciado para carregar agentes, informe isso e forneça o comando correto para reabrir o CLI no diretório atual.
9. Não faça commit, push, deploy, publicação nem alterações no código da aplicação. Esta tarefa é somente preparação local do ambiente.

Ao terminar, mostre um relatório objetivo: sistema e versão detectados, arquivos instalados, backups criados, configuração ajustada, verificações realizadas, limitações e o que ainda exige ação manual. Se qualquer etapa for insegura ou impossível, não improvise: pare nessa etapa, preserve o estado anterior e explique o motivo.

Depois da instalação, use o agente `orchestrator` para coordenar tarefas maiores do N.E.X.U.S. Delegue apenas trabalho independente, evite edições concorrentes nos mesmos arquivos e integre os resultados antes de concluir.
