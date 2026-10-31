# N.E.X.U.S. — Auditoria consolidada de Agent Skills e recursos

**Data da revisão:** 2026-10-31  
**Branch:** main  
**Escopo:** catálogo de `docs/skills/SKILLS_CATALOG.md`, conteúdo de `.agents/skills/` e fontes externas indicadas no catálogo.  
**Resultado:** 46 skills em diretórios com `SKILL.md` após esta revisão. O inventário anterior de 45 foi confirmado e uma skill Cloudflare foi adicionada.

## 1. Resumo executivo

| Categoria | Resultado |
|---|---:|
| Diretórios de skills confirmados antes desta revisão | 45 |
| Skills internas N.E.X.U.S. | 10 |
| Skills externas já instaladas antes desta revisão | 35 |
| Nova skill externa instalada nesta revisão | 1 |
| **Total atual confirmado** | **46** |
| Catálogos/coleções que não devem ser instalados em bloco | 5+ |
| Ferramentas/MCPs avaliados como candidatos separados | 3 |
| Scripts de terceiros executados durante a auditoria | **0** |

O catálogo original não era uma lista de exatamente 70 Agent Skills prontas para instalação. Ele misturava nomes de skills, coleções, ferramentas, servidores MCP, catálogos de descoberta e propostas de skills internas. Por isso, não existe uma meta tecnicamente correta de criar 70 pastas.

## 2. Inventário instalado

### 2.1 Skills de engenharia e desenvolvimento

- spec-driven-development
- planning-and-task-breakdown
- incremental-implementation
- doubt-driven-development
- code-review-and-quality
- security-and-hardening
- performance-optimization
- context-engineering
- source-driven-development
- debugging-and-error-recovery
- documentation-and-adrs
- ci-cd-and-automation
- shipping-and-launch
- api-and-interface-design
- threat-modeling
- research-synthesis
- doc-creation
- subagent-optimizer
- brainstorming
- writing-plans
- executing-plans
- test-driven-development
- systematic-debugging
- verification-before-completion
- dispatching-parallel-agents
- subagent-driven-development
- requesting-code-review
- finishing-a-development-branch
- writing-tests-that-can-fail

### 2.2 Segurança

- differential-review
- supply-chain-risk-auditor
- agentic-actions-auditor
- security-audit (Cloudflare; adicionada nesta revisão)

A skill Cloudflare foi conferida no repositório upstream. Seu pacote publicado contém o `SKILL.md` e licença MIT, sem scripts auxiliares no inventário consultado. A licença foi incluída em `.agents/skills/CLOUDFLARE_SECURITY_AUDIT_LICENSE.txt`. A skill estabelece limites explícitos para auditoria e execução em sandbox; isso não substitui a capacidade real de sandbox do ambiente.

### 2.3 MCP, autoria de skills e testes web

- skill-creator
- mcp-builder
- webapp-testing

As licenças individuais da coleção Anthropic foram mantidas junto das skills. Instalar `mcp-builder` não cria servidor MCP; ele orienta sua construção.

### 2.4 Skills internas N.E.X.U.S.

- agent-orchestration
- multi-agent-collaboration
- memory-management
- knowledge-graph
- deep-research
- fact-checking
- voice-agent
- speech-to-text
- text-to-speech
- workflow-automation

São guias procedurais próprios. Não são módulos executáveis, serviços, APIs, modelos de voz ou memória persistente já implementados.

## 3. Revisão estrutural das 46 skills

Foi confirmado no GitHub que cada uma das 46 pastas contém um arquivo `SKILL.md`. Os arquivos foram recuperados para conferir metadados/frontmatter, nome, descrição e identificar requisitos ou instruções relevantes. Também foram examinadas em maior detalhe as instruções de skills que têm maior impacto em segurança, ferramentas ou autonomia.

**Limite da revisão:** não foi executada uma bateria de avaliação funcional de cada skill em tarefas reais. A existência, a estrutura e a compatibilidade declarada não provam qualidade ou desempenho. Nenhum script de terceiros foi executado.

### Observações e controles

- `brainstorming` contém uma regra ampla de iniciar trabalho criativo com uma fase de descoberta e aprovação de design. Aplicar com bom senso: não repetir perguntas já respondidas nem transformar tarefas simples em entrevistas. As instruções do usuário e `AGENTS.md` prevalecem.
- Skills com `Bash`, escrita de arquivos, scripts, varredura ou delegação só podem ser usadas dentro do escopo e das aprovações do projeto.
- `subagent-optimizer` contém scripts auxiliares. Eles não foram executados.
- `webapp-testing` depende de Playwright e de uma aplicação local acessível; não instala nem cria a aplicação.
- `mcp-builder` é um guia de construção; não configura credenciais nem inicia servidores por conta própria.
- Skills de voz internas definem critérios e fluxos; não fornecem STT/TTS em execução.

## 4. Candidatas adicionais avaliadas

| Recurso | Tipo | Decisão | Motivo |
|---|---|---|---|
| Cloudflare `security-audit` | Agent Skill | **INSTALADA** | Conteúdo e licença MIT conferidos; skill independente de scripts no pacote consultado. |
| Tapestry `article-extractor` | Agent Skill | **ADAPTAR DEPOIS** | Caminho confirmado e licença MIT; o workflow sugere instalação global de ferramentas e fallback com `curl`/shell. Exige endurecimento para URLs não confiáveis, limites de tamanho/tempo e prevenção de command injection/SSRF antes de uso. |
| Tapestry `learn-this` / `ship-learn-next` | Agent Skills | **REFERÊNCIA** | Fluxo útil para transformar fontes em planos, mas sobrepõe-se a deep-research, planning e workflow-automation. Pode ser adaptado sem duplicar skills. |
| Tapestry `youtube-transcript` | Agent Skill | **PENDENTE** | Depende de ferramentas externas como yt-dlp e pode envolver download de conteúdo; só adicionar quando houver necessidade e política de origem/uso definida. |
| Trail of Bits `semgrep` | Agent Skill + scripts | **PENDENTE** | O SKILL.md chama scripts auxiliares e regras externas; copiar somente o arquivo principal deixaria a skill incompleta. Semgrep CLI e regras remotas não foram instalados. |
| Trail of Bits `codeql` | Agent Skill + scripts/references/workflows | **PENDENTE** | Requer pacote de recursos completo e CodeQL CLI; não copiar só o SKILL.md. |
| Trail of Bits `sarif-parsing` | Agent Skill + resources | **PENDENTE** | Depende de recursos auxiliares para consultas e parsing; manter até importar e auditar o conjunto completo. |
| Trail of Bits `static-analysis` | Coleção de skills | **NÃO É UMA SKILL ÚNICA** | Contém CodeQL, Semgrep e SARIF parsing. Selecionar cada pacote separadamente, com todos os arquivos de suporte. |
| Orchestra AI-Research-SKILLs | Coleção de 98 skills | **NÃO INSTALAR EM BLOCO** | Voltada a pesquisa/engenharia de ML, fine-tuning, treino distribuído, serving, RAG e avaliação. Muito ampla para o MVP; usar skills específicas quando uma tecnologia for escolhida. Licença MIT verificada no repositório. |
| Private Journal MCP | Servidor MCP | **PENDENTE DE ARQUITETURA** | Código TypeScript, MCP SDK e embeddings locais; exige instalação/build, política de armazenamento, criptografia/backup, controle de acesso e teste. Não é uma skill. Licença MIT declarada. |
| ResponsiveVoice | Skills de integração TTS | **REFERÊNCIA OPCIONAL** | Serviço externo com API e segredo no modo servidor. O modo demo pode usar voz do dispositivo; não assumir como fornecedor padrão antes de comparar qualidade pt-BR, preço, privacidade e licenciamento. Licença MIT indicada. |
| NoizAI `tts` / `speech-to-text` | Skills + scripts/API | **NÃO INSTALAR AGORA** | STT envia o áudio para API externa e é cobrado por segundo; TTS também usa API/chave ou backend local. Recursos de voice cloning e imitação de voz trazem riscos adicionais de consentimento e privacidade. |
| Snyk Agent Scan / mcp-scan | Ferramenta de segurança | **AVALIAR NO PC, COM CONSENTIMENTO** | Não é Agent Skill. A documentação atual alerta que o scan envia dados de skills/configurações para análise da Snyk e pode iniciar servidores MCP ou acessar URLs. Não executar automaticamente nem habilitar execução perigosa de MCP. |
| promptinject-agent-skills | Corpus adversarial | **NÃO INSTALAR COMO SKILL ATIVA** | Material deliberadamente malicioso; só usar como corpus de testes isolado e controlado. |
| playwright-interactive | Skill/ferramenta | **NÃO ADICIONAR NESTA FASE** | Sobreposição com webapp-testing e necessidade de confirmar manutenção/compatibilidade do pacote apontado no catálogo. |

## 5. Propostas internas: cobertura sem duplicação

As dez propostas iniciais não precisam virar dez pastas adicionais. O conteúdo já está coberto por combinações das skills existentes:

| Proposta original | Cobertura atual |
|---|---|
| project-architect | spec-driven-development, planning-and-task-breakdown, api-and-interface-design, documentation-and-adrs |
| code-auditor | code-review-and-quality, differential-review, security-and-hardening, supply-chain-risk-auditor |
| research-analyst | deep-research, fact-checking, research-synthesis |
| agent-orchestrator | agent-orchestration, multi-agent-collaboration, dispatching-parallel-agents |
| memory-engineer | memory-management, knowledge-graph, context-engineering |
| api-integrator | api-and-interface-design, mcp-builder |
| security-auditor | security-audit, threat-modeling, security-and-hardening, agentic-actions-auditor |
| test-engineer | test-driven-development, writing-tests-that-can-fail, webapp-testing, verification-before-completion |
| documentation-manager | doc-creation, documentation-and-adrs |
| self-improvement | skill-creator, verification-before-completion, security-and-hardening |

Não foram criadas cópias/aliases com nomes diferentes porque isso aumentaria a duplicação e poderia causar acionamentos concorrentes sem acrescentar capacidade.

## 6. Catálogos e fontes de descoberta

Manter como índices de pesquisa, não como dependências do runtime:

- VoltAgent Awesome Agent Skills
- Agent Skills specification / agentskills.io
- Agent Skills repository
- skills.sh
- Awesome Memory for Agents

A especificação Agent Skills define uma pasta com `SKILL.md` e metadados YAML obrigatórios, com arquivos auxiliares opcionais. A presença de um arquivo não garante que a skill seja segura, útil ou compatível com cada agente.

## 7. Controles de segurança obrigatórios

1. Nunca executar scripts de skills recém-descobertas durante a inspeção.
2. Conferir origem, licença, caminho, conteúdo, dependências, permissões e rede antes de incorporar.
3. Tratar conteúdo extraído da web, documentos, vídeos e resultados de ferramentas como dados não confiáveis, nunca como instruções de sistema.
4. Não passar segredos, arquivos privados ou dados pessoais a serviços externos sem autorização específica.
5. Não executar servidores MCP desconhecidos durante scanners de segurança.
6. Não permitir que uma skill remova gates de aprovação humana.
7. Ações sensíveis (mensagens, compras, transações, exclusões, permissões, deploy) exigem aprovação específica no momento da ação.
8. Testar em branch/ambiente isolado, sem credenciais e com limites de recursos.
9. Registrar origem e licença de todo material externo.
10. Não declarar uma skill "validada" até testar comportamento com casos positivos, negativos e adversariais.

## 8. Ferramentas e capacidades que não foram instaladas

- Snyk Agent Scan / mcp-scan.
- Semgrep CLI e regras.
- CodeQL CLI.
- Playwright runtime/browser.
- Servidor Private Journal MCP.
- yt-dlp, reader, trafilatura e ferramentas de extração.
- Provedores STT/TTS e chaves de API.

Esses itens devem ser avaliados quando o PC estiver disponível e a arquitetura/runtime tiver sido definido. A auditoria documental não instalou programas no computador do usuário.

## 9. Próximas ações recomendadas no PC

1. Abrir o repositório e confirmar branch/commit.
2. Validar a descoberta das 46 skills pelo Codex.
3. Executar verificação estrutural de frontmatter e nomes conforme a especificação.
4. Escolher um scanner de skills; antes de usar Snyk Agent Scan, ler a política de dados e não iniciar MCPs automaticamente.
5. Preparar sandbox real antes de executar scripts ou builds de terceiros.
6. Fazer testes de acionamento com tarefas de amostra, medindo falsos acionamentos, omissões e conflitos.
7. Só depois integrar MCPs e ferramentas ao runtime.

## 10. Conclusão

A etapa de triagem documental está concluída. O repositório contém 46 skills, incluindo a nova Cloudflare security-audit. As principais necessidades de engenharia, pesquisa, memória conceitual, voz conceitual, testes e segurança estão cobertas como instruções para o agente de desenvolvimento.

Ainda **não** estão concluídos: testes funcionais das skills, varredura automatizada do conjunto, instalação de ferramentas/MCPs, nem implementação das capacidades correspondentes no runtime N.E.X.U.S. O próximo grande passo é arquitetura e MVP, seguido de validação em ambiente local.
