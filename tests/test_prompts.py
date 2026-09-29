"""
Testes automatizados para validação de prompts.
"""
import pytest
import yaml
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
V2_PATH = PROMPTS_DIR / "bug_to_user_story_v2.yml"
V2_KEY = "bug_to_user_story_v2"


def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def prompt_v2() -> dict:
    """Carrega o prompt otimizado (v2) uma única vez para todos os testes."""
    data = load_prompts(V2_PATH)
    assert data is not None, f"Não foi possível carregar {V2_PATH}"
    assert V2_KEY in data, f"Chave '{V2_KEY}' não encontrada em {V2_PATH}"
    return data[V2_KEY]


class TestPrompts:
    def test_prompt_has_system_prompt(self, prompt_v2):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        assert "system_prompt" in prompt_v2, "Campo 'system_prompt' ausente no prompt"
        assert prompt_v2["system_prompt"].strip() != "", "'system_prompt' está vazio"

    def test_prompt_has_role_definition(self, prompt_v2):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        system_prompt = prompt_v2["system_prompt"].lower()
        role_markers = ["você é um", "você é uma", "product manager", "persona"]
        assert any(marker in system_prompt for marker in role_markers), (
            "Nenhum marcador de definição de persona/role encontrado no system_prompt"
        )

    def test_prompt_mentions_format(self, prompt_v2):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        system_prompt = prompt_v2["system_prompt"].lower()
        format_markers = [
            "markdown",
            "user story",
            "como um",
            "eu quero",
            "para que",
            "critérios de aceitação",
        ]
        assert any(marker in system_prompt for marker in format_markers), (
            "Nenhuma exigência de formato (Markdown ou User Story padrão) encontrada"
        )

    def test_prompt_has_few_shot_examples(self, prompt_v2):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        system_prompt = prompt_v2["system_prompt"]
        system_prompt_lower = system_prompt.lower()

        assert "exemplo" in system_prompt_lower, "Nenhum exemplo (few-shot) encontrado no system_prompt"

        # Precisa ter pelo menos 2 exemplos, cada um com entrada (relato de bug)
        # e saída (resposta esperada) claramente identificados.
        example_count = system_prompt_lower.count("exemplo")
        assert example_count >= 2, (
            f"Esperado pelo menos 2 exemplos few-shot, encontrado(s) {example_count}"
        )
        assert "relato de bug" in system_prompt_lower, "Exemplos não identificam a entrada (relato de bug)"
        assert "resposta esperada" in system_prompt_lower, "Exemplos não identificam a saída esperada"

    def test_prompt_no_todos(self, prompt_v2):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        system_prompt = prompt_v2["system_prompt"]
        user_prompt = prompt_v2.get("user_prompt", "")

        assert "[TODO]" not in system_prompt, "system_prompt ainda contém um [TODO]"
        assert "TODO" not in system_prompt, "system_prompt ainda contém um TODO"
        assert "[TODO]" not in user_prompt, "user_prompt ainda contém um [TODO]"
        assert "TODO" not in user_prompt, "user_prompt ainda contém um TODO"

    def test_minimum_techniques(self, prompt_v2):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        techniques = prompt_v2.get("techniques_applied", [])
        assert len(techniques) >= 2, (
            f"Esperado no mínimo 2 técnicas em 'techniques_applied', encontrado(s) {len(techniques)}"
        )

    def test_prompt_passes_structural_validation(self, prompt_v2):
        """Validação estrutural completa (utils.validate_prompt_structure)."""
        is_valid, errors = validate_prompt_structure(prompt_v2)
        assert is_valid, f"Prompt reprovado na validação estrutural: {errors}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])