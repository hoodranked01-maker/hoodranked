import random
from django.http import JsonResponse
from orders.models import Coupon
from django.views.decorators.http import require_POST

PRIZE_COUPONS = {
    "free_delivery": dict(kind=Coupon.FREE_DELIVERY),
    "five_off": dict(kind=Coupon.PERCENT, percent=5),
    "ten_off": dict(kind=Coupon.PERCENT, percent=10),
}

# Order = order around the wheel. Alternate good/bad so it looks balanced.
WHEEL_PRIZES = [
    {"id": "free_delivery", "label": "FREE DELIVERY", "weight": 8},
    {"id": "none",          "label": "NO LUCK",       "weight": 22},
    {"id": "five_off",      "label": "5% OFF",        "weight": 15},
    {"id": "spin_again",    "label": "SPIN AGAIN",    "weight": 15},
    {"id": "ten_off",       "label": "10% OFF",       "weight": 6},
    {"id": "none",          "label": "NO LUCK",       "weight": 22},
    {"id": "free_delivery", "label": "FREE DELIVERY", "weight": 8},
    {"id": "spin_again",    "label": "SPIN AGAIN",    "weight": 4},
]


@require_POST
def spin_wheel(request):
    state = request.session.get("wheel", {"spins": 1, "prize": None})

    if state["spins"] <= 0:
        return JsonResponse({"error": "already_spun", "prize": state["prize"]}, status=403)

    state["spins"] -= 1
    index = random.choices(range(len(WHEEL_PRIZES)), weights=[p["weight"] for p in WHEEL_PRIZES])[0]
    prize = WHEEL_PRIZES[index]

    code = None
    if prize["id"] == "spin_again":
        state["spins"] += 1
    elif prize["id"] in PRIZE_COUPONS:
        coupon = Coupon.issue(email=state.get("email", ""), **PRIZE_COUPONS[prize["id"]])
        state["prize"] = prize["id"]
        state["code"] = coupon.code
        code = coupon.code

    request.session["wheel"] = state
    request.session.modified = True

    return JsonResponse({
        "index": index, "label": prize["label"], "id": prize["id"],
        "spins_left": state["spins"], "code": code,
    })