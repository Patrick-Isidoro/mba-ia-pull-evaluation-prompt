"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

DICAS DE IMPLEMENTAÇÃO:

- O push é feito pelo cliente do LangSmith:

      from langsmith import Client
      from langchain_core.prompts import ChatPromptTemplate

      client = Client()
      prompt = ChatPromptTemplate.from_messages([
          ("system", system_prompt),
          ("user", user_prompt),
      ])
      url = client.push_prompt(
          f"{username}/bug_to_user_story_v2",
          object=prompt,
          is_public=True,
          description="...",
          tags=[...],
      )

- `username` vem de USERNAME_LANGSMITH_HUB no .env e precisa ser o seu handle
  do Hub. Se você ainda não tem um handle, veja as instruções no .env.example.

- A variável do template precisa ser {bug_report}, que é a chave de entrada
  usada no dataset de avaliação.

- Use `load_yaml` de utils.py para ler o arquivo .yml.
"""

import os
import sys
from dotenv import load_dotenv
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header, validate_prompt_structure

load_dotenv()

PROMPTS_PATH = "prompts/bug_to_user_story_v2.yml"


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do prompt (chave do YAML, ex: "bug_to_user_story_v2")
        prompt_data: Dados do prompt

    Returns:
        True se sucesso, False caso contrário
    """
    is_valid, errors = validate_prompt(prompt_data)

    if not is_valid:
        print(f"❌ Prompt '{prompt_name}' reprovado na validação:")
        for error in errors:
            print(f"   - {error}")
        return False

    username = os.getenv("USERNAME_LANGSMITH_HUB")
    if not username:
        print("❌ USERNAME_LANGSMITH_HUB não configurado no .env")
        return False

    system_prompt = prompt_data["system_prompt"]
    user_prompt = prompt_data.get("user_prompt") or "{bug_report}"

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", user_prompt),
    ])

    full_name = f"{username}/{prompt_name}"
    description = prompt_data.get("description", "")
    techniques = prompt_data.get("techniques_applied", [])
    tags = list(prompt_data.get("tags", []))
    tags += [f"technique:{technique}" for technique in techniques]

    print(f"Fazendo push de '{full_name}'...")

    try:
        client = Client()
        url = client.push_prompt(
            full_name,
            object=prompt,
            is_public=True,
            description=description,
            tags=tags,
        )
        print(f"   ✓ Push concluído: {url}")
        return True
    except Exception as e:
        print(f"❌ Erro ao fazer push de '{full_name}': {e}")
        return False


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    return validate_prompt_structure(prompt_data)


def main():
    """Função principal"""
    print_section_header("PUSH DE PROMPTS OTIMIZADOS PARA O LANGSMITH HUB")

    required_vars = ["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]
    if not check_env_vars(required_vars):
        return 1

    all_prompts = load_yaml(PROMPTS_PATH)

    if not all_prompts:
        print(f"❌ Não foi possível carregar prompts de: {PROMPTS_PATH}")
        return 1

    all_success = True

    for prompt_key, prompt_data in all_prompts.items():
        success = push_prompt_to_langsmith(prompt_key, prompt_data)
        all_success = all_success and success

    if all_success:
        username = os.getenv("USERNAME_LANGSMITH_HUB")
        print("\n✅ Todos os prompts foram publicados com sucesso!")
        print("\nPróximos passos:")
        print(f"1. Confirme em https://smith.langchain.com/prompts que {username}/... está público")
        print("2. Execute a avaliação: python src/evaluate.py")
        return 0

    print("\n❌ Alguns prompts falharam ao publicar. Veja os erros acima.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
