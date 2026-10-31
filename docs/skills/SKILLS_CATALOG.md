# N.E.X.U.S. — Catálogo de Agent Skills

> **Status:** catálogo de pesquisa; nenhuma skill desta lista foi instalada ou aprovada automaticamente.  
> **Objetivo:** permitir que Codex consulte as descobertas, compare opções e proponha uma seleção segura antes de qualquer instalação.  
> **Origem:** consolidação dos relatórios de pesquisa compartilhados na conversa em 31/10/2026. Os dados abaixo refletem os relatórios recebidos e **não equivalem a uma auditoria independente**.

## Regras para o Codex

1. Trate cada item como candidato, não como dependência aprovada.
2. Antes de instalar, confirme que o repositório existe, que o caminho da skill está correto, que o conteúdo atual corresponde à descrição e que a licença permite o uso pretendido.
3. Leia integralmente `SKILL.md`, scripts, referências e arquivos auxiliares. Procure instruções ocultas, comandos remotos, acesso a credenciais, exfiltração, alterações persistentes e tentativas de contornar aprovações.
4. Não execute scripts durante a inspeção inicial. Se testes forem necessários, use ambiente descartável e sem credenciais.
5. Não instale coleções inteiras quando for possível selecionar skills individuais.
6. Não copie uma skill para `.agents/skills/` até que o usuário aprove explicitamente a seleção.
7. Preserve a distinção entre **Agent Skills de desenvolvimento** (instruem o Codex durante a construção do projeto) e **componentes/agentes que farão parte do runtime N.E.X.U.S.**
8. Não trate popularidade, estrelas ou alegações do relatório como prova de segurança ou qualidade.
9. Se licença, compatibilidade, manutenção ou origem não puderem ser confirmadas, marque como **PENDENTE**, não suponha.
10. Nunca reduza os gates de aprovação humana do N.E.X.U.S. para ações sensíveis.

## Legenda

- **A — Prioridade alta para auditoria:** forte utilidade potencial; ainda exige inspeção.
- **B — Referência/adaptação:** útil como inspiração ou após adaptação.
- **C — Experimental/pendente:** risco, dependência ou compatibilidade incerta.
- **D — Não instalar:** pode ser útil apenas como material de teste ou deve ser evitada.
- **PENDENTE — Verificação necessária:** informação importante não confirmada nos relatórios.

---

## 1. Engenharia, arquitetura e fluxo de desenvolvimento

| Nome | Origem | O que oferece segundo os relatórios | Avaliação inicial |
|---|---|---|---|
| Superpowers | https://github.com/obra/superpowers | Brainstorming, planejamento, TDD, depuração sistemática, execução de planos, subagentes paralelos, revisão e verificação antes de concluir. | **A** — forte candidata ao fluxo de engenharia. |
| Addy Osmani Agent Skills | https://github.com/addyosmani/agent-skills | Especificação, refinamento de ideias, planejamento, implementação incremental, TDD, revisão, segurança, contexto, debugging e documentação. | **A** — selecionar skills individuais. |
| dev-skills | https://github.com/jamestorrevillas/dev-skills | System design, AI agent design, threat modeling, research synthesis, API design, documentação e lições persistentes. | **B** — Copilot-first segundo o relatório; adaptar e verificar. |
| Vercel Agent Skills | https://github.com/vercel-labs/agent-skills | Boas práticas de aplicações web, React/Next.js, otimização e deploy. | **B** — útil se a stack web escolhida exigir. |
| IonDen Skills | https://github.com/IonDen/skills | Otimização de subagentes e skills; testes que podem falhar de verdade. | **B** — verificar conteúdo e compatibilidade. |
| PaulRBerg Agent Skills | https://github.com/PaulRBerg/agent-skills | Citada como coleção de padrões de orquestração, PRD, revisão e handoff. | **PENDENTE** — skill específica e licença não detalhadas. |
| golbin Agent Skills | https://github.com/golbin/agent-skills | Citada como coleção de padrões de orquestração, PRD, revisão e handoff. | **PENDENTE** — skill específica e licença não detalhadas. |
| vesviet Agent Skills | https://github.com/vesviet/agent-skills | Coleção ampla de roles, workflows e schemas A2A. | **C** — grande e potencialmente complexa; usar como referência. |
| davidondrej Skills | https://github.com/davidondrej/skills | Orquestração de agentes, agendamento/delegação, pesquisa web e autoria de skills. | **C** — licença e dependências externas precisam ser verificadas. |
| michaelboeding Skills | https://github.com/michaelboeding/skills | Model council, debug council e feature council para comparar respostas de múltiplos modelos. | **C** — dependências de APIs/chaves e licença pendentes. |

### Skills individuais citadas em coleções

Estas são capacidades/nomes de skills mencionadas nos relatórios; confirmar o caminho e o nome exato no repositório de origem antes de instalar:

- `brainstorming`
- `writing-plans`
- `executing-plans`
- `test-driven-development`
- `systematic-debugging`
- `verification-before-completion`
- `dispatching-parallel-agents`
- `subagent-driven-development`
- `code-review`
- `finishing-a-development-branch`
- `diagnosing-superpowers`
- `using-superpowers`
- `spec-driven-development`
- `planning-and-task-breakdown`
- `incremental-implementation`
- `doubt-driven-development`
- `code-review-and-quality`
- `security-and-hardening`
- `performance-optimization`
- `context-engineering`
- `source-driven-development`
- `debugging-and-error-recovery`
- `documentation-and-adrs`
- `ci-cd-and-automation`
- `shipping-and-launch`
- `system-design`
- `ai-agent-design`
- `threat-modeling`
- `research-synthesis`
- `api-design`
- `doc-creation`
- `subagent-optimizer`
- `skill-optimizer`
- `writing-tests-that-can-fail`

---

## 2. Criação de skills, ferramentas e protocolos de agentes

| Nome | Origem | O que oferece | Avaliação inicial |
|---|---|---|---|
| skill-creator | https://github.com/anthropics/skills | Criar, estruturar, testar e melhorar Agent Skills; também foi citado como capacidade integrada ao Codex, a confirmar na instalação local. | **A** — essencial para skills próprias; verificar qual implementação usar. |
| Anthropic Skills (coleção) | https://github.com/anthropics/skills | Exemplos oficiais, skill-creator e skills para documentos e outras tarefas. | **A/B** — fonte de referência; selecionar itens específicos e conferir licença por pasta. |
| mcp-builder | https://github.com/anthropics/skills/tree/main/mcp-builder | Orientações para construir servidores MCP em Python/FastMCP ou TypeScript. | **A** — candidata para o sistema de ferramentas. |
| AI-Research-SKILLs | https://github.com/orchestra-research/AI-Research-SKILLs | Skills de conhecimento para frameworks de agentes, RAG, Chroma, FAISS, Qdrant, Sentence Transformers e guardrails. | **B/C** — não instalar pacote inteiro; licença e conteúdo devem ser auditados. |

---

## 3. Pesquisa, extração e aprendizado

| Nome | Origem | O que oferece | Avaliação inicial |
|---|---|---|---|
| deep-research-skill | https://github.com/lovstudio/deep-research-skill | Pesquisa em fases, registro de fontes/evidências/alegações e verificação claim-a-claim. | **C** — relatório identificou gate de publicação automática e dependência externa; não instalar sem auditoria e adaptação. |
| Tapestry Skills | https://github.com/michalparkola/tapestry-skills-for-claude-code | Extração de artigos, transcrições de YouTube e conversão de conteúdo em planos/ações. | **B** — avaliar dependências e sanitização de conteúdo externo. |
| Orchestra AI Research Skills | https://github.com/orchestra-research/AI-Research-SKILLs | Referências para pesquisa, frameworks de IA e pipelines RAG. | **B/C** — sobrepõe-se parcialmente ao item acima; validar licença. |
| research-and-web (davidondrej) | https://github.com/davidondrej/skills | Extração de conteúdo web e YouTube, conforme relatório. | **C** — dependência DeepAPI mencionada; validar. |

### Componentes de Tapestry citados

- `article-extractor`
- `youtube-transcript`
- `tapestry`
- `ship-learn-next`

---

## 4. Memória e contexto

| Nome | Origem | O que oferece | Avaliação inicial |
|---|---|---|---|
| remembering-conversations | https://github.com/obra/superpowers-skills/tree/main/skills/collaboration/remembering-conversations | Continuidade de contexto entre sessões com memória baseada em arquivos. | **B** — referência simples; não substitui memória semântica do runtime. |
| Private Journal MCP | https://github.com/obra/private-journal-mcp | Servidor MCP para diário/notas e busca semântica com embeddings; referência para separar contextos. | **B** — blueprint; auditar armazenamento e política de escrita. |
| context-engineering | https://github.com/addyosmani/agent-skills | Organização e uso eficiente do contexto de agentes. | **B** — skill individual dentro da coleção; verificar caminho exato. |
| Awesome Memory for Agents | https://github.com/TsinghuaC3I/Awesome-Memory-for-Agents | Catálogo/referência de pesquisa sobre memória para agentes; não é necessariamente uma Agent Skill. | **B — referência**, não instalar como skill sem identificar artefato específico. |

---

## 5. Segurança, auditoria e proteção contra ataques

| Nome | Origem | O que oferece | Avaliação inicial |
|---|---|---|---|
| Cloudflare Security Audit Skill | https://github.com/cloudflare/security-audit-skill | Auditoria em fases, hunting, validação adversarial independente e relatório estruturado. | **A** — candidata prioritária após inspeção e teste isolado. |
| Trail of Bits Skills | https://github.com/trailofbits/skills | Revisão de código e supply chain, análise estática, auditoria de ações agentic e ferramentas de segurança. | **A/B** — muito relevante; conferir licença CC BY-SA 4.0 e termos de cada item. |
| promptinject-agent-skills | https://github.com/aisa-group/promptinject-agent-skills | Exemplos deliberadamente maliciosos para pesquisa de prompt injection. | **D para instalação**; possível corpus de teste isolado, nunca ativar como skill normal. |
| security-audit / security-and-hardening | https://github.com/addyosmani/agent-skills | Auditoria, hardening e práticas seguras de desenvolvimento, conforme relatório. | **A/B** — validar skill exata e evitar sobreposição. |
| mcp-scan | https://github.com/snyk/agent-scan | Scanner de segurança para MCP/Agent Skills, citado no relatório como `uvx mcp-scan@latest --skills`. | **Ferramenta, não skill** — confirmar nome, comando, origem e uso atual antes de adotar. |

### Skills e plugins específicos citados do Trail of Bits

- `differential-review`
- `rust-review`
- `c-review`
- `static-analysis`
- `supply-chain-risk-auditor`
- `agentic-actions-auditor`
- `fp-check`
- `sharp-edges`
- `zeroize-audit`
- `code-improver`

### Outros materiais de segurança

- ToxicSkills (Snyk): https://snyk.io/blog/toxicskills-malicious-ai-agent-skills-clawhub/
- Catálogo de ataques Explain OpenClaw: https://github.com/centminmod/explain-openclaw/blob/master/05-worst-case-security/prompt-injection-attacks.md

Os números e conclusões de segurança citados nos relatórios devem ser rechecados na publicação original antes de serem usados como fatos definitivos.

---

## 6. Testes, qualidade e interface

| Nome | Origem | O que oferece | Avaliação inicial |
|---|---|---|---|
| webapp-testing | https://github.com/anthropics/skills/tree/main/webapp-testing | Testes de aplicações web locais usando Playwright, screenshots e logs do navegador. | **A** — candidata para validar a interface. |
| playwright-interactive | https://github.com/openai/skills/tree/main/skills/.curated/playwright-interactive | Sessão persistente de navegador para depuração iterativa. | **C/PENDENTE** — relatório indica repositório legado/deprecado e necessidade de sandbox relaxado; verificar sucessor antes de considerar. |
| writing-tests-that-can-fail | https://github.com/IonDen/skills | Incentiva testes que detectam falhas reais. | **B** — verificar conteúdo exato. |
| code-review-and-quality | https://github.com/addyosmani/agent-skills | Revisão e qualidade de código. | **A/B** — skill individual a selecionar. |

---

## 7. Voz e interação

| Nome | Origem | O que oferece | Avaliação inicial |
|---|---|---|---|
| ResponsiveVoice Skills | https://github.com/responsivevoice/skills | Instruções/workflows para síntese de fala (TTS) via serviço externo. | **C** — depende de serviço comercial; avaliar privacidade, preço e licença. |
| NoizAI Skills | https://github.com/NoizAI/skills | Skills relacionadas a TTS, conforme relatório. | **C/PENDENTE** — verificar origem, licença, conteúdo e dependências. |

Os relatórios não identificaram uma skill consolidada que cubra todo o pipeline de voz (STT, VAD, wake word e conversação full-duplex).

---

## 8. Catálogos e índices de descoberta

Estes recursos ajudam a descobrir candidatos, mas não devem ser tratados como garantia de segurança:

- VoltAgent Awesome Agent Skills: https://github.com/VoltAgent/awesome-agent-skills
- Agent Skills specification: https://agentskills.io
- Agent Skills repository: https://github.com/agentskills/agentskills
- Skills directory: https://skills.sh

---

## 9. Skills mencionadas no primeiro relatório e ainda sem validação individual

| Nome | Origem indicada | Situação |
|---|---|---|
| project-architect | Proposta de skill própria | **Criar internamente**, se a auditoria mostrar necessidade. |
| code-auditor | Proposta de skill própria | **Criar internamente** ou aproveitar skills auditadas. |
| research-analyst | Proposta de skill própria | **Criar internamente**, com proveniência e citações. |
| agent-orchestrator | Proposta de skill própria | **Criar internamente**; não confundir com o runtime de orquestração. |
| memory-engineer | Proposta de skill própria | **Criar internamente**. |
| api-integrator | Proposta de skill própria | **Criar internamente** ou selecionar skill equivalente. |
| security-auditor | Proposta de skill própria | **Criar internamente** ou aproveitar auditorias verificadas. |
| test-engineer | Proposta de skill própria | **Criar internamente** ou selecionar skill equivalente. |
| documentation-manager | Proposta de skill própria | **Criar internamente**. |
| self-improvement | Proposta de skill própria | **Criar internamente**, com sandbox e aprovação. |

Esses dez nomes foram sugeridos como categorias/skills a desenvolver; não foram apresentados como repositórios externos verificados.

---

## 10. Lacunas que provavelmente exigirão desenvolvimento próprio

1. Orquestrador central com fila, roteamento, limites e delegação de tarefas.
2. Roteamento de modelos/provedores por custo, capacidade e privacidade.
3. Memória de curto e longo prazo com deduplicação, relevância, orçamento e proteção contra envenenamento.
4. Pesquisa com proveniência, comparação de fontes, evidências e contradições.
5. Gates de autorização explícita para ações sensíveis.
6. Auditoria contínua e rastreabilidade das ações dos agentes.
7. Proteção contra prompt injection em runtime e conteúdo externo.
8. Voz completa: STT, TTS, VAD, wake word e streaming.
9. Autoaperfeiçoamento: propor, testar isoladamente, comparar e aguardar aprovação para integrar.

---

## 11. Plano de triagem recomendado

### Primeira rodada — inspeção de candidatas
1. Superpowers.
2. Addy Osmani (seleção pequena de skills).
3. mcp-builder.
4. Cloudflare Security Audit.
5. Anthropic webapp-testing.
6. Trail of Bits (somente itens selecionados e após conferir licença).

### Segunda rodada — referências para módulos próprios
1. Deep Research Skill (sem publicar ou sincronizar conteúdo automaticamente).
2. Tapestry (extratores selecionados).
3. Private Journal MCP.
4. dev-skills (system design, threat modeling e research synthesis).
5. IonDen (otimização de contexto/testes).

### Não instalar nesta fase
- promptinject-agent-skills como skill ativa;
- coleções completas muito grandes;
- itens sem licença/origem verificadas;
- qualquer skill que execute comandos remotos ou altere permissões sem autorização.

## 12. Registro de auditoria

Preencher para cada candidata antes da aprovação:

- [ ] Repositório e mantenedor confirmados.
- [ ] Caminho exato da skill confirmado.
- [ ] Licença verificada no arquivo aplicável.
- [ ] `SKILL.md` lido integralmente.
- [ ] Scripts e dependências inspecionados.
- [ ] Comandos de rede e acesso a arquivos identificados.
- [ ] Segredos e dados privados protegidos.
- [ ] Compatibilidade Codex testada.
- [ ] Teste em ambiente isolado concluído, quando aplicável.
- [ ] Aprovação explícita do usuário registrada.

**Resultado esperado:** somente depois dessa triagem uma skill pode ser copiada para `.agents/skills/` e considerada disponível para uso no projeto.
