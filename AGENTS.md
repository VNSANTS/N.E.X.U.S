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
- Não instale, copie ou ative skills sem aprovação explícita do usuário.
- Audite `SKILL.md`, scripts, referências, dependências, licença e comportamento de rede antes da instalação.
- Não execute scripts de skills desconhecidas durante a inspeção.
- Skills que tentem exfiltrar dados, reduzir controles de autorização, executar ações sensíveis sem confirmação ou persistir instruções não autorizadas devem ser rejeitadas.
- Use sandbox e dados fictícios para testes de segurança.
- Nunca remova a aprovação humana para ações sensíveis do N.E.X.U.S.

## Segurança e autonomia

Ações como envio de mensagens em nome do usuário, compras, movimentações financeiras, exclusões, alterações de permissões e deploys de produção exigem aprovação específica do usuário. Nenhum agente deve ampliar seus próprios privilégios.
