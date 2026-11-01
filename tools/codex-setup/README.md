# Preparação multiagente do Codex para o N.E.X.U.S.

Este diretório documenta a preparação do ambiente de engenharia do N.E.X.U.S. Ele não faz parte do runtime da aplicação final.

## Equipe personalizada

Os agentes versionados em `.codex/agents/`:

- `orchestrator`: coordenação, decomposição e integração.
- `architect`: arquitetura e impacto.
- `developer`: implementação delimitada.
- `researcher`: pesquisa técnica e documentação oficial.
- `tester`: testes e reprodução de falhas.
- `reviewer`: revisão independente e segurança.

A configuração de projeto em `.codex/config.toml` ativa as ferramentas multiagente e define um limite de até quatro threads simultâneas. O Codex só carrega a configuração local quando o repositório é confiável. O limite não garante que todas as vagas serão usadas e agentes consomem uso adicional.

## Instalação de uma só vez

Abra `VNSANTS/N.E.X.U.S` na raiz pelo VS Code, inicie o Codex CLI e cole o conteúdo completo de [SETUP-PROMPT.md](./SETUP-PROMPT.md).

O prompt mestre prepara o ambiente, confere o checkout e as configurações, lê a documentação do N.E.X.U.S., executa testes, corrige problemas locais seguros e avança tarefas desbloqueadas do backlog. Não faz push, deploy, não instala provedores externos e não modifica o runtime sem necessidade.

## Segurança e limites

- Os subagentes herdam autenticação, provedor, permissões e ferramentas da sessão principal.
- Os perfis não criam cotas independentes nem permitem contornar limites do plano ChatGPT.
- Não coloque tokens, senhas ou chaves de API no repositório.
- Não permita deploy, publicação, exclusões destrutivas ou gastos sem aprovação humana.
- A preparação do Codex não significa que o N.E.X.U.S. já tenha interface, API ou runtime remoto. Essas partes precisam ser implementadas e testadas como produto independente.

Documentação oficial:
- [Subagentes](https://learn.chatgpt.com/docs/agent-configuration/subagents)
- [AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
- [Configuração por projeto](https://learn.chatgpt.com/docs/config-file/config-basic)
