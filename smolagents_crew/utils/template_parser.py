from string import Formatter

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