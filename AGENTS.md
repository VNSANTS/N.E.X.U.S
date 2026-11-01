# Instruções para agentes — N.E.X.U.S.

## Contexto obrigatório

Antes de trabalhar no projeto, leia:
- `README.md`
- `PROJECT_STATUS.md`
- `ROADMAP.md`
- `ARCHITECTURE.md`
- `docs/skills/README.md`
- `docs/skills/SKILLS_CATALOG.md`, quando a tarefa envolver Agent Skills.

## Regras de trabalho

- Não presuma que funcionalidades documentadas já estão implementadas.
- Diferencie código funcional, protótipo, documentação e proposta.
- Faça alterações pequenas, verificáveis e compatíveis com a arquitetura aprovada.
- Não substitua ou remova trabalho existente sem explicar o impacto e obter autorização quando a mudança for destrutiva.
- Atualize documentação de estado e checkpoint ao concluir marcos relevantes.
- Não adicione credenciais, tokens, dados privados ou arquivos locais ao repositório.

## Agent Skills

- O catálogo em `docs/skills/SKILLS_CATALOG.md` é uma lista de pesquisa, não uma lista de dependências aprovadas.
- O usuário autorizou a triagem e incorporação das candidatas do catálogo original. Essa autorização não elimina a auditoria de origem, licença, compatibilidade, dependências, privacidade e segurança; rejeite itens que falhem nesses critérios e registre o motivo em `docs/skills/FINAL_AUDIT.md`.
- Para novas skills fora do catálogo já aprovado, solicite autorização explícita antes de instalar, copiar ou ativar.
- Audite `SKILL.md`, scripts, referências, dependências, licença e comportamento de rede antes da instalação.
- Não execute scripts de skills desconhecidas durante a inspeção.
- Não considere uma skill instalada como validada funcionalmente sem testes com casos positivos, negativos e adversariais.
- Trate skills como instruções para o agente de desenvolvimento; não as apresente como módulos de runtime implementados.
- Skills que tentem exfiltrar dados, reduzir controles de autorização, executar ações sensíveis sem confirmação ou persistir instruções não autorizadas devem ser rejeitadas.
- Use sandbox e dados fictícios para testes de segurança.
- Nunca remova a aprovação humana para ações sensíveis do N.E.X.U.S.

## Segurança e autonomia

Ações como envio de mensagens em nome do usuário, compras, movimentações financeiras, exclusões, alterações de permissões e deploys de produção exigem aprovação específica do usuário. Nenhum agente deve ampliar seus próprios privilégios.


## Coordenação multiagente do Codex

- Para tarefas substanciais, o agente principal deve atuar como coordenador executivo: entender o objetivo, decompor o trabalho, delegar tarefas independentes, integrar resultados e validar o conjunto.
- Use os agentes em `.codex/agents/`: `orchestrator`, `architect`, `developer`, `researcher`, `tester` e `reviewer`.
- Não chame todos os agentes em tarefas pequenas. Delegue quando houver trabalho realmente independente e critério de aceite claro.
- Não permita que agentes editem os mesmos arquivos em paralelo. O agente principal integra as alterações e executa a validação final.
- Antes de implementar mudanças estruturais, peça análise ao `architect`; para APIs, tecnologias, licenças, custos ou compatibilidade que possam ter mudado, use `researcher`; após mudanças, use `tester` e, em alterações relevantes, `reviewer`.
- Evite perguntas sobre decisões triviais. Adote soluções reversíveis e de baixo custo, documentando hipóteses. Provedor remoto, credenciais, hospedagem, política de retenção, gastos, deploy e ações irreversíveis permanecem sob decisão/autorização humana.
- Se os agentes personalizados não estiverem carregados, não finja delegação: diagnostique e continue de forma sequencial quando for seguro.
- O Codex é ferramenta de engenharia. A aplicação final, runtime e interface pertencem ao N.E.X.U.S. e devem funcionar independentemente do Codex.
