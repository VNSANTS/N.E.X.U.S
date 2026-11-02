## Evolução de arquitetura - tool calling e segurança de agentes (2026-11-02)

A pesquisa comparativa do PR #2 indicou que o próximo incremento de maior valor é o ciclo universal de ferramentas. A primeira fatia implementada adiciona contrato normalizado, adapters Ollama/OpenAI-compatible e continuação bounded no runtime. O gate de capacidade exige allowlist exata do modelo; ferramentas disponíveis são somente READ e passam por PolicyEngine.

Referências de inspiração adaptadas: Hermes para recuperação curta e skills sob demanda; OpenClaw para separar gateway/política de ferramenta do ambiente executor; NanoClaw para isolamento futuro de processos que realmente manipulem código/arquivos. Nenhum dos projetos foi instalado nem copiado como runtime. Sem executar código do usuário, a sandbox de container permanece futura.

Decisão reversível: não anunciar tool schemas no SSE enquanto a geração não puder ser cancelada durante uma chamada síncrona. Isso preserva a semântica de cancelamento já testada; o endpoint POST autenticado executa o ciclo de ferramentas.
