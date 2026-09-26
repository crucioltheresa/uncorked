import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .utils import QUESTIONS, get_recommendations


def quiz(request):
    return render(
        request, "sommelier/quiz.html", {"questions_json": json.dumps(QUESTIONS)}
    )


@require_POST
def quiz_submit(request):
    try:
        data = json.loads(request.body)
        answers = data.get("answers", {})

        # Validate all required questions are answered
        required_questions = {q["id"] for q in QUESTIONS}
        provided_answers = set(answers.keys())
        missing = required_questions - provided_answers

        if missing:
            return JsonResponse(
                {"error": f"Missing answers: {', '.join(sorted(missing))}"},
                status=400
            )

        wines = get_recommendations(answers)
        results = []
        for wine in wines:
            results.append(
                {
                    "name": wine.name,
                    "region": str(wine.region),
                    "character": wine.character,
                    "price": str(wine.price),
                    "slug": wine.slug,
                    "image": wine.image.url if wine.image else "",
                    "type": wine.get_wine_type_display(),
                    "cart_url": f"/cart/add/{wine.id}/",
                }
            )
        return JsonResponse({"wines": results})
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
