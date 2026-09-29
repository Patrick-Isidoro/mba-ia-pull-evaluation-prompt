"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull do prompt semente do desafio
3. Salva localmente em prompts/bug_to_user_story_v1.yml

DICAS DE IMPLEMENTAÇÃO:

- O pull é feito pelo cliente do LangSmith:

      from langsmith import Client
      client = Client()
      prompt = client.pull_prompt(
          "leonanluppi/bug_to_user_story_v1",
          dangerously_pull_public_prompt=True,
      )

- O parâmetro `dangerously_pull_public_prompt=True` é obrigatório sempre que o
  identificador tem dono explícito ("owner/nome"). O LangSmith bloqueia esse pull
  por padrão porque um prompt do Hub é um objeto LangChain serializado, que pode
  vir de terceiros. Aqui o prompt é o do desafio, então o risco é conhecido.

- O retorno é um ChatPromptTemplate. Para extrair o conteúdo das mensagens,
  use a serialização nativa do LangChain (`prompt.messages`, e o atributo
  `.prompt.template` de cada mensagem).

- Use `save_yaml` de utils.py para gravar o resultado no arquivo .yml.
"""

import os
import sys
from datetime import date
from pathlib import Path
from dotenv import load_dotenv
from langsmith import Client
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()

SEED_PROMPT_ID = "leonanluppi/bug_to_user_story_v1"
OUTPUT_PATH = "prompts/bug_to_user_story_v1.yml"


def pull_prompts_from_langsmith() -> bool:
    """
    Conecta ao LangSmith, faz pull do prompt semente do desafio e salva o
    resultado em prompts/bug_to_user_story_v1.yml.

    Returns:
        True se sucesso, False caso contrário
    """
    client = Client()

    print(f"Puxando prompt do LangSmith Hub: {SEED_PROMPT_ID}")

    try:
        prompt = client.pull_prompt(
            SEED_PROMPT_ID,
            dangerously_pull_public_prompt=True,
        )
    except Exception as e:
        print(f"❌ Erro ao puxar prompt '{SEED_PROMPT_ID}': {e}")
        return False

    system_prompt = ""
    user_prompt = ""

    for message in prompt.messages:
        message_type = message.__class__.__name__
        template = getattr(message.prompt, "template", "")

        if "System" in message_type:
            system_prompt = template
        elif "Human" in message_type:
            user_prompt = template

    if not system_prompt:
        print("❌ Não foi possível extrair o system_prompt do objeto retornado pelo LangSmith")
        return False

    prompt_data = {
        "bug_to_user_story_v1": {
            "description": "Prompt para converter relatos de bugs em User Stories (versão original, baixa qualidade)",
            "system_prompt": system_prompt,
            "user_prompt": user_prompt or "{bug_report}",
            "version": "v1",
            "created_at": date.today().isoformat(),
            "source": SEED_PROMPT_ID,
            "tags": ["bug-analysis", "user-story", "product-management"],
        }
    }

    print(f"Salvando prompt em: {OUTPUT_PATH}")
    return save_yaml(prompt_data, OUTPUT_PATH)


def main():
    """Função principal"""
    print_section_header("PULL DE PROMPTS DO LANGSMITH HUB")

    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return 1

    success = pull_prompts_from_langsmith()

    if success:
        print(f"\n✅ Pull concluído com sucesso! Arquivo salvo em: {OUTPUT_PATH}")
        print("\nPróximos passos:")
        print("1. Analise o prompt em prompts/bug_to_user_story_v1.yml")
        print("2. Crie a versão otimizada em prompts/bug_to_user_story_v2.yml")
        return 0

    print("\n❌ Falha ao puxar prompts do LangSmith. Veja o erro acima.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
