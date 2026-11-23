# Relatório de pesquisa documental: 23 de novembro de 2026

## Resumo executivo

O MARK LVII original continua sendo a base candidata. Reutilização em projeto pessoal não elimina condições de licença. **Nenhuma integração, correção ou teste em hardware foi feita nesta pesquisa.** Esta rodada priorizou problemas reproduzíveis e comparou projetos por função, custo, compatibilidade e manutenção.

### Principais conclusões
1. **Companion J6:** MARK já captura microfone remoto, mas painel HTTP padrão conflita com getUserMedia; o próprio JS orienta usar chrome://flags para tratar origem insegura como segura. Solução de laboratório preferida: HTTPS privado com Tailscale Serve, autenticação própria e WSS, sem flags.
2. **Áudio de volta:** o fluxo /ws/phone-audio só recebe; retorno de fala para o Bluetooth do J6 requer adaptação e testes.
3. **Segurança:** token em URL, execução de plugins durante import e dev-agent com execução/instalação são superfícies prioritárias. Preservar os bons controles já existentes: confirmação por HUD, limitação de agentes, escrita atômica de config.
4. **Memória:** antes de importar Mem0 ou banco novo, corrigir/gravar testes para escrita não atômica do JSON de memória.
5. **Cloud opcional:** MANIFEST de core/cloud.py aponta plugins ausentes no snapshot. Não concluir que o desktop inteiro esteja quebrado: validar o caminho opcional separadamente.
6. **OpenJarvis:** aproveitar política de capacidades e manifesto; notar que montagem sem allowlist de roots configurada permite raízes não bloqueadas, portanto tornar o nosso padrão explicitamente deny-by-default.
7. **Ecossistema:** OpenClaw para ideias de gateway/nós; go2rtc como candidato leve Windows RTSP; Browser Use e Mem0 só após comparação com funcionalidades nativas do MARK.
8. **Android:** VoiceAssistantPhone é relevante, porém não tem licença pública detectada e não é plug-and-play; Mic2Bluetooth requer Android 12+, enquanto J6+ usa Android 10.
9. **Custo:** não presumir que Plus elimina custos de API; Sign in with ChatGPT oficial está sujeito a elegibilidade, endpoints e limites. Não ativar cobrança/fallback pago.

### Status de trabalho
| Item | Estado |
| --- | --- |
| Pesquisa de código MARK | Inspeção estática seletiva concluída |
| Comparativo OpenJarvis e outros projetos | Concluído para seleção inicial, não auditoria exaustiva |
| Documentação no N.E.X.U.S | Registrada |
| Instalação MARK no Windows | NÃO INICIADA |
| Testes no J6/BT/PC/câmera | NÃO INICIADOS |
| Correções no MARK | NÃO INICIADAS |
| Código de outros repositórios importado | NENHUM |
| Custos novos contratados | NENHUM |

### Primeiro experimento quando o PC estiver disponível
1. Instalar e testar o MARK **sem alterar código** conforme 07-PRIMEIRO-TESTE.md.
2. Anotar falhas reais e consumo.
3. Experimentar dashboard local e HTTPS privado para microfone do J6 (sem privilégios extras).
4. Medir se saída da IA permanece somente no PC, preparando design do canal inverso.
5. Classificar propostas e iniciar somente correções comprovadas.

### Próximas decisões humanas (somente quando necessárias)
- Hospedar só documentos neste repositório até a homologação: **já decidido**.
- Alterar repositório para privado ou renomeá-lo: não decidido nesta rodada.
- Provedor principal de IA e elegibilidade ChatGPT: aberto para testes.
- App J6 PWA ou APK: começar PWA, mudar para APK se background/roteamento impedir experiência.
- Câmera: validar RTSP existente, sem presumir ONVIF/PTZ.

**Regra:** notas e pesquisas são hipóteses até provas no hardware. Novos projetos apresentados pelo usuário entram no mesmo processo de triagem, sem substituir silenciosamente as decisões anteriores.
