"""
Integração com Groq API para extrair dados estruturados das mensagens.
Usa Llama 3.3 70B com JSON mode para garantir saída válida.
"""
import os
import json
import logging
from groq import Groq

logger = logging.getLogger(__name__)

# Cliente é criado sob demanda (lazy) pra evitar erro no import
# caso a env var ainda não esteja carregada.
_client = None


def get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY não definida no ambiente")
        _client = Groq(api_key=api_key)
    return _client


MODEL = "llama-3.3-70b-versatile"

CATEGORIES = [
    "Transporte", "Alimentação", "Lazer", "Saúde",
    "Mercado", "Contas", "Educação", "Outros"
]

SYSTEM_PROMPT = f"""Você é um extrator de dados de gastos pessoais em português brasileiro.

Receba uma mensagem informal e retorne APENAS um JSON válido com os campos:
- "tipo": "gasto" se for um registro de gasto, "consulta" se for pergunta sobre gastos, "outro" se não for nenhum dos dois
- "item": nome curto do gasto (ex: "Uber", "Almoço", "Netflix"). Apenas para tipo="gasto".
- "categoria": uma de {CATEGORIES}. Apenas para tipo="gasto".
- "valor": número decimal em reais (ex: 27.50). Apenas para tipo="gasto".

Regras:
- Para mensagens curtas como "uber 27", "almoço 35,90", "netflix 39.90", extraia os dados.
- Vírgula e ponto são separadores decimais válidos.
- Se a mensagem não tiver valor numérico claro, retorne tipo="outro".
- NUNCA inclua texto fora do JSON. Sem markdown, sem comentários.

Exemplos:
"uber 27" -> {{"tipo":"gasto","item":"Uber","categoria":"Transporte","valor":27.0}}
"almoço 35,90" -> {{"tipo":"gasto","item":"Almoço","categoria":"Alimentação","valor":35.90}}
"quanto gastei esse mês?" -> {{"tipo":"consulta"}}
"oi" -> {{"tipo":"outro"}}
"""


def extract_expense(message: str) -> dict:
    """
    Chama o LLM e retorna um dict com os campos extraídos.
    Em caso de erro, retorna {"tipo": "erro", "motivo": "..."}.
    """
    try:
        resp = get_client().chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message},
            ],
            temperature=0.1,
            max_tokens=200,
            response_format={"type": "json_object"},
        )
        content = resp.choices[0].message.content
        data = json.loads(content)
        return data
    except json.JSONDecodeError as e:
        logger.error(f"JSON inválido do LLM: {e}")
        return {"tipo": "erro", "motivo": "resposta inválida do modelo"}
    except Exception as e:
        logger.error(f"Erro ao chamar Groq: {e}")
        return {"tipo": "erro", "motivo": str(e)}
