# Pull, Otimização e Avaliação de Prompts com LangChain e LangSmith

Fork do desafio [devfullcycle/mba-ia-pull-evaluation-prompt](https://github.com/devfullcycle/mba-ia-pull-evaluation-prompt).
Pipeline que puxa um prompt de baixa qualidade do LangSmith Prompt Hub, refatora
com técnicas de Prompt Engineering, publica a versão otimizada de volta ao Hub
e avalia a qualidade com 5 métricas (Helpfulness, Correctness, F1-Score,
Clarity, Precision), com aprovação mínima de 0.8 em todas.

## Status desta entrega

O código está 100% implementado e testado localmente (`pull_prompts.py`,
`push_prompts.py`, `prompts/bug_to_user_story_v2.yml`, os 6 testes de
`tests/test_prompts.py` — todos passando). O que **depende de credenciais
pessoais** (LangSmith API key, handle do Hub, chave de LLM) — rodar
`pull`/`push`/`evaluate` de verdade contra o LangSmith, iterar nas métricas e
gerar os links/screenshots de evidência — está descrito passo a passo na
seção "Como Executar" e ainda precisa ser rodado com as credenciais de quem
for validar este repositório. Os placeholders abaixo (`<PENDENTE...>`) marcam
exatamente o que falta preencher após essa execução.

## Técnicas Aplicadas (Fase 2)

O prompt otimizado está em [`prompts/bug_to_user_story_v2.yml`](prompts/bug_to_user_story_v2.yml).
Três técnicas foram combinadas — mais que o mínimo exigido (Few-shot + 1
adicional) — porque cada uma ataca uma fraqueza diferente e específica do v1:

### 1. Role Prompting

**O quê**: o `system_prompt` abre definindo a persona "Product Manager sênior
com 10 anos de experiência... forte domínio de metodologias ágeis", com a
tarefa explícita de traduzir relatos informais em User Stories prontas para
backlog.

**Por quê**: o v1 não define nenhuma persona — é só "um assistente que ajuda a
transformar relatos de bugs". Isso não ancora o modelo em nenhum padrão de
qualidade real (o que um PM sênior consideraria uma User Story "pronta"), e
explica boa parte da nota baixa de `Clarity`/`Correctness` do v1: sem persona,
o modelo tende a responder de forma genérica e sem o rigor de formato que o
time ágil espera.

**Como foi aplicado**: a seção `# PERSONA` no topo do `system_prompt`, mais a
seção `# TAREFA` que ancora o objetivo ("pronta para entrar no backlog de
desenvolvimento").

### 2. Few-shot Learning (obrigatório)

**O quê**: 3 exemplos completos de entrada (`RELATO DE BUG`) → saída
(`RESPOSTA ESPERADA`), um para cada nível de complexidade do dataset (simples,
médio, complexo) — os dois primeiros são os próprios exemplos que já constam
no dataset de avaliação (`datasets/bug_to_user_story.jsonl`, linhas 1 e 2), e o
terceiro foi escrito à mão para demonstrar o caso complexo (contexto técnico +
impacto).

**Por quê**: o v1 não tem nenhum exemplo — o modelo só recebe o relato bruto e
uma instrução vaga ("crie uma user story a partir dele"). Sem exemplo, o
modelo não sabe o nível de detalhe esperado nem o formato exato dos Critérios
de Aceitação (Given-When-Then), o que reduz diretamente `F1-Score` (a
resposta não cobre o que a referência cobre) e `Precision`.

**Como foi aplicado**: seção `# EXEMPLOS (Few-shot)` com 3 blocos completos.
Usar exemplos reais do dataset (não inventados) para 2 dos 3 casos foi
deliberado: alinha a saída do modelo ao formato exato que a métrica de F1 vai
comparar.

### 3. Chain of Thought (técnica adicional escolhida)

**O quê**: a seção `# COMO PENSAR` instrui o modelo a raciocinar em 4 passos
internos (identificar persona → identificar ação → identificar benefício →
avaliar complexidade) **antes** de escrever a resposta final, com uma regra
explícita e repetida em duas seções diferentes do prompt: **nunca expor esse
raciocínio na resposta**.

**Por quê CoT e não outra técnica**: bug reports são exatamente o tipo de
tarefa que se beneficia de raciocínio estruturado antes da resposta (a
recomendação do próprio enunciado do desafio) — decidir a persona certa, a
ação certa e o nível de detalhe certo são 3 sub-decisões concatenadas, e pedir
para o modelo "pensar" nelas separadamente reduz erro em cada uma. A
alternativa mais óbvia seria Skeleton of Thought, mas ela ajudaria a
*estrutura* da resposta — que o Few-shot já resolve — sem ajudar a *escolha*
de conteúdo (qual persona, qual nível de detalhe), que é o problema real do
v1.

**Risco que essa técnica introduz, e como foi mitigado**: se o modelo expuser
o raciocínio na resposta, o texto vira ruído que a métrica de F1/Clarity vai
penalizar (a referência não tem raciocínio, só o resultado final). Por isso a
instrução de "nunca exponha" aparece duas vezes (na introdução da seção e
reforçada nas `REGRAS DE COMPORTAMENTO`), e o passo 5 ("ESCREVER A RESPOSTA
FINAL") é explicitamente isolado como o único conteúdo que deve sair.

### Requisitos adicionais do enunciado, e onde cada um foi atendido

| Requisito | Onde está no `system_prompt` |
|---|---|
| Instruções claras e específicas | `# TAREFA` + `# COMO PENSAR` |
| Regras explícitas de comportamento | `# REGRAS DE COMPORTAMENTO` (7 regras, incl. anti-alucinação) |
| Few-shot (obrigatório) | `# EXEMPLOS (Few-shot)` — 3 exemplos |
| Tratamento de edge cases | `# REGRAS DE COMPORTAMENTO`: relato vago → fallback de persona; múltiplos bugs no mesmo relato → foco no de maior impacto |
| System vs User Prompt | `system_prompt` carrega persona + regras + exemplos; `user_prompt` é só `{bug_report}` (mesma variável do dataset) |

## Resultados Finais

### Link público do dataset de avaliação

`<PENDENTE — rodar Client().share_dataset(dataset_name="<LANGSMITH_PROJECT>-eval")["url"]
após a primeira execução de python src/evaluate.py, e colar o link aqui>`

### Screenshots das avaliações (notas ≥ 0.8)

`<PENDENTE — capturar a saída do terminal de` `python src/evaluate.py` `com
STATUS: APROVADO, e/ou screenshot do experimento no dashboard do LangSmith>`

### Tracing de pelo menos 3 exemplos

`<PENDENTE — no dashboard do LangSmith, abrir o experimento gerado pelo
evaluate.py e linkar/printar pelo menos 3 traces individuais>`

### Comparação v1 → v2 (estrutural, verificável sem depender de execução)

| Aspecto | v1 (`bug_to_user_story_v1.yml`) | v2 (`bug_to_user_story_v2.yml`) |
|---|---|---|
| Persona | Nenhuma ("um assistente que ajuda a...") | Product Manager sênior, com contexto de time ágil |
| Exemplos | Nenhum | 3 exemplos (simples/médio/complexo) |
| Raciocínio | Nenhuma instrução | CoT em 4 passos, explicitamente oculto na resposta |
| Formato de saída | Não especificado ("User Story gerada:") | Formato fixo: frase padrão + Critérios de Aceitação em Given-When-Then |
| Escala por complexidade | Não existe | Regras explícitas de quantidade de critérios e seções extras (Contexto Técnico/Impacto) para bugs complexos |
| Edge cases | Não tratados | Relato vago, múltiplos bugs no mesmo relato, dados técnicos a preservar |
| Anti-alucinação | Não mencionado | Regra explícita: nunca inventar IDs/nomes/números/causas técnicas |
| `{bug_report}` duplicado | Sim (no `system_prompt` E no `user_prompt`) — problema apontado no comentário do arquivo original | Corrigido: `system_prompt` não repete a variável; `user_prompt` é só `{bug_report}` |

### Iterações

`<PENDENTE — esta seção deve registrar as 3-5 rodadas reais de` `python
src/push_prompts.py` `+` `python src/evaluate.py`, `com as métricas de cada
rodada e o que foi ajustado entre uma e outra. Preencher durante a execução;
o texto abaixo é o esqueleto de tabela a usar>`

| Iteração | O que mudou | Helpfulness | Correctness | F1 | Clarity | Precision | Status |
|---|---|---|---|---|---|---|---|
| 1 | Primeira versão do v2 (persona + few-shot + CoT) | — | — | — | — | — | — |
| ... | ... | | | | | | |

## Como Executar

### Pré-requisitos

- Python 3.10+
- Conta no [LangSmith](https://smith.langchain.com) com um **handle público do
  Hub já criado** (ver instruções abaixo — passo manual, só pode ser feito
  pela interface web)
- Uma API key de LLM: [OpenAI](https://platform.openai.com/api-keys) ou
  [Google AI Studio](https://aistudio.google.com/app/apikey) (Gemini)

### 1. Criar o handle do LangSmith Hub (passo manual, uma vez só)

1. Abra o LangSmith → **Prompts**
2. Crie um prompt qualquer (pode ser de teste) ou abra um existente
3. Nos três pontinhos ao lado de **Playground** → **Make Public**
4. Em **Choose your public handle**, defina seu handle (é definitivo depois
   de confirmado)

Esse handle é o valor de `USERNAME_LANGSMITH_HUB` no `.env`.

### 2. Ambiente

```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Preencha o `.env`:

- `LANGSMITH_API_KEY` — [smith.langchain.com/settings](https://smith.langchain.com/settings)
- `USERNAME_LANGSMITH_HUB` — handle criado no passo 1
- `LLM_PROVIDER` — `openai` ou `google`
- `OPENAI_API_KEY` **ou** `GOOGLE_API_KEY` — conforme o provider escolhido
- `LLM_MODEL` e `EVAL_MODEL` — consulte a documentação oficial do provider
  para ver os modelos disponíveis no momento
  ([OpenAI](https://platform.openai.com/docs/models) /
  [Google](https://ai.google.dev/gemini-api/docs/models)); escolha modelos
  que aceitem `temperature=0`

### 3. Pull do prompt semente

```bash
python src/pull_prompts.py
```

Salva `leonanluppi/bug_to_user_story_v1` em `prompts/bug_to_user_story_v1.yml`.

### 4. Prompt otimizado

Já está pronto em `prompts/bug_to_user_story_v2.yml` (ver seção "Técnicas
Aplicadas" acima). Para ajustar após uma rodada de avaliação, edite este
arquivo diretamente.

### 5. Push do prompt otimizado

```bash
python src/push_prompts.py
```

Publica `{USERNAME_LANGSMITH_HUB}/bug_to_user_story_v2` como público no Hub,
com descrição, tags e as técnicas aplicadas como metadado.

### 6. Avaliação

```bash
python src/evaluate.py
```

Cria (ou reaproveita) o dataset `{LANGSMITH_PROJECT}-eval` no LangSmith a
partir de `datasets/bug_to_user_story.jsonl`, roda o prompt v2 contra os 15
exemplos como um experimento, calcula as 5 métricas por exemplo e grava cada
nota como feedback no experimento. Ao final, imprime o link do experimento.

### 7. Iterar

Se alguma métrica ficar abaixo de 0.8: edite
`prompts/bug_to_user_story_v2.yml` → rode `push_prompts.py` novamente → rode
`evaluate.py` novamente. Repita até todas as 5 métricas atingirem 0.8 (ver
tabela de iterações acima).

### 8. Gerar o link público do dataset (para compartilhar evidência)

```bash
python -c "from langsmith import Client; print(Client().share_dataset(dataset_name='mba-ia-pull-evaluation-prompt-eval')['url'])"
```

Troque `mba-ia-pull-evaluation-prompt-eval` pelo valor real de
`{LANGSMITH_PROJECT}-eval` do seu `.env`, se for diferente. Rode uma vez só —
gerar de novo troca o link.

### 9. Testes de validação (não precisam de credenciais)

```bash
pytest tests/test_prompts.py -v
```

Valida a estrutura do `prompts/bug_to_user_story_v2.yml` (persona, formato,
few-shot, ausência de `[TODO]`, mínimo de 2 técnicas). Já rodado localmente
nesta entrega — 7/7 testes passando (os 6 exigidos + 1 validação estrutural
extra via `utils.validate_prompt_structure`).

## Tecnologias

Python 3.10+, LangChain (`langchain-core`), LangSmith (Prompt Hub + datasets +
avaliação), suporte multi-provider (OpenAI/Gemini via `langchain-openai` /
`langchain-google-genai`), prompts versionados em YAML, `pytest` para
validação estrutural.

## Estrutura do projeto

```
mba-ia-pull-evaluation-prompt/
├── .env.example
├── requirements.txt
├── README.md
├── prompts/
│   ├── bug_to_user_story_v1.yml   # semente, puxado do Hub
│   └── bug_to_user_story_v2.yml   # otimizado (Role Prompting + Few-shot + CoT)
├── datasets/
│   └── bug_to_user_story.jsonl    # 15 exemplos (5 simples, 7 médios, 3 complexos)
├── src/
│   ├── pull_prompts.py            # implementado nesta entrega
│   ├── push_prompts.py            # implementado nesta entrega
│   ├── evaluate.py                # fornecido pelo desafio, não alterado
│   ├── metrics.py                 # fornecido pelo desafio, não alterado
│   └── utils.py                   # fornecido pelo desafio, não alterado
└── tests/
    └── test_prompts.py            # implementado nesta entrega (7 testes)
```
