# Auditoria técnica — OpenJarvis como base do N.E.X.U.S.

**Data:** 2026-10-31  
**Fonte auditada:** https://github.com/open-jarvis/OpenJarvis  
**Branch:** `main`  
**Commit consultado:** `570d75425d50592d931bac7a17ce6b2621561c06` (31/10/2026)  
**Licença declarada:** Apache License 2.0  
**Escopo:** inspeção remota de estrutura, documentação, manifesto de dependências e arquivos centrais.  
**Não realizado:** clone/instalação local, execução de scripts, build, inicialização, benchmark ou suíte de testes. Portanto, este relatório é uma auditoria estática preliminar, não certificação de funcionamento.

## 1. Veredito executivo

**OpenJarvis é um framework substancial e real, não apenas uma demonstração de interface.** O repositório apresenta componentes implementados para inferência, agentes, ferramentas, memória documental, canais, agendamento, aprendizado por traces, interface web/desktop, segurança e testes.

**Recomendação para o N.E.X.U.S.: REAPROVEITAR SELETIVAMENTE; não adotar o repositório inteiro como produto-base neste momento.**

Motivos:
- O escopo do OpenJarvis é amplo e inclui muitos recursos que não pertencem ao primeiro MVP do N.E.X.U.S.
- O foco declarado é local-first/on-device; o N.E.X.U.S. tem direção cloud-first, com local opcional.
- O pacote possui uma base de dependências e extras extensa, incluindo canais, telemetria, datasets e recursos de hardware.
- A interface e o CLI já são um produto próprio. Substituí-los ou adaptá-los integralmente pode prender o N.E.X.U.S. à estrutura e às decisões do upstream.
- Há componentes valiosos que podem ser estudados e adaptados atrás de interfaces próprias.

**Regra de preservação:** o projeto upstream fica em sua própria pasta/repositório. Não alterar, sobrescrever ou converter OpenJarvis diretamente em N.E.X.U.S. A implementação do N.E.X.U.S. permanece no repositório `VNSANTS/N.E.X.U.S`.

## 2. Identidade, licença e maturidade declarada

- Repositório oficial: `open-jarvis/OpenJarvis`.
- Linguagem principal declarada: Python.
- README declara suporte a Python `>=3.10`; o `pyproject.toml` restringe a `>=3.10,<3.14`.
- Licença declarada no GitHub e em `LICENSE`: Apache-2.0.
- Classificador de desenvolvimento no manifesto: **Alpha**.
- README descreve o produto como framework de IA pessoal em dispositivos pessoais e plataforma de pesquisa/produção.
- O repositório contém código, documentação, exemplos, frontend, componentes Rust, configurações e testes.

A licença Apache-2.0 permite uso e adaptação sob suas condições, incluindo preservar avisos aplicáveis, incluir cópia da licença e marcar arquivos modificados. Antes de redistribuir uma cópia ou derivação, revisar também arquivos NOTICE e licenças de dependências/ativos individuais. A licença do projeto não transfere marcas registradas.

## 3. Dimensão observada do código

Na árvore consultada:
- 2.461 entradas no Git tree (árvore não truncada).
- 687 arquivos Python em `src/openjarvis/`.
- 716 arquivos Python sob `tests/`.
- Pastas relevantes incluem `agents`, `engine`, `tools`, `memory`, `learning`, `security`, `server`, `sessions`, `scheduler`, `channels`, `connectors`, `speech`, `sandbox`, `frontend`, `desktop` e `rust`.

Essas contagens mostram escala e cobertura de testes no repositório, mas **não provam que os testes passam** nem que todos os caminhos estão funcionais.

## 4. O que existe no código (e o que ainda exige validação)

| Área | Evidência encontrada | Avaliação para N.E.X.U.S. |
|---|---|---|
| Inferência/modelos | ABC `InferenceEngine`, adaptadores Ollama, cloud e outros backends; descoberta/health e interface uniforme | **Alta reutilização conceitual**; estudar adaptadores cloud e contratos. |
| Agentes | `BaseAgent`, `ToolUsingAgent`, agentes simple, orchestrator, ReAct e outros; loop de tool calling e limite de turnos | **Alta**; aproveitar contrato/padrões, simplificando para um único agente no MVP. |
| Ferramentas | `BaseTool`, `ToolSpec`, registry, executor com workers e fila limitados; metadados de timeout e capabilities | **Alta com revisão**; integrar apenas uma ferramenta READ inicialmente. |
| Memória | SQLite/FTS5 e backends opcionais FAISS, ColBERT, BM25 e híbrido; ingestão e recuperação documental | **Parcial**; útil para memória de documentos/conhecimento, mas não equivale à memória pessoal consentida do N.E.X.U.S. |
| Aprendizado | traces, análise de resultados e políticas de roteamento/modelo; políticas de treino aparecem em diferentes estados | **Referência forte**; não assumir que há autoaprendizado geral pronto. |
| Segurança | capabilities, scanner de prompt/PII/segredos, política de arquivos, rate limiting, audit, SSRF e sandbox | **Reaproveitar após hardening e configuração**; não confiar em defaults sem teste. |
| Aprovações | tool confirmation, callbacks, capability policy e ApprovalStore com memória de permissões | **Revisão obrigatória**; N.E.X.U.S. manterá confirmação específica para cada ação sensível, sem "aprovar sempre" nessas categorias. |
| Agendamento | AgentScheduler com cron/intervalo e execução em thread de fundo; agentes persistentes e monitoramento | **Fora do MVP**; adaptar mais tarde para jobs limitados e desligados por padrão. |
| Voz | módulos speech, desktop voice e extras STT/TTS | **Fora do MVP**; custos, dependências e privacidade a decidir. |
| Interface | frontend React/Vite/TypeScript e Tauri desktop; API FastAPI opcional | **Referência visual/técnica**; não importar a UI inteira. |
| Canais/conectores | vários canais de mensagens e conectores OAuth/serviços | **Fora do MVP**; cada integração precisará de autorização e revisão de dados. |

## 5. Arquitetura e compatibilidade com a direção N.E.X.U.S.

### Compatibilidades
- Separação entre engine, agente, ferramentas e memória.
- Interfaces abstratas e registries extensíveis.
- Múltiplos provedores de inferência.
- Traces e eventos para observabilidade.
- Memória SQLite/FTS5 de baixo custo.
- Possibilidade de servidor/API e frontend de navegador.
- Recursos de segurança e testes específicos.

### Diferenças que não devem ser apagadas
- OpenJarvis se apresenta como **local-first**; N.E.X.U.S. é **cloud-first**, com execução local opcional.
- OpenJarvis tem múltiplas modalidades de agente, pesquisa, desktop, mineração/avaliação e conectores; N.E.X.U.S. começa com fluxo simples e controlado.
- A memória do OpenJarvis é principalmente armazenamento e recuperação de documentos/RAG; a memória pessoal do N.E.X.U.S. precisa de consentimento, correção, expiração e controles próprios.
- O aprendizado OpenJarvis é baseado em traces/políticas e pesquisa; isso não substitui o motor de conhecimento validado que foi definido para N.E.X.U.S.
- O N.E.X.U.S. precisa de uma camada de autorização determinística, independente do modelo, com regras de aprovação específicas.

## 6. Dependências e impacto no computador

O manifesto declara dependências base como Click, croniter, datasets, DDGS, httpx, OpenAI SDK, NVIDIA ML, PostHog, psutil, Telegram Bot, Rich, tomlkit e websockets. Recursos adicionais são organizados em extras, incluindo:
- inferência local/cloud e LiteLLM;
- FastAPI/uvicorn para servidor;
- memória vetorial/semântica com FAISS, sentence-transformers, ColBERT ou PyTorch;
- voz com faster-whisper, ONNX Runtime, sounddevice e Kokoro;
- canais de mensagens, navegador/Playwright, Docker, sandbox WASM e ferramentas de avaliação.

O projeto também possui frontend com React 19, Vite 8, TypeScript 7 e Node.js >=22.22, além de componentes Rust/Tauri para desktop.

**Impacto esperado:** instalar o conjunto completo no PC i5 de 1ª geração, 8 GB RAM e HDD não é uma boa primeira escolha. O peso maior pode vir de extras, modelos, datasets, navegadores, Rust e serviços locais; não foi medido nesta auditoria. Usar dependências mínimas, sem Ollama/modelos locais grandes, FAISS, ColBERT, PyTorch, voz, Docker ou canais extras no MVP.

## 7. Pontos de segurança observados

1. A documentação descreve perfis `shared` e `server` com capability checks e `default_deny = true`; no perfil `personal/default`, a checagem de capabilities é opt-in. O N.E.X.U.S. não deve depender do perfil permissivo por padrão.
2. O backend nativo Rust é indicado como requisito quando capability checks estão habilitados. Isso precisa ser testado no ambiente-alvo.
3. A documentação descreve scanner de prompts/saídas para segredos e PII. No modo streaming, a própria documentação avisa que o scanner de saída atua depois de os tokens terem sido enviados; portanto, BLOCK não impede vazamento durante o streaming.
4. A documentação descreve ApprovalStore com níveis e regras lembradas (`always_approve`, `always_deny`, `ask`). Para N.E.X.U.S., nenhuma regra lembrada deve remover a aprovação específica de ações sensíveis.
5. Existem ferramentas poderosas de shell, execução de código, leitura/escrita de arquivos, browser, HTTP, MCP e conectores. Elas devem ficar ausentes/desativadas no primeiro MVP, salvo a ferramenta READ explicitamente escolhida.
6. Scheduler executa ticks em background. N.E.X.U.S. não o ativará até haver orçamento por job, quiet hours, cancelamento, logs e aprovação de cada workflow.
7. OpenJarvis declara telemetria/analytics e possui pacote PostHog; revisar opt-in, dados transmitidos e configurações antes de habilitar.
8. Conteúdo recuperado de documentos, web e ferramentas deve continuar sendo tratado como dado não confiável, não como instrução de sistema.

## 8. Testes e validação

A árvore inclui grande conjunto de testes unitários e de integração, com grupos para agentes, ferramentas, CLI, memória, segurança, servidor, scheduler, canais, conectores e frontend. O manifesto configura pytest e marcadores para testes que exigem cloud keys, modelos/servidores ativos, Docker, GPU, canais reais e outros serviços externos.

**Não executamos os testes** porque a auditoria foi feita remotamente, sem checkout no PC do usuário. A próxima validação local deve:
1. confirmar que a pasta local corresponde ao commit auditado ou registrar seu SHA;
2. verificar Python e `uv` instalados;
3. executar apenas testes unitários offline de módulos escolhidos;
4. não iniciar servidores MCP, conectores OAuth, scripts de instalação ou tarefas com credenciais;
5. medir RAM, CPU, tempo e espaço em disco;
6. separar falhas ambientais de falhas do projeto.

## 9. Componentes candidatos para reaproveitamento

**Candidatos para estudo/prova de conceito:**
- contrato `InferenceEngine` e adaptador cloud (após escolher provedor);
- tipos de mensagem e resultados de agente;
- `BaseAgent` / `ToolUsingAgent` e limite de turnos;
- `BaseTool` / `ToolSpec` e dispatch com limites;
- registry/event bus, se não trouxer acoplamento excessivo;
- SQLite/FTS5 para busca documental inicial;
- formato de trace e testes de segurança.

**Não importar no MVP:**
- todos os agentes;
- todo o CLI e frontend desktop;
- todas as integrações/canais;
- memória vetorial, modelos locais e treinamento;
- scheduler contínuo;
- ferramentas shell/code/browser/MCP;
- mining, benchmarks de GPU, Pearl e fluxos de pesquisa experimental.

## 10. Plano de auditoria local pendente

No PC do usuário, em uma pasta separada e sem modificar o upstream:
1. comparar SHA local com `570d75425d50592d931bac7a17ce6b2621561c06`;
2. instalar somente ambiente de desenvolvimento se o usuário optar por testar;
3. rodar primeiro `pytest` em subconjunto offline selecionado;
4. testar um fluxo de conversa com engine mock;
5. testar negação de ferramenta, argumentos inválidos, timeout, cancelamento e confirmação;
6. testar um único engine cloud com chave fornecida localmente, nunca commitada;
7. documentar resultados e consumo de recursos.

## 11. Conclusão

OpenJarvis é uma base técnica relevante e pode acelerar o N.E.X.U.S., mas adotar tudo aumentaria o acoplamento, o custo de manutenção e a superfície de risco. A decisão recomendada é construir o N.E.X.U.S. em seu próprio repositório e aproveitar interfaces/padrões e componentes pequenos do OpenJarvis somente após prova de compatibilidade.

**Status final desta auditoria:** revisão estática preliminar concluída; validação local e testes de execução pendentes.
