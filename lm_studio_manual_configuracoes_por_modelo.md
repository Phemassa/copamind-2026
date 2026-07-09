# LM Studio — Manual de Configurações por Modelo

Este documento consolida as configurações visíveis nas telas do **LM Studio / Aba Inference** para servir como base de manual e parametrização por modelo.

---

## 1. Context and Offload

> Observação: as duas primeiras telas enviadas possuem os mesmos valores.

| Campo | Valor na tela | Observação para manual |
|---|---:|---|
| Context Length | `8192` | Janela de contexto usada na inferência. Pode ser aumentada conforme VRAM/RAM disponível. |
| Model supports up to | `262144 tokens` | Limite máximo suportado pelo modelo carregado. |
| GPU Offload | `0` | Quantidade de camadas enviadas para GPU. `0` indica sem offload de camadas para GPU. |

---

## 2. Advanced

| Campo | Valor / Estado | Observação para manual |
|---|---:|---|
| CPU Thread Pool Size | `9` | Número de threads de CPU usadas pelo runtime. |
| Evaluation Batch Size | `2048` | Tamanho do lote de avaliação. Impacta velocidade e uso de memória. |
| Physical Batch Size | `512` | Tamanho físico real do batch processado. |
| Max Concurre... | `4` | Campo truncado na tela. Provavelmente relacionado a concorrência máxima. |
| Unified KV Cache | Ativado | Usa cache KV unificado. |
| RoPE Frequency Base | Auto | Configuração automática, checkbox desmarcado. |
| RoPE Frequency Scale | Auto | Configuração automática, checkbox desmarcado. |
| Offload KV Cache to GPU Memory | Ativado | Envia KV Cache para memória da GPU. |
| Keep Model in Memory | Ativado | Mantém o modelo carregado na memória. |
| Try mmap() | Ativado | Usa mmap para carregar o modelo de forma mais eficiente. |
| Seed | Random Seed | Checkbox desmarcado, usando seed aleatória. |
| Number of Experts | `8` | Número de experts ativos, relevante para modelos MoE. |
| Number of lay... | `0` | Campo truncado. Provavelmente relacionado ao número de layers/camadas. |
| Flash Attention | Ativado | Otimização de atenção para performance/memória. |
| K Cache Quantization Type | Desativado | Experimental. Sem quantização do K Cache. |
| V Cache Quantization Type | Desativado | Experimental. Sem quantização do V Cache. |

---

## 3. System Prompt

| Campo | Valor / Estado |
|---|---|
| System Prompt | Vazio |
| Placeholder exibido | `Example, "Only answer in rhymes"` |
| Token count | `N/A` |

### Uso recomendado no manual

```text
System Prompt:
[Inserir aqui instruções fixas do modelo, persona, regras de resposta, idioma, formato de saída e restrições.]
```

### Exemplo para modelos de código

```text
Você é um agente especializado em análise, modernização e conversão de código legado.
Responda sempre em português do Brasil.
Priorize explicações objetivas, rastreabilidade técnica, riscos e próximos passos.
```

---

## 4. Custom Fields

| Campo | Valor / Estado | Observação |
|---|---|---|
| Enable Thinking | Ativado | Controla se o modelo deve pensar antes de responder. |
| Preserve Thinking | Desativado | Não preserva o raciocínio de turnos anteriores, apenas o mais recente. |

Texto exibido na tela:

```text
Enable Thinking
Controls whether the model will think before replying

Preserve Thinking
Preserve reasoning content in all prior assistant turns instead of only the most recent one
```

---

## 5. Settings

| Campo | Valor / Estado | Observação |
|---|---:|---|
| Temperature | `0.6` | Controla criatividade/variação. |
| Limit Response Length | Desativado | Sem limite explícito de resposta. |
| Context Overflow | `Truncate Middle` | Quando o contexto excede o limite, remove conteúdo do meio. |
| Stop Strin... | Vazio | Campo para strings de parada. |
| CPU Threads | `9` | Threads de CPU usadas na inferência. |

### Referência de temperature

```text
Temperature:
- 0.1 a 0.3: respostas mais determinísticas, ideal para código, análise técnica e documentação.
- 0.4 a 0.7: equilíbrio entre precisão e flexibilidade.
- 0.8+: respostas mais criativas, menos recomendadas para código crítico.
```

---

## 6. Reasoning Parsing

| Campo | Valor / Estado |
|---|---|
| Reasoning Section Parsing | Ativado |
| Start String | `<think>` |
| End String | `</think>` |

### Uso no manual

```text
Reasoning Parsing:
Usado para identificar blocos de raciocínio interno do modelo quando o modelo retorna conteúdo entre tags como <think> e </think>.
```

---

## 7. Sampling

| Campo | Valor / Estado | Observação |
|---|---:|---|
| Top K Sampling | `20` | Limita a seleção aos 20 tokens mais prováveis. |
| Repeat Penalty | Desativado | Penalização de repetição não aplicada. |
| Presence Penalty | Desativado | Penalização por presença não aplicada. |
| Top P Sampling | Ativado / `0.95` | Amostragem nucleus habilitada. |
| Min P Sampling | Desativado | Min-P não aplicado. |

### Sugestão para modelos técnicos

```text
Sampling recomendado para modelos técnicos:
Top K: 20 a 40
Top P: 0.90 a 0.95
Temperature: 0.3 a 0.6
Repeat Penalty: ativar apenas se o modelo repetir muito
```

---

## 8. Structured Output

| Campo | Valor / Estado |
|---|---|
| Structured Output | Desativado |

### Uso no manual

```text
Structured Output:
Ativar quando for necessário forçar saída em JSON, schema, tabelas ou formatos rígidos.
```

---

## 9. Speculative Decoding

| Campo | Valor / Estado |
|---|---|
| Draft Model | Nenhum selecionado |
| Placeholder | `Select a compatible draft model` |
| Link exibido | `Read how it works` |

### Uso no manual

```text
Speculative Decoding:
Permite usar um modelo menor como draft model para acelerar a geração de respostas, desde que compatível com o modelo principal.
```

---

## 10. Prompt Template

| Campo | Valor / Estado |
|---|---|
| Prompt Template | Modo `Template (Jinja)` selecionado |
| Manual | Aba alternativa disponível |
| Additional Stop ... | Campo vazio |

Trecho visível do template:

```jinja
{%- set image_count = namespace(value=0) %}
{%- set video_count = namespace(value=0) %}
{%- macro render_content(content,
do_vision_count,
```

### Uso no manual

```text
Prompt Template:
Define como as mensagens do usuário, sistema, histórico, imagens e vídeos são empacotados antes de serem enviados ao modelo.
Normalmente deve ser mantido no template padrão do modelo, salvo quando houver necessidade de customização avançada.
```

---

# Configuração-base transcrita das telas

```yaml
context_and_offload:
  context_length: 8192
  model_supports_up_to_tokens: 262144
  gpu_offload: 0

advanced:
  cpu_thread_pool_size: 9
  evaluation_batch_size: 2048
  physical_batch_size: 512
  max_concurrent: 4
  unified_kv_cache: enabled
  rope_frequency_base: auto
  rope_frequency_scale: auto
  offload_kv_cache_to_gpu_memory: enabled
  keep_model_in_memory: enabled
  try_mmap: enabled
  seed: random
  number_of_experts: 8
  number_of_layers: 0
  flash_attention: enabled
  k_cache_quantization_type: disabled
  v_cache_quantization_type: disabled

system_prompt:
  value: empty
  token_count: n/a

custom_fields:
  enable_thinking: enabled
  preserve_thinking: disabled

settings:
  temperature: 0.6
  limit_response_length: disabled
  context_overflow: truncate_middle
  stop_string: empty
  cpu_threads: 9

reasoning_parsing:
  reasoning_section_parsing: enabled
  start_string: "<think>"
  end_string: "</think>"

sampling:
  top_k_sampling: 20
  repeat_penalty: disabled
  presence_penalty: disabled
  top_p_sampling:
    enabled: true
    value: 0.95
  min_p_sampling: disabled

structured_output:
  enabled: false

speculative_decoding:
  draft_model: none_selected

prompt_template:
  mode: template_jinja
  additional_stop: empty
```

---

# Template de ficha por modelo

Use este padrão para documentar cada modelo testado no LM Studio.

```markdown
# Modelo: [Nome do modelo]

## Perfil de uso

- Finalidade:
- Tamanho:
- Tipo:
- Quantização:
- Suporta reasoning:
- Suporta visão:
- Suporta tool/function calling:
- Contexto máximo suportado:
- Melhor uso:
- Evitar para:

---

## Configuração LM Studio

### Context and Offload

| Campo | Valor |
|---|---:|
| Context Length | |
| Model supports up to | |
| GPU Offload | |

### Advanced

| Campo | Valor |
|---|---:|
| CPU Thread Pool Size | |
| Evaluation Batch Size | |
| Physical Batch Size | |
| Max Concurrent | |
| Unified KV Cache | |
| RoPE Frequency Base | |
| RoPE Frequency Scale | |
| Offload KV Cache to GPU Memory | |
| Keep Model in Memory | |
| Try mmap() | |
| Seed | |
| Number of Experts | |
| Number of Layers | |
| Flash Attention | |
| K Cache Quantization Type | |
| V Cache Quantization Type | |

### System Prompt

```text
[System prompt usado para este modelo]
```

### Custom Fields

| Campo | Valor |
|---|---|
| Enable Thinking | |
| Preserve Thinking | |

### Settings

| Campo | Valor |
|---|---:|
| Temperature | |
| Limit Response Length | |
| Context Overflow | |
| Stop Strings | |
| CPU Threads | |

### Reasoning Parsing

| Campo | Valor |
|---|---|
| Reasoning Section Parsing | |
| Start String | |
| End String | |

### Sampling

| Campo | Valor |
|---|---:|
| Top K Sampling | |
| Repeat Penalty | |
| Presence Penalty | |
| Top P Sampling | |
| Min P Sampling | |

### Structured Output

| Campo | Valor |
|---|---|
| Structured Output | |
| Schema esperado | |

### Speculative Decoding

| Campo | Valor |
|---|---|
| Draft Model | |
| Compatibilidade | |
| Ganho esperado | |

### Prompt Template

| Campo | Valor |
|---|---|
| Template | |
| Customizações | |
| Additional Stop Strings | |

---

## Observações de execução

- Performance percebida:
- Uso de RAM:
- Uso de VRAM:
- Tempo médio de resposta:
- Qualidade de resposta:
- Problemas encontrados:
- Ajustes recomendados:
```

---

# Guia rápido de perfis de configuração

## Perfil 1 — Código, análise técnica e modernização

Indicado para:
- COBOL para PySpark
- COBOL para .NET
- análise de dependências
- documentação técnica
- refatoração
- geração de testes

```yaml
temperature: 0.2-0.4
top_p: 0.90-0.95
top_k: 20-40
context_length: o_maior_possivel_sem_estourar_memoria
enable_thinking: true
preserve_thinking: false
flash_attention: true
keep_model_in_memory: true
structured_output: opcional
```

Recomendação:
- Usar temperatura baixa para reduzir alucinação.
- Usar contexto alto quando o modelo precisar analisar arquivos longos.
- Ativar Structured Output quando o agente exigir JSON, plano, checklist ou schema.

---

## Perfil 2 — Conversa geral e brainstorming

Indicado para:
- ideação
- prompts
- narrativas
- explicações menos rígidas
- criação de conteúdo

```yaml
temperature: 0.6-0.8
top_p: 0.95
top_k: 20-50
enable_thinking: opcional
structured_output: false
```

Recomendação:
- Temperatura maior aumenta criatividade.
- Menos indicado para transformação crítica de código.

---

## Perfil 3 — Resposta determinística / produção

Indicado para:
- agentes automatizados
- pipelines
- respostas padronizadas
- classificação
- extração de dados
- validação

```yaml
temperature: 0.0-0.2
top_p: 0.80-0.90
top_k: 10-20
structured_output: true
limit_response_length: opcional
stop_strings: conforme_template
enable_thinking: true_para_modelos_reasoning
preserve_thinking: false
```

Recomendação:
- Usar Structured Output quando o consumidor for outro agente/sistema.
- Definir schema quando possível.
- Usar stop strings apenas quando necessário para evitar cortes indevidos.

---

## Perfil 4 — Modelos MoE

Indicado para modelos com experts, como arquiteturas Mixture of Experts.

```yaml
number_of_experts: conforme_recomendacao_do_modelo
temperature: 0.3-0.6
top_p: 0.90-0.95
top_k: 20
flash_attention: true
offload_kv_cache_to_gpu_memory: true
```

Recomendação:
- Não alterar Number of Experts sem comparar qualidade e performance.
- Testar variações por modelo.
- Monitorar uso de RAM/VRAM.

---

# Checklist para cadastro de novo modelo

Antes de liberar um modelo para uso em agente, preencher:

```markdown
## Checklist do modelo

- [ ] Nome e versão do modelo registrados
- [ ] Quantização registrada
- [ ] Contexto máximo validado
- [ ] Configuração de GPU Offload testada
- [ ] Configuração de CPU Threads testada
- [ ] Flash Attention validado
- [ ] KV Cache validado
- [ ] Thinking habilitado/desabilitado conforme tipo do modelo
- [ ] Reasoning Parsing validado com tags corretas
- [ ] Sampling definido
- [ ] Temperature definida por perfil de uso
- [ ] Structured Output testado, se aplicável
- [ ] Prompt Template mantido ou customizado
- [ ] Teste com prompt curto realizado
- [ ] Teste com prompt longo realizado
- [ ] Teste com código/documento realizado
- [ ] Métricas básicas registradas
- [ ] Problemas conhecidos documentados
```

---

# Campos para benchmark por modelo

```markdown
# Benchmark do modelo: [Nome]

## Ambiente

- Máquina:
- CPU:
- RAM:
- GPU:
- VRAM:
- Sistema operacional:
- LM Studio versão:
- Runtime/backend:
- Modelo:
- Quantização:
- Tamanho do arquivo:

## Configuração

- Context Length:
- GPU Offload:
- CPU Threads:
- Batch Size:
- Flash Attention:
- KV Cache GPU:
- Temperature:
- Top P:
- Top K:
- Thinking:
- Structured Output:

## Testes

### Teste 1 — Prompt curto

- Prompt:
- Tempo até primeiro token:
- Tokens por segundo:
- Qualidade:
- Observações:

### Teste 2 — Código

- Prompt:
- Tempo até primeiro token:
- Tokens por segundo:
- Qualidade:
- Erros:
- Observações:

### Teste 3 — Contexto longo

- Prompt:
- Tamanho aproximado do contexto:
- Tempo até primeiro token:
- Tokens por segundo:
- Qualidade:
- Perdeu contexto? Sim/Não
- Observações:

## Resultado final

- Nota geral:
- Melhor uso:
- Limitações:
- Configuração recomendada:
```

---

# Observações importantes

1. **Context Length alto aumenta consumo de memória.**  
   Mesmo que o modelo suporte `262144 tokens`, nem sempre a máquina suporta esse contexto com boa performance.

2. **GPU Offload em `0` significa que as camadas do modelo não estão sendo enviadas para GPU.**  
   Em máquinas com GPU dedicada, normalmente vale testar offload maior, respeitando a VRAM.

3. **Offload KV Cache to GPU Memory ajuda performance, mas consome VRAM.**

4. **Flash Attention geralmente deve ficar ativado quando suportado.**

5. **Thinking deve ser usado com cuidado em agentes.**  
   Pode melhorar raciocínio, mas pode aumentar latência e consumo de tokens.

6. **Preserve Thinking tende a aumentar contexto usado.**  
   Para agentes longos, pode consumir janela de contexto rapidamente.

7. **Structured Output deve ser ativado quando outro sistema depende do formato da resposta.**

8. **Prompt Template deve ser alterado apenas quando houver clareza do formato esperado pelo modelo.**

---

# Próximo passo recomendado

Criar uma ficha individual para cada modelo instalado no LM Studio, por exemplo:

```markdown
- Gemma 4 12B QAT
- Gemma 4 26B A4B QAT
- Gemma 4 31B QAT
- Qwen3.6 27B
- Qwen3.6 35B A3B
- Nemotron Nano V3 Omni
- Text Embedding Nomic Embed Text v1.5
```

Cada ficha deve conter:
- objetivo do modelo;
- configuração LM Studio;
- resultado de benchmark;
- melhor uso em agentes;
- limitações conhecidas.
