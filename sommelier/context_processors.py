import json
from .utils import QUESTIONS


def sommelier_questions(request):
    return {"sommelier_questions_json": json.dumps(QUESTIONS)}
