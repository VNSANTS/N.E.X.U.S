# N.E.X.U.S.

**Neural Engine Expert Underground System**

Projeto de um assistente pessoal de IA que vai além de um chatbot: deverá pesquisar, organizar conhecimento, utilizar ferramentas, coordenar agentes e executar tarefas autorizadas, mantendo o usuário no controle.

> **Estado atual:** aplicação local em Python/SQLite com API WSGI autenticada, sessões e conversas persistidas, recuperação contextual lexical, UI web conectada, ferramentas READ em allowlist e worker local de tarefas seguras. MockProvider é o padrão offline; adapters opcionais estão disponíveis para Gemini, Groq e OpenRouter mediante configuração explícita. Ainda não é uma implantação cloud nem um assistente com colaboração autônoma geral entre modelos. Consulte [PROJECT_STATUS.md](PROJECT_STATUS.md) e [docs/LOCAL_API.md](docs/LOCAL_API.md).

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
| [PERSONAL_AGENT_COMPARATIVE_REVIEW_2026-11-02.md](docs/PERSONAL_AGENT_COMPARATIVE_REVIEW_2026-11-02.md) | Comparação Hermes/OpenClaw/NanoClaw e plano de evolução do N.E.X.U.S. |
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

Executar testes manuais da UI/API local; decidir provider/modelo e políticas de retenção antes de enviar dados reais. Planejar identidade, TLS e banco de produção antes de qualquer exposição remota. O checkout OpenJarvis continua separado e não é dependência do app.

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

## Executar a aplicação local

```powershell
python -m unittest discover -s tests -v
python -m nexus_learning --db nexus_learning.db serve --host 127.0.0.1 --port 8765
```

Na primeira execução, crie um usuário e uma senha forte no prompt local. Acesse `http://127.0.0.1:8765/`. O servidor é loopback-only. Para provider externo, revise `docs/LOCAL_API.md` e `.env.example`; não use credenciais no repositório. O worker seguro roda separadamente com `python -m nexus_learning --db nexus_learning.db worker --poll 1`.

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


### Ingestão local de documentos (protótipo)

O módulo `nexus_learning.ingestion` agora aceita arquivos de texto e Markdown, registra a origem, calcula SHA-256, divide o conteúdo em trechos com posições e permite busca lexical simples. Arquivos repetidos pelo mesmo conteúdo são reconhecidos pelo hash. Limite padrão: 1 MB por documento.

Formatos aceitos: `.txt`, `.md` e `.markdown`. PDF, DOCX, páginas web e extração por IA ainda não estão incluídos.

```bash
python -m nexus_learning ingest-file ./anotacoes.md
python -m nexus_learning document-search "memória e aprendizado"
```

A busca atual é lexical (termos coincidentes), não semântica. O conteúdo fica no banco SQLite local; não envie o banco ao repositório.


## Runtime controlado (protótipo offline)

O repositório agora inclui:
- `PolicyEngine`: política fail-closed com allowlist; ações READ, WRITE_REVERSIBLE e SENSITIVE;
- contrato `ModelProvider` e `MockProvider` offline, sem credenciais e sem rede;
- `TaskRuntime`: registra entrada, execução, conclusão/falha e eventos no SQLite;
- comando de demonstração offline.

```bash
python -m nexus_learning runtime-once "Olá, N.E.X.U.S."
```

O comando usa o provedor simulado, não uma IA real. O runtime ainda não possui API HTTP, autenticação, ferramentas reais, agendador distribuído ou worker remoto. Nenhuma saída de modelo executa comandos ou ferramentas.


### Pesquisa científica pela Crossref API

O módulo `nexus_learning.crossref` consulta metadados bibliográficos públicos da Crossref, sem dependências externas e sem chave de API. A busca retorna título, autores, ano, DOI, periódico/editora e URL. Não baixa o texto integral dos artigos, não cria afirmações automaticamente e não valida os resultados.

```bash
python -m nexus_learning research-search "memory consolidation learning" --limit 5
# Opcional: informar um e-mail válido para usar o polite pool
python -m nexus_learning research-search "neuroscience of memory" --limit 5 --mailto "seu-email@example.com"
```

O limite local é de 20 resultados por consulta, com timeout de 12 segundos. A integração usa a biblioteca padrão do Python, identifica o cliente por User-Agent e permite o parâmetro `mailto` recomendado pela Crossref. Respeite os limites do serviço e evite consultas paralelas desnecessárias. Os metadados retornados são pistas para pesquisa, não evidência suficiente para validar uma afirmação.
