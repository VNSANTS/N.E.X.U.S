# NEXUS: regra universal de voz, referência Sukuna

**Data da decisão:** 2026-11-23  
**Status:** requisito de experiência aprovado pelo usuário; **não implementado nem testado** no MARK LVII.  
**Referência solicitada literalmente:** **a voz de Sukuna, personagem de Jujutsu Kaisen**, e não somente uma voz masculina genérica. **Interpretação definida:** dublagem brasileira de Ryomen Sukuna por **Francisco Júnior**.

## Regra universal solicitada

- O usuário quer **a voz do Sukuna como identidade vocal padrão e consistente do NEXUS**.
- Aplicar o mesmo perfil de voz em **todas as falas sintetizadas** no PC e no futuro Companion Galaxy J6+ por Bluetooth, incluindo respostas, alertas, confirmações, avisos e fala iniciada pelo próprio NEXUS.
- A **personalidade do assistente** continua sendo a especificação NEXUS v1.0 com 35 características. **Não copiar o comportamento cruel, ameaçador ou a personalidade de Sukuna**; a escolha é da **voz**, não do caráter.
- Fala precisa ser clara e inteligível em **português brasileiro** para uso cotidiano, ainda que a referência vocal escolhida seja a versão original japonesa.
- Em emergências/alertas, modificar prosódia (seriedade, ritmo, volume) sem perder uma identidade vocal reconhecível. Humor e fala cotidiana seguem regras da persona.
- Trocar entre ferramentas de voz não deve resultar em mudança silenciosa e inesperada de timbre: exibir aviso e oferecer escolha explícita de alternativa.

## Fidelidade, direitos e segurança

- **Preferência do usuário:** fidelidade à interpretação vocal da **dublagem brasileira de Sukuna por Francisco Júnior**.
- **Limite real:** não declarar que existe motor capaz de reproduzir exatamente essa voz antes de pesquisar disponibilidade/licenças e fazer teste perceptual. A forma de entrega deve respeitar permissões aplicáveis a gravações e voz de dubladores, direitos de execução e termos do fornecedor.
- Evitar extração e clonagem não autorizadas de gravações comerciais ou da voz de um dublador real. Procurar uma licença/autorização adequada para a solução pretendida; se a reprodução exata não for possível, submeter alternativas com timbre/prosódia semelhantes **sem substituir sorrateiramente a preferência**.
- O projeto permanece pessoal e experimental, mas uso privado não significa que toda amostra/voz esteja livre de direitos. Não publicar modelos de voz, samples derivados ou gravações de terceiros sem base legal/licença.
- Não usar a saída de voz para induzir terceiros a crer que ouviram o ator/dublador real.

## Compatibilidade técnica a investigar depois do baseline MARK

1. Inspecionar provedores de voz realmente suportados pelo MARK e se aceitam uma voz personalizada, áudio de saída e streaming de TTS.
2. Diferenciar voz de resposta do Gemini Live (vozes pré-definidas), TTS externo/local e conversação bidirecional, inclusive latência e interrupções.
3. Se o provedor LLM de voz não suporta timbre escolhido, avaliar **STT -> LLM textual -> TTS autorizado** como caminho modular. Medir atraso contra Gemini Live; não prometer mesma baixa latência.
4. Garantir uma identidade de saída em PC, painel web e Companion J6. O J6 toca o áudio recebido, sem precisar sintetizá-lo localmente na primeira versão.
5. Avaliar qualidade em PT-BR, naturalidade, inteligibilidade, estabilidade, emoção moderada, latência, custo, RAM/CPU e funcionamento offline quando necessário.
6. Separar áudio gerado de sons do sistema; configurações de dispositivo Bluetooth não autorizam o acesso ao microfone ou a sensores.
7. Implementar fallback apenas com visibilidade e consentimento do usuário para não perder a identidade solicitada.

## Testes de aceite futuros

- O usuário escolhe uma referência precisa de Sukuna e aprova um sample licenciado/gerado do perfil vocal.
- Pronúncia e inteligibilidade adequadas em PT-BR; ao menos testes com texto casual, técnico e mensagens curtas.
- Timbre e identidade consistentes em PC e J6+; variações de urgência não transformam a voz em outra.
- Boa latência na conversa com possibilidade de interrupção; medir no hardware real.
- Sem envio oculto de gravações de referência ou dados pessoais a provedores externos; informar tratamento de dados.
- Troca de provider não substitui a voz em segredo; a falha é sinalizada.
- Licenças, direitos da voz e termos de uso verificados e documentados antes de integrar uma reprodução fiel.

## Pendência única mais imediata

**Resolvido em 2026-11-23:** referência é **Francisco Júnior como Sukuna, na dublagem brasileira**. Pendem viabilidade técnica, direitos/autorizações e um teste de voz para aprovação. Não publicar áudio de referência ou modelo derivado sem permissão adequada.

**Nenhum código do MARK LVII foi alterado nesta etapa.**


## Dublagem escolhida, referência verificável (2026-11-23)

- **Identidade vocal desejada:** Francisco Júnior no papel de **Ryomen Sukuna**, série **Jujutsu Kaisen**, áudio da **dublagem brasileira em português brasileiro**.
- **Fontes de verificação:** [Dublapédia: elenco de Jujutsu Kaisen](https://dublapedia.com/wiki/Jujutsu_Kaisen), [JBox: Francisco Júnior](https://www.jbox.com.br/j-pedia/perfis/francisco-junior/), [DubFinder: Francisco Junior](https://dubfinder.app/pt/dubladores/francisco-junior/).
- Não confundir com a interpretação de Junichi Suwabe na versão japonesa.
- A identidade vocal desejada vale para todas as respostas faladas do NEXUS, inclusive Companion J6+, independentemente do modelo de linguagem.
- **Compromisso de honestidade:** não afirmar que reproduzimos perfeitamente o ator antes de termos solução tecnicamente viável e direitos de uso assegurados. Não extrair amostras de episódios ou clonar a voz sem autorização adequada.
- Fica pendente escolher tecnologia de voz, opções de licenciamento, qualidade perceptual e viabilidade no PC/J6+; o código do MARK não foi alterado.


## Complemento: referência de estilo de fala (2026-11-23)

A escolha não se limita ao timbre. O usuário também quer que o NEXUS tenha um **jeito de falar inspirado em Sukuna**, especialmente **autoconfiança imponente e arrogância elegante**, com ironia provocativa e carisma casual.

- **É uma camada expressiva do NEXUS**, não adoção da personalidade violenta ou do desprezo pelo interlocutor do personagem.
- Em conversas casuais: mais sarcasmo controlado, brincadeiras desafiadoras e segurança teatral.
- Durante trabalho: comentários afiados pontuais, sem perder objetividade, cooperação ou precisão.
- Emergências e assuntos sensíveis: tom calmo, direto, sem provocações.
- **Separação:** referência vocal = dublagem de Francisco Júnior; estilo de fala = padrão textual/expressivo. Ambos documentados, nenhum implementado.
- Ver [docs/14-PERSONALIDADE-NEXUS-V1.md](14-PERSONALIDADE-NEXUS-V1.md) para regras de comportamento e exemplos.
