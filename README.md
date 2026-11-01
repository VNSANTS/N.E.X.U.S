# N.E.X.U.S.

**Neural Engine Expert Underground System**

Projeto de um assistente pessoal de IA que vai além de um chatbot: deverá pesquisar, organizar conhecimento, utilizar ferramentas, coordenar agentes e executar tarefas autorizadas, mantendo o usuário no controle.

> **Estado atual:** núcleo local Python/SQLite e runtime offline com MockProvider; ainda não há provider real, API, autenticação ou deploy. O CAE foi adicionado em branch de implementação; CI passou em Python 3.11 e 3.12.

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
| [DECISIONS.md](DECISIONS.md) | Decisões de arquitetura |
| [CHECKPOINT.md](CHECKPOINT.md) | Ponto de continuidade |
| [CHANGELOG.md](CHANGELOG.md) | Histórico de mudanças |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Regras de contribuição |
| [docs/COGNITIVE_ADAPTATION.md](docs/COGNITIVE_ADAPTATION.md) | Cognitive Adaptation Engine (CAE) |

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
python -m nexus_learning source-add "https://example.org" --title "Fonte de exemplo"
python -m nexus_learning claim-add "Afirmação a investigar" --source ID_DA_FONTE
python -m nexus_learning claim-review ID_DA_AFIRMACAO under_review "Precisa de mais evidências"
python -m nexus_learning claim-list --state proposed
python -m nexus_learning consolidate
python -m nexus_learning memory-archive ID_DA_MEMORIA
```

## Ingestão local de documentos (protótipo)

O módulo `nexus_learning.ingestion` aceita arquivos de texto e Markdown, registra a origem, calcula SHA-256, divide o conteúdo em trechos com posições e permite busca lexical simples. Formatos aceitos: `.txt`, `.md` e `.markdown`. Limite padrão: 1 MB.

```bash
python -m nexus_learning ingest-file ./anotacoes.md
python -m nexus_learning document-search "memória e aprendizado"
```

A busca é lexical, não semântica. PDF/DOCX, web, OCR e extração por IA ainda não estão incluídos.

## Runtime controlado (protótipo offline)

O núcleo inclui política fail-closed, contrato de provedor e MockProvider offline. O runtime registra tarefas e eventos, mas não possui provider real, ferramentas reais ou execução de comandos.

```bash
python -m nexus_learning runtime-once "Olá, N.E.X.U.S."
```

## Cognitive Adaptation Engine (CAE) — primeira implementação

O CAE adiciona preferências explícitas e padrões de raciocínio revisados pelo usuário. Fica desativado por padrão; padrões só entram no contexto depois de confirmação humana. Não faz diagnóstico psicológico nem armazena transcrições automaticamente.

```bash
python -m nexus_learning cognitive-status
python -m nexus_learning cognitive-preference-set response_length short
python -m nexus_learning cognitive-pattern-propose "Questiona premissas antes de aceitar um problema" "Padrão observado em tarefas de raciocínio." --confidence 0.7
python -m nexus_learning cognitive-pattern-review ID_DO_PADRAO confirmed "Confirmado pelo usuário."
python -m nexus_learning cognitive-enable
python -m nexus_learning cognitive-disable
```

Consulte [docs/COGNITIVE_ADAPTATION.md](docs/COGNITIVE_ADAPTATION.md). O hook já pode fornecer o contexto ao runtime, mas o runtime atual usa MockProvider; integração com modelo real ainda não foi feita.
