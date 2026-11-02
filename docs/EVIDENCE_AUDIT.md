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
- Até uma claim por especialista.
- Cada claim tem até 50 caracteres e até três IDs de evidência.
- Apenas Analyst e Reviewer recebem o catálogo de fontes.
- Claims estruturadas são passadas ao modelo de síntese como dados não confiáveis.
- Nenhum especialista recebe ferramentas ou permissão para executar ações.

## Próxima evolução

Adicionar persistência de evidence records com hash, URL, título, data de recuperação, trecho exato e referência à claim; produzir um relatório de conflitos entre fontes e exigir revisão independente antes de promover afirmações ao conhecimento validado.


## Política da síntese final

Quando a execução inclui fontes, a camada de síntese remove deterministicamente claims marcadas como `unreferenced` antes de passar os resultados dos especialistas ao modelo final. Cada entrega informa quantas claims foram omitidas. Claims `source_linked` permanecem identificadas como não verificadas; a política proíbe tratá-las como verdade comprovada. Resumos e itens dos especialistas continuam sendo análise não confiável e não são promovidos automaticamente a fatos.

Sem catálogo de fontes, claims permanecem visíveis como `unreferenced`, mas o contexto da síntese instrui explicitamente que não podem ser apresentadas como fatos verificados. O Reviewer recebe a instrução de apontar afirmações sem referência nos seus itens de revisão.

Esta política é uma barreira de estrutura e instrução, não uma garantia de que o LLM final nunca vá parafrasear incorretamente uma afirmação. Para uso crítico, é necessária revisão independente/humana.


## Reviewer claim assessments

The Reviewer must return one assessment per Analyst claim. Each finding includes a zero-based `claim_index`, a bounded note (maximum 100 characters), and one of:

- `supported`: the Reviewer model believes the supplied evidence is relevant; this is advisory, not proof.
- `unsupported`: the Reviewer model did not find support in the supplied context.
- `uncertain`: insufficient context to assess.
- `conflicting`: the Reviewer model identifies disagreement in the supplied material.

The parser requires one-to-one coverage and rejects duplicated/missing/out-of-range indices. It rejects `supported` when the Analyst claim has no supplied evidence ID. The Reviewer cannot create factual claims in its review output.

Before final synthesis, Analyst claims marked `unsupported` or `conflicting` are withheld deterministically, even if source-link filtering is disabled. Claims marked `uncertain` remain labelled with their review status/note. The final model is instructed not to restate rejected claims as facts.

A distinct Reviewer provider/model is recorded in metadata as `separate_review_model`; using a second model is not independent verification, source validation, human review, or approval of actions.
