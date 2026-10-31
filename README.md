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

Validar no PC a cópia local do OpenJarvis comparando-a com o commit auditado, executar um subconjunto pequeno de testes offline e medir recursos. Depois, fechar provedor, autenticação e hospedagem antes de implementar o MVP.

## Ambiente de desenvolvimento

O desenvolvimento considera um computador modesto. Portanto, a arquitetura não deve depender de modelos locais grandes nem de processamento contínuo. Custos de APIs e hospedagem precisam ser avaliados antes de adicionar serviços pagos.

---

**N.E.X.U.S. — um assistente pessoal útil, capaz e confiável, sempre sob controle do usuário.**


## Primeiro módulo executável — motor de aprendizado

Foi iniciado `nexus_learning/`, um núcleo Python baseado apenas na biblioteca padrão:
- SQLite para memórias episódicas, semânticas e procedurais;
- cadastro de fontes e afirmações candidatas ligadas às fontes;
- estados de conhecimento e revisão explícita;
- fila de tarefas com prioridade heurística transparente;
- testes automatizados iniciais em `tests/test_learning_engine.py`.

Este módulo é uma primeira base local. Ainda não inclui API, interface, pesquisa automática na web, integração com modelos de IA, sincronização cloud/PC ou execução contínua. Consulte [a arquitetura de aprendizado](docs/LEARNING_ARCHITECTURE_NEUROSCIENCE.md).


### Uso local do protótipo

Com Python 3 instalado, na raiz do repositório:

```bash
python -m nexus_learning init
python -m nexus_learning stats
python -m nexus_learning memory-add episodic "Primeiro teste" "Descrição do evento"
python -m nexus_learning memory-list
python -m nexus_learning task-add "Estudar memória" --relevance 0.9 --uncertainty 0.8
python -m nexus_learning task-list
python -m unittest discover -s tests -v
```

O banco padrão é `nexus_learning.db` no diretório atual. Não coloque dados sensíveis no banco de teste nem envie o arquivo do banco ao GitHub.


### Comandos adicionais do núcleo

```bash
# Registrar uma fonte e uma afirmação associada
python -m nexus_learning source-add "https://example.org" --title "Fonte de exemplo"
python -m nexus_learning claim-add "Afirmação a investigar" --source ID_DA_FONTE

# Revisar uma afirmação (validação exige justificativa e confiança explícitas)
python -m nexus_learning claim-review ID_DA_AFIRMACAO under_review "Precisa de mais evidências"
python -m nexus_learning claim-list --state proposed

# Gerar relatório de consolidação sem alterar automaticamente os registros
python -m nexus_learning consolidate

# Arquivar uma memória
python -m nexus_learning memory-archive ID_DA_MEMORIA
```

O relatório de consolidação aponta afirmações sem fontes, possíveis duplicatas, itens em disputa e itens ainda não revisados. Ele não decide se uma afirmação é verdadeira e não modifica o banco.
