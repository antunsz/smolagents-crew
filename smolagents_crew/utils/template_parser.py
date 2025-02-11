from string import Formatter
from typing import List, Dict

class TemplateValidator:
    @staticmethod
    def get_required_vars(template: str) -> List[str]:
        """Extrai variáveis necessárias de um template"""
        return [fn for _, fn, _, _ in Formatter().parse(template) if fn is not None]

    @staticmethod
    def validate_context(template: str, context: dict) -> bool:
        """Valida se o contexto possui todas as variáveis necessárias"""
        required = TemplateValidator.get_required_vars(template)
        return all(var in context for var in required)

def parse_template(template: str, context: Dict = None) -> Dict:
    """Parse a template string and optionally validate its context.

    Args:
        template (str): The template string to parse.
        context (Dict, optional): The context dictionary to validate against.

    Returns:
        Dict: A dictionary containing the required variables and validation status.
    """
    validator = TemplateValidator()
    required_vars = validator.get_required_vars(template)
    result = {"required_vars": required_vars}
    
    if context is not None:
        result["is_valid"] = validator.validate_context(template, context)
    
    return result