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
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
