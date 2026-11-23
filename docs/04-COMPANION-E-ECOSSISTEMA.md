# NEXUS Companion V0.1 — arquitetura proposta

## Decisão

O **Galaxy J6+ será somente comunicador**, dependente de um MARK LVII rodando no PC. Nada de inferência independente no J6+ no MVP.

```text
J6+ Android (microfone interno + PTT)
       | áudio/comando autenticado, rede privada
       v
PC Windows (MARK LVII + motor de IA)
       | áudio de resposta autenticado
       v
J6+ Android -> saída de mídia Bluetooth A2DP (fone sem microfone)
```

## O que o MARK já oferece

- `dashboard/static/app.html`: captura por `getUserMedia`; converte Float32 para PCM16 (~16 kHz).
- `dashboard/server.py`: WebSocket autenticado `/ws/phone-audio`; fila para pacotes.
- `main.py`: `_relay_phone_audio` envia áudio recebido ao motor.
- **Limitação a validar:** não há comprovação, nesse fluxo, de streaming de áudio sintetizado de volta ao telefone; atualmente o fluxo foi desenhado para voz do celular entrar no Gemini Live do PC.
- O painel remoto em HTTP por padrão NÃO é aceito como arquitetura final do Companion. Evitar credenciais em URL/query e conexões não criptografadas.

## Protocolo futuro (especificação, não implementação)

- Pairing explícito com autorização no PC e segredo aleatório por dispositivo, sem QR que vaze segredo em histórico.
- Canal seguro com troca de tokens curtos e revogáveis; sequência e IDs de sessão; limite de tamanho e validação de frame.
- Pacotes de audio com timestamp, codec/acordo de amostragem, backpressure, ping/heartbeat, cancelamento e política de reconexão.
- Saída de IA em áudio e/ou texto; tratar TTS/Live de modo diferente quando necessário.
- Exibição clara: `desconectado`, `conectando`, `escutando`, `processando`, `falando`, `erro`.
- Comando confirmado no PC antes de qualquer ação sensível e log mínimo sem transcrições pessoais.

## Android e Bluetooth

- Testar seleção da entrada de microfone **do J6+** com saída de mídia Bluetooth; rotas dependem de hardware, versão Android e API usada.
- PTT primeiro; palavra de ativação opcional apenas após bateria/privacidade.
- Serviço foreground com notificação persistente somente quando necessário, respeitando permissões de microfone e restrições Android; sem burlar proteções.
- O fone sem microfone é apenas saída. Se áudio Bluetooth alterar a entrada inesperadamente, detectar e informar erro, não presumir que funcionou.
- J6+ antigo: evitar modelos grandes, serviços pesados, processamento constante e dependência de GPU.

## Integrações futuras (fora da V0.1)

- **Infinix Hot 50i:** agente Android separado, permissões solicitadas caso a caso, controle limitado às APIs/serviços permitidos. Evitar root no telefone principal.
- **PC:** executar ações apenas quando ligado/conectado; confirmar resultado real.
- **Câmera de segurança:** URL RTSP e, se houver suporte, ONVIF; não armazenar senhas no código. A análise de imagens deve ser sob solicitação no início; considerar latência e CPU do PC.
- **Tailscale:** preferido para rede privada entre dispositivos; ainda exigir autenticação de aplicação.
- **Sem PC:** o Companion exibe indisponibilidade. Independência/offline fica fora do escopo por decisão do usuário.

## Critérios de aceite da V0.1
1. J6 emparelha e mostra estado correto do PC.
2. Usuário fala pelo microfone **interno** e o PC recebe áudio.
3. IA devolve áudio pelo fone Bluetooth, inclusive após troca de app, nos limites do sistema.
4. PTT interrompe/cancela sem manter microfone inadvertidamente ativo.
5. Reconexão não duplica comandos nem reaproveita token revogado.
6. PC desligado não gera respostas falsas.
