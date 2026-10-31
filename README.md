# N.E.X.U.S.

**Neural Engine Expert Underground System**

Projeto de um assistente pessoal de IA que vai além de um chatbot: deverá pesquisar, organizar conhecimento, utilizar ferramentas, coordenar agentes e executar tarefas autorizadas, mantendo o usuário no controle.

> **Estado atual:** base de planejamento e documentação. O runtime ainda não foi implementado nem validado neste repositório.

## Visão do projeto

- **Cloud-first:** acessível pelo celular e navegador, sem depender de um computador potente ligado o tempo todo.
- **Multimodelo:** possibilidade de selecionar provedores conforme tarefa, qualidade e custo.
- **Ollama opcional:** execução local quando fizer sentido, sem ser requisito.
- **Interação multimodal:** texto, botão e voz, evoluindo por etapas.
- **Agentes e ferramentas:** módulos especializados trabalhando sob limites claros.
- **Aprendizado rastreável:** pesquisa, comparação de fontes, validação e registro de incertezas — não treinamento automático e contínuo dos pesos do modelo.
- **Autonomia controlada:** tarefas agendadas e acionadas por eventos, com orçamento, limites e aprovações.

## Princípios de segurança

- Ações sensíveis exigem aprovação explícita e específica.
- Mensagens enviadas em nome do usuário, compras, movimentações financeiras, exclusões e mudanças de produção não serão executadas sem autorização.
- Melhorias propostas pelo próprio sistema devem ser testadas em ambiente isolado e revisadas antes de serem integradas.
- Não armazenar nem publicar credenciais, tokens, dados pessoais ou conversas privadas.

## Documentação

| Documento | Conteúdo |
|---|---|
| [PROJECT_STATUS.md](PROJECT_STATUS.md) | Estado atual, próximo marco e riscos |
| [ROADMAP.md](ROADMAP.md) | Fases e critérios para avançar |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Arquitetura conceitual |
| [TECH_STACK.md](TECH_STACK.md) | Tecnologias em avaliação |
| [LEARNING_ENGINE.md](LEARNING_ENGINE.md) | Pesquisa e aprendizado |
| [KNOWLEDGE_SYSTEM.md](KNOWLEDGE_SYSTEM.md) | Conhecimento e fontes |
| [MEMORY_SYSTEM.md](MEMORY_SYSTEM.md) | Memória pessoal e contexto |
| [HUMAN_INTERACTION.md](HUMAN_INTERACTION.md) | Interação com o usuário |
| [SELF_IMPROVEMENT.md](SELF_IMPROVEMENT.md) | Melhorias controladas |
| [KNOWLEDGE_VALIDATION.md](KNOWLEDGE_VALIDATION.md) | Validação e confiança |
| [SECURITY.md](SECURITY.md) | Segurança e permissões |
| [DECISIONS.md](DECISIONS.md) | Decisões do projeto |
| [CHECKPOINT.md](CHECKPOINT.md) | Ponto de continuidade |
| [CHANGELOG.md](CHANGELOG.md) | Histórico de mudanças |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Regras de contribuição |

## Próximo passo

Revisar a arquitetura v1 e definir o MVP executável. Antes da implementação, auditar o código-base/OpenJarvis que se pretende reaproveitar, confirmar stack, dependências e licença, e então detalhar contratos e testes de aceitação.

## Ambiente de desenvolvimento

O desenvolvimento considera um computador modesto. Portanto, a arquitetura não deve depender de modelos locais grandes nem de processamento contínuo. Custos de APIs e hospedagem precisam ser avaliados antes de adicionar serviços pagos.

---

**N.E.X.U.S. — um assistente pessoal útil, capaz e confiável, sempre sob controle do usuário.**
