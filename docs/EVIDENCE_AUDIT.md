# Auditoria estruturada de evidências

## Objetivo

Tornar verificável a ligação entre uma afirmação produzida por um especialista e as fontes que estavam efetivamente disponíveis no contexto, sem confundir citação com prova.

## Contrato de claim

Cada resultado de especialista contém:

- `text`: afirmação curta e delimitada;
- `evidence_ids`: zero ou mais IDs do catálogo de fontes fornecido.

O runtime atribui IDs estáveis dentro da requisição (`S1`, `S2`, `S3`) às no máximo três fontes incluídas no contexto do Analyst/Reviewer. O parser rejeita referências inexistentes, duplicadas ou fora do schema. Claims sem referência são preservadas como `unreferenced`; claims com referências válidas são marcadas `source_linked`.

## O que a validação garante

- O ID citado existia no contexto entregue ao agente.
- O ID não foi inventado pelo modelo dentro daquele deliverable.
- O payload de claim respeita os limites de tamanho e quantidade.

## O que a validação NÃO garante

- Que a fonte é confiável, atual, independente ou correta.
- Que a fonte realmente sustenta o texto da afirmação.
- Que uma claim `source_linked` seja verdadeira.
- Que a revisão feita pelo LLM Reviewer seja uma verificação factual independente.

Não há confiança numérica gerada automaticamente. Para fortalecer a auditoria será necessário persistir proveniência completa, extratos por fonte, posição/trecho, revisão humana ou validação externa adequada. Fontes e saídas dos modelos continuam sendo conteúdo não confiável.

## Limites atuais

- Máximo de três fontes por pipeline; IDs limitados a `S1`–`S3`.
- Até duas claims por especialista.
- Cada claim tem até 60 caracteres e até três IDs de evidência.
- Apenas Analyst e Reviewer recebem o catálogo de fontes.
- Claims estruturadas são passadas ao modelo de síntese como dados não confiáveis.
- Nenhum especialista recebe ferramentas ou permissão para executar ações.

## Próxima evolução

Adicionar persistência de evidence records com hash, URL, título, data de recuperação, trecho exato e referência à claim; produzir um relatório de conflitos entre fontes e exigir revisão independente antes de promover afirmações ao conhecimento validado.
