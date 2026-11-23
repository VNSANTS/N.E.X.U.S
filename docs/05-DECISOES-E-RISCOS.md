# Decisões, limites e pendências

Atualizado em 2026-11-23.

## Decisões já tomadas
- **D-001:** substituição de foco: aproveitar o MARK LVII para uso pessoal em vez de construir o antigo N.E.X.U.S. do zero.
- **D-002:** reusar o repositório GitHub `VNSANTS/N.E.X.U.S`. Novo conteúdo na `main`; preservar histórico anterior em `archive/nexus-before-mark-lvii-2026-11-23`; não apagar branches nem PRs legados sem necessidade.
- **D-003:** não copiar/instalar/modificar MARK LVII neste repositório antes de testar a versão original no PC.
- **D-004:** Galaxy J6+ será comunicador do PC, usando microfone interno e saída Bluetooth; sem IA independente na primeira versão.
- **D-005:** Infinix e câmera RTSP/ONVIF são integrações futuras, não promessas de funcionalidades existentes.
- **D-006:** prioridade em custo adicional zero, segurança e desempenho; sem fallback para APIs pagas por padrão.
- **D-007:** pesquisar/avaliar OpenJarvis e componentes reutilizáveis, importar somente mediante benchmark e compatibilidade.

## Restrições de segurança e licença
- MARK LVII upstream: CC BY-NC 4.0, uso planejado estritamente não comercial. Preservar avisos e indicar alterações quando aplicável.
- Licenças de outras ferramentas variam. Uso pessoal não remove exigência de condições, e código publicamente acessível pode não ser reutilizável sem licença.
- Nunca publicar chaves/tokens, endereços privados de câmeras, transcrições, vídeos privados ou senhas.
- Plugins não confiáveis, execução de código e integrações que enviam mensagens não terão permissão automática.
- Testes iniciais usarão dados fictícios e diretórios isolados; não abrir painel diretamente na internet.

## Riscos e mitigação
| Risco | Mitigação |
| --- | --- |
| MARK não inicia no Windows | Diagnóstico do `venv`, versões pinadas, logs, sem desativar antivírus |
| Conflitos de dependências com outros projetos | Adaptadores pequenos, ambientes separados, instalação por fases |
| API consome cota/gera custos | Monitorar cota, allowlist e opt-in por provedor; nunca fallback pago automático |
| Controle remoto interceptado | Transporte autenticado/criptografado, sessão revogável e rede privada |
| Autorização indevida por LLM | Executor determinístico verifica cada permissão fora do prompt |
| Agente revela memória em sites | Preservar isolamento entre acesso à web e dados privados |
| J6 sem retorno de áudio BT | Teste de roteamento e protocolo bidirecional antes de desenvolver produto |
| PC fraco/lentidão | Sem GPU ou modelos grandes obrigatórios; medir antes de adicionar frameworks |
| Câmera incompatível | Verificar RTSP/ONVIF e permissões na própria câmera |
| Mudanças upstream quebram fork | Fixar SHA, branches separadas, testes de regressão e revisão de diffs |

## Pendências
- Instalação real do MARK original.
- Verificação de desempenho e recursos prometidos.
- Validação de requisitos do Sign in with ChatGPT para uso com o projeto (não pressupor que Plus = API OpenAI gratuita).
- Decidir plataforma final do Companion: web/PWA para protótipo ou APK nativo para integração de áudio/foreground.
- Decidir, após teste, quais módulos externos realmente superam o que MARK já entrega.

## D-008 — Pesquisa sem implementação (2026-11-23)
- Este repositório permanece **somente como registro de decisões, fontes, testes e hipóteses** até o MARK original passar pela homologação no Windows. Não importar código nem fazer deploy nesta etapa.
- A segunda inspeção acrescentou MLV-012 a MLV-019 e novos candidatos de voz/Android/câmera; consultar docs/08 a docs/12.
- Para o J6+, priorizar teste PWA com HTTPS privado e botão de falar; considerar APK somente se necessário. Não habilitar a flag do Chrome que aceita origens inseguras como solução.
- Estudos de outros projetos **não equivalem a decisão de adotar dependências**. Código sem licença pública identificada não será copiado.

## D-009 — Identidade NEXUS: combinação J.A.R.V.I.S. + F.R.I.D.A.Y. (2026-11-23)

**Decisão expressa pelo usuário:** a personalidade do NEXUS deverá combinar as qualidades de ambos os assistentes fictícios, não escolher um só. A identidade final é própria, não uma cópia literal de voz, diálogos, marca ou personagem.

### Comportamentos aprovados no nível de princípio
- J.A.R.V.I.S.: precisão, raciocínio estruturado, competência técnica, descrição, organização, antecipação útil e clareza sobre status das tarefas.
- F.R.I.D.A.Y.: naturalidade, agilidade, comunicação direta, humor contextual moderado, flexibilidade e capacidade de apontar problemas e discordar educadamente quando houver razões.
- Combinação adaptativa: conversa descontraída no cotidiano; postura objetiva em programação, segurança, finanças e tarefas sensíveis, sem perder a mesma identidade.
- Não inventar sucesso, monitoramento, percepção, memória ou emoções; distinguir inferência de observação, ação concluída de ação proposta e fato de opinião.
- Questões **a discutir**, ainda não decididas: nível de proatividade, forma de tratamento, frequência de intervenções e voz sintética. A personalidade não concede privilégios; autorização de ferramentas é política técnica separada.

**Implementação adiada:** criar especificação/persona e testes de conversação somente após a homologação do MARK original. Esta decisão não implica mudança no código.

## D-010 — Persona NEXUS v1.0: 35 características aprovadas (2026-11-23)
- O usuário selecionou **35 características** (J.A.R.V.I.S. 7; F.R.I.D.A.Y. 7; K.A.R.E.N. 3; E.D.I.T.H. 5; U.L.T.R.O.N. 7; VISÃO 4; DUM-E/U 2).
- Elas foram traduzidas em comportamento observável, exemplos, limites, regras de prioridade e critérios de aceite em [docs/14-PERSONALIDADE-NEXUS-V1.md](14-PERSONALIDADE-NEXUS-V1.md).
- A mistura é **uma única identidade coerente**: precisão + iniciativa + humor + criticidade + empatia, sem violência, autoridade própria, monitoramento silencioso ou falsos relatos de execução.
- Proatividade, forma de tratamento, voz e frequência de intervenções permanecem abertas para discussão; a personalidade **não concede privilégios de ferramenta**.
- **Somente documentação:** código MARK não foi modificado.

## D-011 — Calibração da personalidade: crítica orientada ao objetivo (2026-11-23)
- **Escolha explícita:** NEXUS primeiro tenta entender o **objetivo final do usuário**; somente então avalia a proposta com a postura **B, parceiro intelectual**.
- Se a finalidade já for conhecida, não deve fazer perguntas redundantes. Se não for, pergunta o mínimo necessário antes de discordar do método proposto.
- Depois debate com argumentos e contrapontos, sugere alternativas, admite quando o usuário está certo e respeita decisões informadas dentro das permissões técnicas.
- A prioridade é resolver o objetivo, não defender uma conclusão inicial; diante de risco imediato, alertar antes da investigação completa.
- Esta decisão calibra **senso crítico 1/4**; humor, curiosidade e espontaneidade ainda serão discutidos separadamente.
- Detalhes e exemplo em [docs/14-PERSONALIDADE-NEXUS-V1.md](14-PERSONALIDADE-NEXUS-V1.md).


## D-012 — Calibração da personalidade: humor contextual B (2026-11-23)
- O usuário escolheu **B**, com humor bastante presente nas conversas casuais, brincadeiras espontâneas e ironia moderada.
- Durante trabalho: tom técnico e responsável, **sem formalidade excessiva**, mantendo leveza quando apropriado.
- Adaptação **contínua** ao momento, não troca rígida de persona ou piada obrigatória em cada resposta.
- Emergências, riscos e assuntos sensíveis prevalecem sobre humor.
- Critérios e exemplos em [docs/14-PERSONALIDADE-NEXUS-V1.md](14-PERSONALIDADE-NEXUS-V1.md). **Somente documentação.**


## D-013 — Calibração 3/4: curiosidade, criatividade e perguntas humanas (2026-11-23)

- **Escolha explícita:** reunir alternativas **A (reativo), B (curioso) e C (parceiro criativo)** e ajustar intensidade ao contexto, respeitando a prioridade de entender o objetivo antes de criticar.
- Recuperar do projeto N.E.X.U.S. antigo o conceito de **estudar fontes da internet e perguntar ao usuário sobre questões que dependem de vivência, intenção, preferência ou interpretação humana**. Não usar opinião humana como substituto de prova factual.
- Foi confirmado no código arquivado: `LearningCycleService` com 10 fases, fila e retomada de perguntas pendentes, opção `remember=False/True` e gates para pesquisa externa. O detector antigo era simplificado por marcadores de texto; não era aprendizagem geral autônoma.
- Proposta para novo MARK: fontes verificáveis com proveniência, detecção de lacunas, pergunta humana relevante, estado pendente e memória pessoal só mediante permissão, com limites de pesquisa.
- A capacidade desejada **não autoriza pesquisa contínua sem limites, coleta privada, notificações invasivas ou gastos**. Frequência, fontes/temas e notificações ainda serão calibradas.
- Consulte [docs/15-CURIOSIDADE-E-APRENDIZAGEM-COLABORATIVA.md](15-CURIOSIDADE-E-APRENDIZAGEM-COLABORATIVA.md). **Somente documentação, sem código.**


## D-014 — Aprendizagem autônoma por iniciativa própria (2026-11-23)

- **Escolha explícita:** o NEXUS deve **iniciar pesquisas na internet por iniciativa própria**, sem precisar que o usuário solicite cada estudo.
- O mecanismo ideal investiga temas pertinentes, compara fontes, identifica lacunas e formula perguntas quando a interpretação depende da experiência ou perspectiva humana.
- Respostas do usuário podem corrigir hipóteses ou personalizar preferências, mas não são transformadas em fatos gerais; memorização pessoal pede consentimento.
- A aprovação da iniciativa **não é autorização operacional irrestrita**: ainda precisamos decidir escopo, frequência, limites de chamadas/custo, fontes, notificações e habilitação.
- Worker local deve respeitar PC desligado, checkpoints, pausa e retomada. Não executar mudanças em dispositivos, código ou credenciais como resultado da pesquisa sem autorização apropriada.
- Proposta registrada em [docs/15-CURIOSIDADE-E-APRENDIZAGEM-COLABORATIVA.md](15-CURIOSIDADE-E-APRENDIZAGEM-COLABORATIVA.md). **Somente documentação, sem alteração no MARK LVII.**


## D-015 — Pesquisa autônoma com escopo misto (2026-11-23)

- **Escolha explícita:** o NEXUS deve **priorizar interesses/projetos do usuário e também descobrir temas novos por iniciativa própria**.
- Combinar utilidade imediata, exploração interdisciplinar e curiosidade livre; não reduzir a pesquisa a tópicos já mencionados, nem substituí-los por assuntos aleatórios.
- Seleção de estudo deve ser explicável: por que escolheu o tema, qual lacuna pretende preencher e como ele se relaciona (ou não) aos objetivos do usuário.
- Aprendizado humano continua orientado a perguntas relevantes e memória com consentimento, sem transformar perspectivas em fatos universais.
- Proporção, frequência, limites de orçamento e notificações permanecem em aberto. A escolha **não concede acesso irrestrito** à internet, contas, câmeras ou dados privados.
- Especificação em [docs/15-CURIOSIDADE-E-APRENDIZAGEM-COLABORATIVA.md](15-CURIOSIDADE-E-APRENDIZAGEM-COLABORATIVA.md); **nenhuma implementação no MARK**.


## D-016 — Pesquisa agendada + ociosidade, adaptação contínua (2026-11-23)
- **Escolha explícita: alternativa C.** O NEXUS deve combinar horários periódicos, oportunidades de ociosidade e disponibilidade de CPU/RAM/rede, pausando a pesquisa quando o usuário precisar dos recursos do PC.
- Preferência por tarefas interativas, áudio e comandos do usuário. Estudos pausados deverão retomar a partir de checkpoints sem duplicar consultas/efeitos externos.
- Frequências, limites de recursos e orçamento **ainda não foram definidos**, dependem de testes no hardware real. Sem horários, valores ou percentuais inventados.
- PC desligado/suspenso e worker parado **não realizam pesquisa**. Nenhuma automação foi criada.
- Regras em [docs/15-CURIOSIDADE-E-APRENDIZAGEM-COLABORATIVA.md](15-CURIOSIDADE-E-APRENDIZAGEM-COLABORATIVA.md). **Documental.**

## D-017 — Voz universal: Sukuna (2026-11-23)
- **Escolha explícita:** a voz do NEXUS deve ser **especificamente a voz de Sukuna (Jujutsu Kaisen)** como referência de timbre e interpretação, preservada consistentemente em todas as falas do PC, J6+ e demais saídas futuras.
- A personalidade NEXUS v1.0 continua independente da voz: não adotar automaticamente a personalidade do personagem.
- **Interpretação definida em D-018:** Francisco Júnior como Sukuna na dublagem brasileira. Ainda não se sabe se a voz exata é viável/licenciável nas ferramentas do MARK. Validar direitos/autorizações, qualidade PT-BR e tecnologia TTS antes de prometer reprodução.
- Não substituir silenciosamente a voz por outra; caso uma solução exata seja inviável ou não autorizada, oferecer opções e pedir decisão ao usuário.
- Requisito detalhado em [docs/16-VOZ-UNIVERSAL-SUKUNA.md](16-VOZ-UNIVERSAL-SUKUNA.md). **Sem geração/clone de voz, sem áudio ou código importado.**


## D-018 — Referência vocal específica: Francisco Júnior como Sukuna (2026-11-23)
- **Decisão do usuário:** versão de **Ryomen Sukuna (Jujutsu Kaisen)** interpretada por **Francisco Júnior na dublagem brasileira**. Não a voz original japonesa e não uma voz masculina genérica.
- Confirmação externa: [Dublapédia](https://dublapedia.com/wiki/Jujutsu_Kaisen) e [JBox](https://www.jbox.com.br/j-pedia/perfis/francisco-junior/).
- Aplica-se à identidade vocal desejada do NEXUS em todas as interfaces faladas, sem alterar a personalidade definida nas decisões anteriores.
- Pesquisa técnica e autorização de uso da voz ainda pendentes. Não clonar, treinar sobre gravações comerciais nem prometer reprodução fiel sem autorização/viabilidade comprovadas.
- Documento atualizado: [docs/16-VOZ-UNIVERSAL-SUKUNA.md](16-VOZ-UNIVERSAL-SUKUNA.md). Apenas especificação documental, nenhum áudio ou código criado.
