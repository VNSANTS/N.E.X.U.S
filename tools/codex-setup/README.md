# Preparação multiagente do Codex para o N.E.X.U.S.

Este diretório guarda a configuração versionada dos agentes personalizados usados no desenvolvimento do N.E.X.U.S. Ela não faz parte do runtime da aplicação final.

## Agentes
- `orchestrator`: coordena planejamento, delegação, integração e validação.
- `architect`: análise de arquitetura.
- `developer`: implementação delimitada.
- `researcher`: pesquisa técnica e documentação oficial.
- `tester`: testes e reprodução de defeitos.
- `reviewer`: revisão independente.

## Instalação
A configuração do projeto fica em `.codex/agents/`. O Codex também permite agentes pessoais em `~/.codex/agents/`. Para instalar globalmente no Windows, copie os seis arquivos TOML para `%USERPROFILE%\.codex\agents\`.

Use [SETUP-PROMPT.md](./SETUP-PROMPT.md): cole o prompt no Codex CLI com o repositório aberto na raiz. Ele orienta a verificar o ambiente, fazer backup, instalar os agentes, ajustar com segurança a concorrência e validar a configuração.

## Limites e segurança
- Subagentes herdam autenticação, provedor, permissões e ferramentas da sessão principal. Não criam cotas independentes nem usam outro provedor.
- O número configurado é um limite máximo, não garantia de paralelismo ou capacidade disponível.
- A instalação não ativa um orquestrador persistente automaticamente. Em cada tarefa, peça ao Codex para atuar como coordenador ou iniciar pelo agente `orchestrator`.
- Não coloque tokens, senhas ou chaves de API neste repositório.
- Não permita deploy, publicação, exclusões destrutivas ou gastos sem confirmação humana.

Documentação oficial: [Subagentes](https://learn.chatgpt.com/docs/agent-configuration/subagents) e [Configuração](https://learn.chatgpt.com/docs/config-file/config-reference).
