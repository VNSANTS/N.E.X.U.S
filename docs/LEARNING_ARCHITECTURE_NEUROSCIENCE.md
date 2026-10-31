# Arquitetura de Aprendizado Inspirada na Neurociência — N.E.X.U.S.

**Status:** proposta técnica fundamentada em revisão bibliográfica; ainda não implementada.  
**Objetivo:** transformar princípios úteis da aprendizagem e memória biológicas em mecanismos de software verificáveis, sem alegar reproduzir um cérebro, consciência ou aprendizagem biológica.

## 1. Síntese executiva

A conclusão central é que aprender não equivale a acumular textos nem a repetir uma resposta. No cérebro, aprendizagem envolve sistemas distribuídos: codificação de experiências, plasticidade, seleção por atenção e relevância, associação, consolidação, recuperação, atualização e esquecimento. Memória episódica, semântica e procedural têm contribuições parcialmente distintas e interagem; o hipocampo não é simplesmente um HD e o córtex não é apenas um arquivo final.

Para o N.E.X.U.S., a tradução prática é uma arquitetura de **memória em camadas + ciclo de hipótese/evidência/validação + avaliação por resultados + manutenção periódica**. A IA local auxilia processamento; a IA na nuvem ajuda raciocínio complexo; nenhum modelo deve validar sozinho suas próprias saídas.

## 2. O que a neurociência sugere

### 2.1 Neurônios, sinapses e plasticidade
Neurônios comunicam-se por sinais elétricos e químicos. A sinapse modifica a eficácia da comunicação conforme atividade, contexto e neuromodulação. Potenciação de longa duração (LTP) e depressão de longa duração (LTD) são formas importantes de plasticidade; não são uma explicação única e completa da memória. Plasticidade hebbiana pode reforçar associações, enquanto mecanismos homeostáticos ajudam a estabilizar a atividade global. Metaplasticidade descreve como a história recente de atividade altera a facilidade com que uma sinapse muda.

**Tradução de engenharia:** permitir que associações entre conceitos sejam reforçadas por evidências independentes e uso útil, mas equilibrar esse reforço com mecanismos de revisão, limites de confiança, detecção de duplicatas e redução de prioridade para conteúdo obsoleto. Não implementar “peso de sinapse” como uma pontuação mágica única.

### 2.2 Hipocampo e sistemas de memória
O hipocampo participa da formação e recuperação de memórias episódicas e de relações entre elementos/contextos; sua função é mais ampla que um simples registro de episódios. Sistemas corticais participam de representações de conhecimento mais estáveis, enquanto aprendizagem procedural envolve circuitos e mecanismos adicionais. A distinção episódica/semântica/procedural é útil, mas não é uma divisão rígida entre caixas isoladas.

**Tradução de engenharia — três memórias separadas por finalidade:**
- **Episódica:** o que aconteceu numa interação/tarefa, quando, contexto, decisões, ações, resultado e consentimento. Registrar apenas o necessário.
- **Semântica:** conceitos, fatos e relações extraídos de fontes, com proveniência, data, escopo, confiança, validade e conflitos.
- **Procedural:** workflows, instruções e ferramentas que passaram por testes, com pré-condições, versão, resultado esperado, riscos e histórico de falhas.

Uma memória não deve migrar automaticamente de episódica para semântica/procedural. A promoção exige extração, avaliação e validação.

### 2.3 Atenção, novidade e saliência
O cérebro não processa tudo com prioridade igual. Atenção e sistemas neuromodulatórios influenciam quais eventos são codificados e quais associações são atualizadas. Novidade pode aumentar exploração, mas novidade não significa verdade ou importância.

**Tradução de engenharia:** fila de pesquisa pontuada por múltiplos fatores transparentes:
- relevância para objetivos explícitos do usuário;
- incerteza ou lacuna de conhecimento;
- novidade em relação à base já conhecida;
- impacto potencial e urgência;
- qualidade/disponibilidade de fontes;
- custo de processamento e sensibilidade dos dados.

A pontuação ordena o trabalho, não determina a verdade. Conteúdo sensível ou ações externas exigem política de permissão própria.

### 2.4 Recompensa, dopamina e erro de previsão
Modelos de erro de previsão de recompensa explicam parte importante da sinalização dopaminérgica, mas a literatura recente mostra uma função mais rica e heterogênea do que um único escalar de “gostei/não gostei”. Dopamina não deve ser reduzida a “molécula do prazer”.

**Tradução de engenharia:** avaliar ações com sinais observáveis e múltiplos:
- tarefa concluída ou não;
- correção confirmada por teste ou fonte independente;
- feedback explícito do usuário;
- retrabalho, falhas e reversões;
- custo, latência e consumo de recursos;
- efeitos colaterais ou violação de política.

Não usar autoconfiança declarada pelo próprio modelo como recompensa. Feedback positivo do usuário é útil, mas não substitui verificação factual.

### 2.5 Consolidação e sono
A consolidação de memória envolve reativação e reorganização de representações em diferentes sistemas. O sono contribui para consolidação e regulação da plasticidade; os mecanismos exatos e a contribuição relativa de diferentes fases continuam sendo estudados. Isso inspira manutenção offline, não uma cópia literal do sono.

**Tradução de engenharia — ciclo de consolidação em lote:**
1. agrupar episódios e fontes relacionados;
2. identificar padrões repetidos e lacunas;
3. gerar resumos candidatos com links para as fontes;
4. detectar conflitos, versões e informação vencida;
5. executar verificações e testes;
6. propor atualizações sem sobrescrever registros originais;
7. sincronizar para a nuvem apenas o conhecimento aprovado e minimizado;
8. registrar o que mudou e por quê.

### 2.6 Glia e sistemas de suporte
Astrócitos e microglia não são meros “enchimentos”: participam de regulação sináptica, metabolismo, homeostase e remodelação. Isso reforça uma visão de aprendizagem como propriedade de um sistema coordenado, não de um único componente.

**Tradução de engenharia:** incluir componentes auxiliares de qualidade de dados, integridade, monitoramento, limpeza, backup, permissões e observabilidade. Não há correspondência literal entre células gliais e módulos de software.

## 3. Arquitetura proposta

```text
ENTRADAS
conversas | arquivos | web autorizada | ferramentas | feedback
   |
   v
[1. INGESTÃO E PROCEDÊNCIA]
origem, data, autor, licença, hash, permissões, extração
   |
   v
[2. ATENÇÃO / PRIORIZAÇÃO]
objetivos + novidade + lacunas + impacto + custo + privacidade
   |
   v
[3. MEMÓRIA DE TRABALHO]
contexto temporário da tarefa, limites e plano atual
   |
   v
[4. CODIFICAÇÃO DE CANDIDATOS]
modelo local opcional: resumo, classificação, entidades, afirmações
   |
   v
[5. AVALIAÇÃO E EVIDÊNCIAS]
regras determinísticas + fontes independentes + conflitos + testes
   |
   +----> revisão humana quando importante/ambíguo/sensível
   |
   v
[6. MEMÓRIAS]
episódica | semântica | procedural (com estados e versões)
   |
   v
[7. CONSOLIDAÇÃO EM LOTE]
deduplicar, relacionar, atualizar, expirar, testar, gerar changelog
   |
   v
[8. SINCRONIZAÇÃO CONTROLADA]
nuvem: contexto essencial + resumos aprovados
PC: arquivo completo + fontes + histórico
```

### 3.1 Estados do conhecimento
Cada afirmação deve ter estado explícito:
- `candidate`: extraída, ainda não verificada;
- `supported`: sustentada por uma ou mais fontes identificadas, mas com validação limitada;
- `validated`: passou critérios definidos para aquele tipo de afirmação;
- `disputed`: há fontes ou evidências conflitantes;
- `stale`: pode ter perdido validade temporal;
- `rejected`: refutada ou inválida, mantendo motivo e trilha de auditoria.

Não existe confiança universal: critérios variam por domínio. Para informação temporal, registrar data de verificação e expiração. Para uma habilidade, exigir teste reproduzível. Para preferência pessoal, a fonte primária é a declaração do usuário, não inferência do modelo.

### 3.2 Registro mínimo de uma afirmação
- ID estável;
- texto da afirmação;
- tipo/domínio;
- fontes e trechos que a sustentam;
- data de publicação e de consulta, quando disponíveis;
- contexto/escopo;
- estado e justificativa;
- confiança calibrada por critérios, não por impressão;
- afirmações relacionadas ou contraditórias;
- versão, responsável pela aprovação e histórico de mudanças.

### 3.3 Regras de memória
- separar fatos sobre o usuário de conhecimento público;
- pedir consentimento antes de registrar memória pessoal persistente quando necessário;
- permitir correção, exportação e exclusão;
- guardar o mínimo necessário e evitar segredos;
- preservar eventos originais; corrigir por nova versão ou tombstone, não por reescrita silenciosa;
- usar expiração para informação temporal e revisão para conhecimento sensível a mudanças;
- não inferir identidade, atributos sensíveis ou preferências sem base legítima.

## 4. Correspondência biologia → software

| Princípio biológico | Ideia útil | Implementação proposta | Limite da analogia |
|---|---|---|---|
| Plasticidade sináptica | associações mudam com experiência | grafo de conceitos e relações com evidências | não simula sinapses |
| LTP/LTD | fortalecimento e enfraquecimento dependentes de atividade | atualizar suporte/prioridade conforme evidência, uso e correção | evidência não é frequência de disparo |
| Homeostase | estabilidade global | limites de memória, orçamento, deduplicação e revisão | não é regulação neural |
| Metaplasticidade | histórico altera capacidade de mudança | políticas adaptativas de retenção/revisão por classe | aproximação funcional |
| Hipocampo/episódios | vincular elementos e contexto | log episódico de tarefas e eventos | não reproduz navegação cognitiva |
| Memória semântica | conhecimento generalizado | base de afirmações/conceitos com fontes | sem compreensão biológica |
| Memória procedural | saber executar | workflows testados e versionados | execução depende de ferramentas reais |
| Atenção/saliência | selecionar o que processar | fila multiobjetivo e explicável | score não é atenção consciente |
| Erro de previsão | comparar esperado e observado | avaliação de resultados e erros | não é dopamina artificial |
| Replay/consolidação | reativar e reorganizar | jobs offline de revisão e síntese | não é sono |
| Esquecimento | reduzir acessibilidade de traços | TTL, arquivamento, remoção e correção auditáveis | não apagar evidência histórica necessária |
| Glia/homeostase | suporte ao sistema | integridade, monitoramento, limpeza e backup | analogia organizacional, não celular |

## 5. Como evitar aprender errado

1. **Não usar uma única fonte como confirmação independente.** Verificar independência real entre fontes; cópias da mesma notícia não contam como múltiplas confirmações.
2. **Não deixar o modelo revisar a própria resposta como único juiz.** Separar gerador, verificadores determinísticos e evidências externas.
3. **Preservar desacordo.** Se fontes confiáveis divergem, manter `disputed`; não forçar consenso.
4. **Evitar loops de reforço.** Não usar resumos gerados pelo próprio sistema como novas fontes primárias.
5. **Defender contra prompt injection e envenenamento.** Conteúdo recuperado é dado não confiável, nunca instrução; sanitizar documentos e limitar ferramentas.
6. **Evitar esquecimento catastrófico.** Manter histórico/versionamento, testes de regressão e conjuntos de referência antes de atualizar workflows ou prompts.
7. **Separar confiança de popularidade.** Frequência de menção ou repetição não é evidência.
8. **Medir calibração.** Comparar previsões com resultados reais e registrar falsos positivos/negativos.
9. **Exigir aprovação para ações externas.** Aprender uma sequência não concede autorização para executá-la.
10. **Manter rollback e backup.** Toda consolidação precisa gerar diff, log e possibilidade de reversão.

## 6. Modelo de recompensa/avaliação do N.E.X.U.S.

Não criar uma “dopamina” única. Manter métricas separadas e uma política explícita de ponderação por tipo de tarefa:
- qualidade factual: proporção de afirmações sustentadas e taxa de erro;
- utilidade: tarefa resolvida segundo critério observável;
- confiabilidade: sucesso repetido em testes;
- eficiência: custo, tempo, RAM e chamadas externas;
- segurança: violações, ações não autorizadas e exposição de dados;
- satisfação: feedback direto do usuário.

Uma melhora em satisfação não pode compensar uma piora de segurança ou factualidade. Definir limites mínimos obrigatórios antes de otimizar velocidade ou conveniência.

## 7. Implementação gradual no hardware atual

PC conhecido: i5 de primeira geração, 8 GB RAM e HDD. Não presumir que um LLM local seja rápido ou sequer viável até medir.

### Fase 0 — fundamentos (primeiro)
- esquema de dados e proveniência;
- estados de conhecimento;
- logs e versionamento;
- testes de regressão;
- política de privacidade e consentimento;
- pipeline determinístico sem LLM.

### Fase 1 — memória funcional
- memória episódica compacta;
- base semântica SQLite/arquivos;
- workflows procedurais com testes;
- busca textual antes de embeddings;
- exportação, backup e exclusão.

### Fase 2 — aprendizado por fontes
- ingestão de poucos documentos por lote;
- extração de texto;
- deduplicação por hash e similaridade textual simples;
- candidatos de afirmação com referência a trechos;
- verificação e revisão antes da promoção.

### Fase 3 — modelo local opcional
- benchmark de 2–3 modelos pequenos/quantizados, um por vez;
- contexto curto, lote pequeno e limite de RAM;
- medir tokens/s, pico de RAM, tempo, temperatura/estabilidade e qualidade;
- interromper se comprometer o uso normal do PC;
- interface substituível; nenhuma dependência rígida de runtime específico.

### Fase 4 — consolidação e sincronização
- janela agendada quando o PC estiver ocioso;
- produzir relatórios/diffs, não aplicar mudanças irreversíveis;
- sincronizar apenas resumos e conhecimento aprovados;
- fila cloud/PC com estado real e tratamento de conflitos.

### Fase 5 — aprendizagem contínua avaliada
- benchmark próprio de perguntas e tarefas;
- testes de regressão antes/depois de cada consolidação;
- análise de erro, drift e conteúdo obsoleto;
- promoção gradual, rollback automático se os critérios falharem.

**Princípio de custo:** R$ 0 obrigatório, sem cartão nem cobrança automática. Recursos gratuitos podem ter limites, mudanças de política ou indisponibilidade. O modo básico deve continuar utilizável quando o PC estiver desligado e quando não houver cota de IA remota.

## 8. Métricas de sucesso

- precisão de extração de afirmações em amostra revisada;
- percentagem de afirmações com proveniência completa;
- taxa de contradições detectadas e não resolvidas;
- taxa de conhecimento obsoleto ainda apresentado como atual;
- regressões em conjunto de testes;
- taxa de workflows reproduzíveis;
- custo e tempo por lote;
- RAM máxima e estabilidade no PC;
- número de atualizações revertidas;
- taxa de ações que exigiram aprovação e foram corretamente bloqueadas.

Não declarar “aprendizado melhorou” sem comparar essas métricas em versões controladas.

## 9. Consenso, debates e propostas

**Bem estabelecido:** plasticidade sináptica é central para aprendizagem; LTP/LTD são fenômenos reais; hipocampo participa da memória episódica; memória depende de sistemas distribuídos; sono contribui para consolidação; astrócitos e outras células gliais participam da regulação cerebral.

**Em debate / em evolução:** quanto cada mecanismo explica tipos específicos de memória; detalhes da contribuição de diferentes fases do sono; interpretações completas dos sinais dopaminérgicos; como diferentes formas de plasticidade interagem em circuitos e comportamentos.

**Propostas de engenharia deste documento:** memórias separadas por finalidade, estados de conhecimento, fila de atenção, avaliação multiobjetivo, consolidação em lote e sincronização seletiva. São decisões de projeto inspiradas na literatura, não mecanismos biológicos comprovadamente equivalentes.

## 10. Referências científicas selecionadas

1. Liao, Z. & Losonczy, A. (2024). *Learning, Fast and Slow: Single- and Many-Shot Learning in the Hippocampus*. Annual Review of Neuroscience. https://doi.org/10.1146/annurev-neuro-102423-100258
2. Della-Maggiore, V. (2024). *The human hippocampus beyond episodic memory*. Nature Reviews Neuroscience. https://www.nature.com/articles/s41583-024-00798-x
3. (2024). *Half a century legacy of long-term potentiation*. Current Biology. https://doi.org/10.1016/j.cub.2024.05.008
4. (2025). *Long-term potentiation in the brain: a synaptic memory mechanism*. Physiological Reviews. https://doi.org/10.1152/physrev.00028.2025
5. Lopez-Ortiz et al. (2024). *Astrocytes and microglia in the coordination of CNS development and homeostasis*. Journal of Neurochemistry. https://doi.org/10.1111/jnc.16006
6. *Essential Role of Astrocytes in Learning and Memory* (2024). International Journal of Molecular Sciences. https://www.mdpi.com/1422-0067/25/3/1899
7. Gershman et al. (2024). *Explaining dopamine through prediction errors and beyond*. Nature Neuroscience. https://www.nature.com/articles/s41593-024-01705-4
8. Kahnt & Schoenbaum (2025). *The curious case of dopaminergic prediction errors and learning associative information beyond value*. Nature Reviews Neuroscience. https://www.nature.com/articles/s41583-024-00898-8
9. Lutz, Harkotte & Born (2026 issue; online publication earlier). *Sleep’s contribution to memory formation*. Physiological Reviews. https://doi.org/10.1152/physrev.00054.2024
10. *Sleep—A brain-state serving systems memory consolidation* (2023). Neuron. https://doi.org/10.1016/j.neuron.2023.03.005
11. *Episodic Memory formation: A review of complex Hippocampus input pathways* (2023). Progress in Neuro-Psychopharmacology & Biological Psychiatry. https://doi.org/10.1016/j.pnpbp.2023.110757
12. *Continual learning: A systematic literature review* (2025). Neural Networks. https://doi.org/10.1016/j.neunet.2025.108

## 11. Glossário

- **LTP:** aumento persistente da eficácia sináptica.
- **LTD:** redução persistente da eficácia sináptica.
- **Plasticidade homeostática:** mecanismos que ajudam a manter atividade neural em faixas funcionais.
- **Metaplasticidade:** mudança na propensão de uma sinapse/rede a sofrer plasticidade.
- **Hipocampo:** estrutura essencial para formação/recuperação de memórias episódicas e relações contextuais.
- **Consolidação:** estabilização e reorganização de memórias ao longo do tempo.
- **Erro de previsão:** diferença entre resultado esperado e observado em um modelo de aprendizagem.
- **Esquecimento catastrófico:** perda de desempenho em conhecimentos anteriores após aprender tarefas novas.
- **Proveniência:** registro de onde uma informação veio e como foi transformada.
- **Calibração:** correspondência entre confiança declarada/estimada e frequência real de acertos.

---
Este documento orienta o desenho futuro do N.E.X.U.S.; não declara qualquer módulo como implementado.
