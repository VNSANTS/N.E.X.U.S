# Chat local seguro e cofre de credenciais — NEXUS MARK LVII

**Data:** 2026-11-23  
**Decisão:** D-040, esclarecimento de D-039 e das permissões da Central D-031/D-032.  
**Estado:** especificação apenas; nenhuma implantação, captura, armazenamento ou autorização de uso de credenciais em produção.

## Intenção explícita

O proprietário quer poder **mandar uma senha/credencial no chat do NEXUS e pedir ao assistente que trabalhe com ela**, desde que **a senha nunca seja exposta a um serviço externo de IA**. Se a compreensão da instrução exigir IA, **usar modelo local apenas na parte que trabalha com o segredo**. Guardar segredos persistentes somente com autorização; padrão desligado (D-039).

### Distinção essencial
- **Provedor externo de IA, busca, analytics, telemetria, transcrição, TTS, ferramenta de terceiros:** nunca receber valor de senha, token, chave privada ou conteúdo secreto.
- **Serviço de destino explicitamente autorizado para a tarefa:** o executor pode transmitir a credencial **diretamente ao endpoint de autenticação oficial desse serviço**, quando isso for necessário para o login solicitado. Isto não é permissão para divulgá-la a provedores de IA ou intermediários.
- **ChatGPT ou outro chat hospedado fora do NEXUS local:** enviar um segredo ao serviço de chat já envolve transferência do dado àquele serviço. **Não prometer processamento exclusivamente local no ChatGPT**. O requisito destina-se ao futuro chat próprio do NEXUS.

## Arquitetura de fluxo seguro

### 1. Entrada de segredo
- A interface do NEXUS deve oferecer **campo de credencial seguro** no próprio chat e possibilidade de colagem de texto com detecção e segregação local **antes** de enviar conteúdo para qualquer componente de nuvem.
- Dar suporte à intenção "mande no chat" de forma natural, mas incentivar campo seguro para maior proteção, porque detectar todos os formatos de senha em texto livre **não é infalível**.
- Quando detectado: substituir o valor por marcador opaco, ex.: `[CREDENCIAL_PROTEGIDA]`, na conversa comum. O valor original só segue para o fluxo local isolado.
- Mensagens não devem ser enviadas para LLM remoto até passar pelo **filtro local de segredos**; evitar que streaming, envio prévio, logs de requisição, histórico de navegador ou cache de app gravem o segredo bruto.
- Se o segredo escapar ao isolamento e tiver sido enviado a serviço externo, **não afirmar que ficou local**; registrar incidente, avisar ao usuário e recomendar rotação quando necessário. Nunca presumir que mascarar depois apaga uma exposição anterior.

### 2. Processamento e uso local
- A compreensão de credenciais é **local** por padrão; preferir parsing/validação determinísticos e chamadas diretas de ferramenta. Quando necessário, selecionar **modelo realmente executado no próprio PC do usuário**, sem API remota para esse trecho.
- **Bloqueio técnico de saída**: segredos não podem ser interpolados em prompts de IA remota, pesquisas, consultas de agentes externos, captura de erros, crash reporting, embeddings, sincronização ou telemetria. Não confiar apenas em "instrução do prompt"; impor controles no roteador, executor e egress de rede.
- O modelo externo, se usado para assuntos não secretos, recebe somente instrução saneada/metadados mínimos ("usuário forneceu credencial protegida; pedido: login no serviço X"), **nunca o valor**.
- O executor obtém o segredo localmente apenas no momento do uso e só para alvo/conta/operação autorizados na Central. Modelos (até locais) não deveriam obter o valor bruto quando uma ferramenta parametrizada pode usá-lo sem isso.
- Ferramentas, navegador e extensões não confiáveis não recebem credenciais. Mitigar prompt injection de sites, instruções externas pedindo revelação e vazamento por URLs/query strings.

### 3. Proteção de armazenamento e sessão
- **Sem salvamento persistente por padrão.** Em uso pontual, manter apenas em memória pelo período estritamente necessário; limpar após conclusão quando tecnicamente possível. Não alegar apagamento garantido de todos os vestígios em RAM/swap sem comprovação.
- **Com autorização específica para guardar**: usar cofre separado da memória do chat, com criptografia em repouso, autenticação, acesso mínimo, logs sem valores, expiração/revogação e exclusão; preferir armazenamento seguro do sistema operacional e proteger backups.
- Separar permissões **guardar, ler, usar para login, usar para tarefas automatizadas e compartilhar com destino autorizado**. O consentimento para uma não concede as outras.
- Central: mostrar apenas nome/serviço/identificador mascarado da credencial e histórico de uso, nunca valores por padrão; permitir revogar, rotacionar, esquecer e desativar processamento.
- Não falar senha em voz alta; impedir que TTS/STT externos recebam segredo. Para credencial ditada oralmente, somente reconhecimento local aprovado ou recusar via canal inseguro.

### 4. Segurança dos dispositivos e transporte
- No **PC local**, proteger processo de recepção e roteamento, controle de janelas, arquivos temporários, clipboard (quando viável), logs, mecanismos de crash e permissões de SO.
- Do **Galaxy J6+ ao PC**, proteger tráfego com criptografia/autenticação ponta a ponta no canal do aplicativo; Tailscale é a camada de rede, não substitui validação de sessão/autorização por aplicativo.
- O chat do NEXUS no dispositivo remoto não deve enviar o segredo para serviços externos no próprio Android (teclado com sincronização, backups, autofill não confiável); informar limitações reais e oferecer entrada segura.
- Se o modelo local estiver indisponível e a tarefa exigir o segredo, **não aplicar fallback em nuvem**: suspender o fluxo e explicar que precisa de processamento local.
- Para operações irreversíveis ou alto impacto, solicitar confirmação autenticada separada. Não confiar só em texto vindo de página ou em consenso de agentes.

## Caso de uso ilustrativo

1. Usuário: "Entre na minha conta do serviço X." Fornece senha no campo seguro do chat.
2. NEXUS local guarda somente uma referência efêmera da credencial no histórico e verifica se há autorização de login para X.
3. Roteador pode deliberar o procedimento com modelo remoto **apenas sobre contexto saneado**. Tratamento do valor secreto permanece local.
4. Executor autorizado envia o segredo **somente ao login oficial de X**, sem intermediá-lo por um provedor de IA.
5. NEXUS: "Login concluído" **apenas após evidência real de autenticação**, ou "Não foi possível confirmar o login" se falhou.
6. Se não houve autorização de armazenamento, o segredo não é incorporado à memória persistente.

## Critérios de aceite
- Inspecionar tráfego e logs em testes com credencial sintética; verificar **zero transmissão do valor secreto a provedores de IA, pesquisa, telemetria ou serviços não autorizados**.
- Testar senha colada no chat, senha enviada via campo seguro, tentativa de exfiltração por prompt injection e ausência de modelo local.
- Testar interface Android, reconexão, histórico, cache de navegador e recuperação de falhas.
- Testar autorização negada, autorização pontual, cofre persistente, revogação, rotação e não duplicação em prompts.
- Confirmar que mascarar mensagem **antes** do envio é requisito e que segredos escapados não podem ser tornados privados retroativamente.
- Nunca usar credenciais reais em logs, testes automatizados ou commits.

## Estado e relação com decisões anteriores

Complementa **D-039 (memória sensível sob opt-in)**, **D-031/D-032 (permissões na Central)**, **D-038 (roteamento de especialistas)** e **D-006 (custo adicional zero)**. O comportamento é desejado, não comprovado. O MARK original permanece não instalado/não homologado, e nenhuma alteração em seu código foi feita.
