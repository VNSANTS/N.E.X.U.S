# Provedores de IA: pesquisa e restrições

**Status:** estudo; nenhuma integração nova implementada.

## Atualmente no MARK LVII
- `core/gemini.py` e pipeline Gemini Live para conversação de áudio.
- `providers/llm_openai.py` usa API compatível com `/v1/chat/completions`, com presets para OpenAI, Ollama, Groq, DeepSeek e outros.
- Engines alternativas combinam STT (Whisper), modelo e TTS (Piper/voz do sistema/ElevenLabs conforme configuração).

## ChatGPT Plus

A assinatura ChatGPT Plus **não é automaticamente uma chave nem franquia ilimitada da API OpenAI**. Não usar cookie, token de sessão web nem automação do site ChatGPT para burlar o acesso. Investigar apenas canais **oficiais e elegíveis** de autenticação, incluindo Sign in with ChatGPT quando permitido, conferindo termos e capacidades atuais. A integração eventualmente poderá cobrir texto/ferramentas sem fornecer o mesmo serviço de streaming de voz Gemini Live.

## Estratégia
1. Primeiro homologar Gemini Live e o modo OpenAI-compatible atual.
2. Construir gateway com interfaces distintas para texto, ferramentas, voz e visão, sem fingir que todo provedor oferece todas as modalidades.
3. Descrever política de dados, cotas, limites, fallbacks e endpoints por provedor.
4. Preferir modo grátis explicitamente autorizado; falhas devem explicar indisponibilidade em vez de trocar para um plano pago.
5. Só experimentar autenticação oficial ChatGPT depois de provar elegibilidade técnica e do aplicativo.
6. Testar português brasileiro, tempo de resposta, streaming, interrupção, consumo e capacidade de function/tool calling.

## Prova de aceite
- Configuração segura; nenhum token em logs.
- Mensagem clara para quota ou permissão insuficiente.
- Nenhuma cobrança implícita.
- Ferramentas não executam sem validação do core.
