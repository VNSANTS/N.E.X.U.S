# NEXUS MARK LVII — Percepção sob demanda, emergências e conselho de agentes

**Data:** 2026-11-23  
**Status:** proposta de requisitos decorrente de escolhas explícitas do proprietário, **sem implementação**.  
**Relação:** D-025 (comunicação contextual), D-026 (voz em risco crítico), D-027 a D-030 (detalhamento deste documento).

## Decisões aprovadas pelo proprietário

1. **Alternativa B — percepção inteligente:** usar sinais leves do PC e consultar tela/câmera **apenas quando necessário para compreender melhor o contexto**, dentro de permissões específicas.
2. **Alerta de emergência que pode interromper a tela:** dependendo do risco, o proprietário gostaria de "congelar a tela". O requisito funcional é **captar atenção e obter resposta rapidamente**, não necessariamente suspender processos. Estudar uma sobreposição temporária e fechável que possa ter foco em eventos críticos. Não suspender processos/threads à força nem bloquear acesso ao SO por default.
3. **Chamado por áudio com alcance:** quando o usuário estiver longe do PC, mas em casa, o NEXUS deve tentar alcançá-lo com fala e, se viável, elevar gradualmente o volume dentro de um teto configurável.
4. **Despertar de noite quando necessário:** se houver **evento crítico confirmado**, mesmo durante descanso, tentar chamar por voz até obter resposta ou esgotar uma política curta de tentativas; não garantir despertar. Perguntar a decisão relevante, aceitar comando de voz quando habilitado e autenticar instruções consequenciais.
5. **Agentes debatendo decisões na maioria das vezes:** o sistema deve usar agentes especializados para examinar problemas, levantar opções, discordar, avaliar evidências e apresentar uma melhor resposta. Sempre que permitido por política de ações, idealmente resolver automaticamente o que não exige usuário; consultas de alto impacto deverão ir ao proprietário. **A fronteira exata da autonomia de execução ainda não foi escolhida**, e "agentes concordaram" não constitui autorização.
6. **Baixo custo e hardware modesto:** não exigir sete modelos pesados simultâneos. Orquestrar análise em poucas rodadas e usar papéis especializados sequencialmente ou com provedores já autorizados, obedecendo limites de chamadas, tokens e RAM.

## A. Percepção e presença sem vigilância constante

O NEXUS decide se o usuário está disponível usando sinais primeiro: aplicativo foreground, fullscreen, interação recente, DND, horário e presença de dispositivo local *quando autorizado*. Se não bastar, consultar screenshot/frames de câmera com autorização específica, capturando o mínimo necessário. Não deduzir conclusivamente que está dormindo ou em casa apenas por tela desligada ou um telefone conectado. Acesso visual deve ter indicador, pausa, revogação, isolamento de dados, retenção mínima e sem envio externo oculto.

**Exemplos:** 
- Jogo em tela cheia com interação: ocupado, eventos comuns só notificação.
- Área de trabalho sem atividade por período suficiente e contexto permissivo: pode oferecer fala.
- Estado incerto ou câmera indisponível: não pressupor disponibilidade e, salvo crítico confirmado, apenas notificação.
- Notificação crítica não necessita câmera para existir; prova do risco deve vir de ferramenta/fonte confiável.

## B. "Congelar tela" como requisito de captura de atenção

**Intenção explícita do usuário:** dependendo do risco, pode "congelar a tela" para que a situação seja notada.

### Caminho técnico preferível, a validar
- Em risco crítico confirmado, lançar alerta visual de **alta prioridade, temporário, legível e com botões** "Entendi", "Mostrar detalhes", "Responder por voz" e "Dispensar/Continuar", conforme gravidade.
- Verificar overlay/topmost/fullscreen apenas onde o sistema permitir. Não garantir sobreposição a jogos com exclusive fullscreen, desktop seguro, tela bloqueada ou apps protegidos.
- **Não suspender processos/threads, congelar a sessão Windows, travar teclado/mouse, impedir Alt+Tab ou prejudicar operações críticas.** Interromper inputs ou congelar software pode corromper dados ou impedir que o usuário resolva a emergência.
- Alerta deve possuir timeout/fallback, botão de saída, escape manual e log; se overlay falhar, usar notificação convencional e voz.
- Se o aplicativo controlado expuser **pausa cooperativa e segura**, pode propor uma integração específica, nunca presumir que todo jogo/processo suporta pausas.

### Evidência técnica preliminar
- Windows admite notificações de aplicativos e janelas topmost, mas foco pode depender de permissões e contexto: 
  - https://learn.microsoft.com/en-us/windows/apps/develop/notifications/app-notifications/toast-notifications-overview
  - https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setwindowpos
- Microsoft desencoraja usar `SuspendThread` como mecanismo de sincronização, pois não controla o ponto de suspensão: 
  - https://learn.microsoft.com/en-us/windows/win32/procthread/suspending-thread-execution

## C. Escalonamento de áudio, presença em casa e despertar

**Objetivo de produto:** fazer a mensagem chegar a uma pessoa presente e autorizada, não reproduzir volume máximo indiscriminadamente.

- Detectar canal disponível (alto-falantes do PC, saída Bluetooth, J6+ autorizado), estado da sessão e contexto relevante. Presença no lar pode ser inferida por fontes opcionais aprovadas e precisa incluir categoria **incerto**, sem rastreamento privado presumido.
- Ao notar afastamento provável do PC durante evento crítico, selecionar saída que tenha chance real de ser ouvida, considerando se o áudio pode estar indo a um fone que o usuário não está usando.
- Pode aumentar **gradualmente** o volume específico do aviso ou saída **até limite seguro configurado**; evitar alterar volume mestre sem necessidade. Registrar volume anterior e restaurar quando possível; modo noturno com limites explícitos.
- Não elevar indefinidamente, não reproduzir picos inesperados, não assumir que alto volume é seguro para fones, pessoas dormindo, crianças ou animais na casa.
- Se sono foi deduzido, tratar como **hipótese**. Só evento crítico confirmado habilita tentativa de despertar e com política de repetição limitada e cancelamento. Sem garantia de efetiva audição/resposta.
- Se PC estiver suspenso/desligado ou Companion sem serviço, sistema local não está disponível para alertar; não apresentar falsas promessas de monitoramento independente.
- Se receber resposta por voz ("Não reinicie; apenas isole a conexão"), repetir a instrução detectada e pedir confirmação autenticada quando houver efeito externo relevante. STT pode ouvir incorretamente; autenticação de voz não é confiável apenas por parecer a voz do usuário.
- Para riscos técnicos importantes não críticos, conservar preferência D-025: se ocupado, só notificação, sem tentativa de acordar.

**Fonte técnica para avaliação futura:** APIs de volume por sessão/endpoint do Windows: 
- https://learn.microsoft.com/en-us/windows/win32/coreaudio/volume-controls
- https://learn.microsoft.com/en-us/windows/win32/coreaudio/endpointvolume-api

## D. Conselho de agentes: deliberação antes de agir

### Intenção e escopo
O proprietário quer que **a maioria das situações seja examinada e respondida pelo próprio conjunto de agentes**, com debate interno e mínima necessidade de consultá-lo. Isso amplia o planejamento anterior sem autorizar ações arbitrárias.

### Papéis mínimos propostos (papéis lógicos, não necessariamente modelos paralelos)
1. **Investigador:** coleta sinais e evidências reais, diferencia observação/hipótese.
2. **Estrategista:** propõe 2–3 respostas viáveis conforme objetivo do proprietário.
3. **Crítico/revisor:** tenta refutar hipóteses e identifica efeitos colaterais, lacunas e falhas de segurança.
4. **Coordenador/decisor:** sintetiza decisão, risco, certeza, urgência e próximo passo; pede autorização quando necessário.
5. **Executor (somente via política):** aplica comandos autorizados com limites e verifica resultados. Não existe "permissão porque o conselho votou".

### Exemplo, risco de falha de backup
1. Monitor autorizado informa falha de backup com log e timestamp.
2. Investigador confirma se o destino está inacessível ou se houve interrupção transitória.
3. Estrategista propõe retentativa segura, mudança de horário ou intervenção humana.
4. Revisor verifica se retentativa poderia sobrescrever dados, duplicar custos ou bloquear aplicação.
5. Coordenador seleciona recomendação; executor só retenta caso ação idempotente/reversível tenha autorização de política. Caso contrário, notifica e pergunta.
6. NEXUS informa **o que foi detectado, debatido, executado ou não, e qual resultado foi comprovado**, sem fabricar consenso.

### Limites e desempenho
- Debate deve ser **orientado por relevância**: problema simples pode usar apenas um agente; problemas médios até 2–3 papéis; emergências curto-circuitam debate extenso para alertar primeiro e deliberar em paralelo/com tempo limitado após notificação.
- Registrar argumentos opostos, evidências, provedor/custo e incertezas. Consenso de agentes não prova correção, especialmente se todos usam mesmo LLM.
- Preferir execução sequencial em modelos pequenos ou chamadas autorizadas para PC modesto. Sem exigir multi-modelos em paralelo nem gasto adicional.
- O modelo nunca pode autorizar ferramentas a si mesmo, promover privilégios, acessar dados sem permissão ou modificar políticas de segurança.
- Em riscos de dano irreversível, gastos, acesso/compartilhamento de dados sensíveis, alteração de contas, postagem, instalação ou destruição de arquivos, consultar usuário salvo política futura muito específica e segura; **nenhuma permissão desse tipo foi concedida neste turno**.

### Níveis de autonomia a calibrar a seguir
- **Nível 0:** apenas conversar e recomendar.
- **Nível 1:** fazer automaticamente verificações/leitura e elaborar resposta, respeitando acessos já autorizados.
- **Nível 2:** executar automaticamente pequenas correções **reversíveis e preaprovadas**, com registro, rollback e limites.
- **Nível 3:** ações com efeitos relevantes que exigem aprovação pontual ou regras específicas por tarefa; não ativado por consenso genérico.

**Pergunta pendente:** o que o conselho pode executar sem perguntar? A decisão de ter conselho não constitui concessão automática de nível 2 ou 3.

## E. Resposta vocal e momentos de decisão humana

Ao acordar/alertar o proprietário em evento crítico, explicar em uma ou duas frases:
- O que foi detectado, com evidência e grau de confiança;
- Quais opções principais os agentes consideraram e qual recomendam;
- Qual decisão humana é necessária, se houver.
A transcrição de uma ordem relevante deve ser exibida no dispositivo e confirmada com mecanismos próprios antes da ação, para evitar erro de reconhecimento e ordens de terceiros.

**Exemplo original de situação crítica:**
"NEXUS: Detectei falhas repetidas de escrita no disco principal. Há risco de perda de dados. O conselho recomenda interromper operações de gravação e verificar o armazenamento. Preciso da sua autorização para desligar o serviço de sincronização. Posso mostrar a evidência no PC e no J6."

O estilo de Sukuna é suspenso no trecho crítico, mantendo voz pessoal e respeitando limites de licenciamento TTS.

## F. Critérios de aceitação (para etapa futura)

1. Percepção contextual consulta câmera/tela só se necessário, autorizado, auditável e com indicador, sem inferir disponibilidade com certeza injustificada.
2. Alerta crítico topmost não bloqueia saída do usuário, não suspende processos nem provoca perda de trabalho; fallback quando fullscreen protegido.
3. Mudança de volume respeita teto seguro configurado, canal correto, restauração e não aumenta indiscriminadamente fones de ouvido.
4. Descanso: tenta chamar só em evento crítico de fonte confiável, com tentativas limitadas; voz offline reconhecida como indisponível.
5. Resposta vocal entende intenção mas pede confirmação segura antes de operações consequenciais.
6. Discussão multiagente inclui contraponto real e critério de parada, sem custos adicionais automáticos.
7. Nenhum agente consegue conceder permissão a outro nem interpretar o próprio consenso como autorização.
8. Para chamadas simples, não sobrecarrega com cinco agentes sem benefício demonstrado.
9. Mantém distinção de estado: sugerido, em análise, aguardando autorização, executando, concluído e verificado.
10. Só relatar capturas e alertas que ferramentas confirmaram; simular condições antes de uso real.

## G. Estado real e decisões pendentes

O MARK LVII original **não foi instalado nem homologado** no Windows. Nenhum serviço, agente, overlay, detector de sono, sistema de volume, câmera, notificação ou voz foi implementado ou ativado aqui.

**Aprovado:** percepção sob demanda, intenção de alerta visual forte, escalonamento de voz seguro para presença em casa, possibilidade de despertar em crítico, debate de agentes na maioria dos problemas.

**Pendente:** limites numéricos e de invasividade, confirmação segura por voz, classificação de emergência, canais e **níveis de ações que agentes podem executar sem consultar**. Este documento é de arquitetura desejada, não um protocolo já funcional.


## H. D-031: autonomia de execução por categoria (2026-11-23)

**Escolha explícita:** o usuário optou pela alternativa **C: autonomia por categoria**. O NEXUS poderá executar sem consulta repetida **apenas ações pertencentes a categorias que o usuário aprovar antecipadamente**, com limites claros. Não escolher categorias nem níveis automaticamente com base nesta resposta.

### Política de execução obrigatória
1. **Unidade de autorização:** `categoria + ação específica + recurso/dispositivo + contexto + limites + prazo de validade`. Categorias amplas não habilitam toda ferramenta relacionada.
2. **Permissões de menor privilégio:** somente operações explicitamente permitidas, incluindo escopo de leitura/gravação, conta, pasta ou serviço; na ausência de correspondência, **negar e solicitar autorização**.
3. **Conselho versus executor:** agentes deliberam e recomendam; um executor determinístico valida autorização independentemente dos prompts ou votação dos agentes.
4. **Gates de impacto:** gravações, instalações, exclusões, mudanças de segurança, mensagens a terceiros e movimentação de dinheiro não são permitidas por inferência; precisarão de uma decisão própria e, quando apropriado, autorização pontual.
5. **Limites:** frequência e tempo, uso de CPU/RAM, volume de dados, orçamento diário, impacto e reversibilidade; fallback pago desativado.
6. **Auditoria:** registrar evidência que motivou a ação, permissão aplicada, comando real, resultado e rollback disponível; distinguir `enviado`, `executando`, `verificado` e `falhou`.
7. **Revogação:** botão de pausa, desativação por categoria e dispositivo, expiração de tokens e revogação imediata; revogação deve impedir novas ações e cancelar trabalhos pendentes quando seguro.
8. **Emergência:** o protocolo de alertas pode chamar o usuário, inclusive por voz em crítico confirmado, mas não concede privilégios adicionais ao executor.

### Categorias candidatas para deliberação, ainda NÃO autorizadas
- Diagnóstico e leitura de informações de sistema;
- Ajustes reversíveis de baixo impacto;
- Manutenção do PC e aplicativos;
- Organização de arquivos e backups;
- Segurança defensiva e resposta a incidentes;
- Pesquisa, organização de conhecimento e recomendações;
- Automação de contas, mensagens e serviços externos;
- Gestão de outros dispositivos (J6+/Infinix/câmeras).

**Diretriz posterior D-032:** adiar escolha de categorias e permissões específicas. O proprietário fará essa configuração **na Central de Controle do NEXUS**; não solicitar definições uma a uma nesta conversa.

**Status:** apenas desenho e decisão de modelo de autorização; nenhuma categoria aprovada, nenhum código/permissão ativado no MARK.


## I. D-032: Central de Controle como ponto de autorização (2026-11-23)

O proprietário decidiu: **"Isso aí eu defino na central"**. O grau de acesso para diagnóstico e as demais categorias da D-031 devem ser ajustados por ele na futura **Central de Controle**, não escolhidos agora via chat.

### Requisitos da Central (proposta decorrente da decisão)
- **Categorias claramente identificadas:** diagnóstico, manutenção, arquivos/backup, segurança, automação, dispositivos, pesquisa e outras adicionadas com controle do proprietário.
- **Permissão por ação e recurso:** mostrar exatamente qual ação pode ser feita, em quais dispositivos/pastas/contas, se acessa apenas metadados ou conteúdo, em quais condições e por quanto tempo.
- **Controles simples:** conceder/negar, pausar, revogar, expirar permissões, visualizar status e histórico de execuções e tentativas negadas.
- **Confirmação e segurança:** configuração sensível requer autenticação; agentes podem sugerir alterações, mas **não podem aprová-las ou ampliar privilégios por conta própria**.
- **Padrões:** negar tudo o que ainda não tiver sido expressamente aprovado; configurações de tela, câmera, áudio e localização são permissões específicas por fonte/dispositivo.
- **Transparência:** explicar riscos, alcance e exemplos antes de habilitar um acesso, com linguagem compreensível.
- **Desempenho:** política de permissões não deve depender de modelo pesado; verificar regras em código independente da deliberação da IA.
- **Registro:** nome do autorizador, escopo, versão, data, expiração, motivo do uso, resultado e revogação.

**Não foi concedida nenhuma autorização operacional.** Os detalhes visuais da Central e de cada categoria ficam para fase futura. O MARK original segue intocado.
