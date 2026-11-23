# NEXUS Companion: opções de transporte e limitações Android

**Status:** estudo de arquitetura, sem app construído. Decisão já tomada: Galaxy J6+ como comunicador **dependente do PC**. Versão inicial é voz por microfone interno do J6 e saída em fone Bluetooth; sem IA própria.

## Descoberta importante no código do MARK
O dashboard já coleta microfone via getUserMedia, converte PCM para 16 kHz e envia no WebSocket /ws/phone-audio:
- [JavaScript app.html 445-590](https://github.com/FatihMakes/Mark-LVII/blob/752ff618a4e6a4bf2e675866b993071d739cfce2/dashboard/static/app.html#L445-L590)
- [FastAPI WebSocket 1044-1070](https://github.com/FatihMakes/Mark-LVII/blob/752ff618a4e6a4bf2e675866b993071d739cfce2/dashboard/server.py#L1044-L1070)
- [Relay main.py 2515-2534](https://github.com/FatihMakes/Mark-LVII/blob/752ff618a4e6a4bf2e675866b993071d739cfce2/main.py#L2515-L2534)

**Isso NÃO entrega a voz de resposta ao telefone**. É necessário verificar o motor TTS/Gemini e acrescentar retorno autenticado de áudio se for a abordagem escolhida. Em fluxo atual, _relay_phone_audio ignora novos chunks enquanto o assistente fala, portanto interrupção por voz exige experimento.

## Opção 1: PWA/browsers HTTPS (primeira preferência)
- J6 abre URL HTTPS privada do PC; botão pressionar-para-falar e mostra estado.
- Tailscale Serve proxy para serviço local, com certificado válido e WSS. Testar integração com WebSocket do MARK.
- O MARK continua exigindo autenticação própria, sessão expira e pode ser revogada.
- Medir comportamento com tela bloqueada: browser em segundo plano pode suspender getUserMedia/AudioContext, então NÃO prometer escuta contínua.
- Vantagem: quase zero instalação no J6, reutiliza UI atual; desvantagem: background limitado e rotas de áudio difíceis de forçar.

## Opção 2: APK nativo Android (se opção 1 não atender)
- Kotlin + AudioRecord para entrada, AudioTrack/ExoPlayer para saída, WebSocket autenticado para comandos e áudio.
- Serviço foreground com notificação persistente e permissão RECORD_AUDIO; seguir regras do Android e comportamento do aparelho Android 10.
- PTT iniciado com aplicativo aberto; depois examinar foreground sem restrições de boot indevido.
- Detectar rota de saída A2DP Bluetooth. Em modo de comunicação, algumas versões mudam rota para HFP/SCO: não assumir que o fone sem microfone funcionará em todo modo.
- Não introduzir STT/wake word local inicialmente, evitando carga no J6+.
- Assinatura APK estável para atualização; versão e testes de instalação/atualização.

## Por que NÃO copiar os candidatos Android imediatamente
- VoiceAssistantPhone inclui mic, speaker e câmera sobre Tailscale e tem minSdk 26; combina com Android 10. Porém **não existe licença de reutilização identificada** e o servidor é de outro assistente: estudar conceitos e buscar autorização antes de usar código.
- Mic2Bluetooth explica A2DP/HFP e PTT, porém exige Android 12+, incompatível com o J6+ Android 10.
- AndroidMic funciona como fonte de microfone para PC (inclui Windows), mas não é o Companion bidirecional. É GPL-3.0 e exige cuidado com cópia/distribuição.
- TailWispr tem boas ideias para reconexão, TLS e captura via browser, mas o receptor serve macOS/Linux, não Windows no README do snapshot.
- OpenClaw tem app Android e gateway, mas não justificaria trazer toda stack Node para um cliente leve.

## Proteção de sessão
- Associação do dispositivo com PC aprovada uma vez, token único por aparelho, expiração e revogação.
- Sem tokens em query de WebSocket, logs, links compartilháveis ou backup em texto claro.
- Rejeitar cliente que se apresenta como dispositivo revogado; rate limit e proteção contra replay.
- Escopo de voz/chat diferente do escopo de comandos de sistema: J6 não ganha privilégio de apagar arquivos só por conectar.
- PC desligado => estado offline e sem resposta fabricada; reconectar com backoff.

## Indicadores a medir
- Microfone correto: voz captada sem depender de headset HFP.
- Saída: áudio da IA pelo Bluetooth, não apenas pela caixa do PC.
- Latência ponta a ponta, echo/feedback, clipping, interrupção da voz.
- Reconexão quando Wi-Fi/BT alternam, aplicativo sai da frente e tela bloqueia.
- Consumo CPU/RAM e bateria J6; evitar escuta 24/7 sem justificativa.
- Feedback visível/sonoro do status, botão de desligar microfone.

## Fontes externas
- MDN Secure Contexts: https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia
- Tailscale Serve: https://tailscale.com/docs/features/tailscale-serve
- Android foreground service com microfone: https://developer.android.com/develop/background-work/services/fgs/service-types
- Android media output routing: https://developer.android.com/media/platform/output
- Código de referência: https://github.com/VirtualyMichael/VoiceAssistantPhone (NÃO copiar sem licença)


## Comunicação adaptativa universal planejada (D-025, 2026-11-23)

O usuário aprovou que o NEXUS determine a possibilidade de interromper com base em **tela e câmera autorizadas**, mais contexto de atividade do sistema. Se disponível, **voz + notificação**; se ocupado, **somente notificação**. Sob incerteza de contexto, adotar notificação apenas.

- No PC, usar contexto de apps/jogos/fullscreen/atividade primeiro; captura de tela e webcam apenas com permissões específicas e indicadores. Evitar gravação ou streaming contínuo sem necessidade.
- J6+ é inicialmente um Companion de voz; não presumir acesso às câmeras do PC, do Infinix ou do próprio J6. Cada origem necessita autorização por dispositivo; o controle multidispositivo deve preservar escopos por conta/aparelho.
- Captura e classificação exigem consentimento e engenharia de privacidade, baixo consumo de energia, limites de frames/dados, opção de pausar e nenhum envio de dados pessoais para um provedor não autorizado.
- Integração de saída de áudio e notificações ainda depende de implementação/testes. Sem falsa alegação de observação contínua ou de que as interfaces já funcionam.
- **Exceção aprovada em D-026:** risco crítico confirmado deve tentar enviar voz + notificação mesmo se o usuário estiver ocupado, respeitando disponibilidade real de canais e permissões.


### Complemento D-026: canal de alerta para risco crítico
- Quando detectado evento **crítico confirmado por sinal confiável**, o NEXUS pode usar **voz + notificação** independentemente da ocupação do usuário.
- Eventos apenas importantes respeitam a escolha adaptativa (somente notificação quando ocupado); achados informativos nunca usam voz em momento inoportuno.
- Áudio indisponível: fallback por notificação permitida, sem alegar fala entregue. O Companion J6+ precisa de implementação e teste de roteamento Bluetooth, reconexão e status de entrega.
- A exceção não concede permissão para gravação de tela/câmera/microfone nem executa correções automaticamente.
- Somente especificação; nada implementado.


## D-027 a D-030 — Contexto sob demanda e respostas de emergência, requisitos futuros

- Escolha do usuário: analisar tela/câmera apenas quando os sinais leves de atividade não bastarem, sempre com autorização por fonte, indicador visível e revogação.
- Um risco crítico confirmado pode solicitar visual forte e voz no PC/J6+; testar camadas de janela, tela cheia, notificações e fallback, **sem suspender processo Windows nem capturar controle irremovível**.
- Volume de aviso pode ser elevado gradualmente só em saída disponível e com teto seguro configurado, respeitando fones, Bluetooth e restauração.
- Acionar usuário fora do PC/descansando exige serviço conectado e ativo, presença/contexto autorizados e comunicação bidirecional já testada. Desligado/offline não há alerta local; voz de confirmação requer proteção contra reconhecimento incorreto.
- Conselho de agentes deve debater, mas não consegue autoaprovar comandos, instalar apps ou abrir acesso a sensores. Veja [17-PERCEPCAO-EMERGENCIAS-E-CONSELHO-DE-AGENTES.md](17-PERCEPCAO-EMERGENCIAS-E-CONSELHO-DE-AGENTES.md).
