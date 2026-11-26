from decimal import Decimal
from .models import Coupon


def get_valid_coupon(code, email=None):
    """Returns (coupon, None) or (None, error_message)."""
    code = (code or "").strip().upper()
    if not code:
        return None, "Enter a code"
    try:
        coupon = Coupon.objects.get(code=code)
    except Coupon.DoesNotExist:
        return None, "Invalid code"
    if coupon.used:
        return None, "This code has already been used"
    if not coupon.is_valid():
        return None, "This code has expired"
    if coupon.email and email and coupon.email.lower() != email.strip().lower():
        return None, "This code belongs to a different email"
    return coupon, None


def apply_coupon(coupon, subtotal, shipping_fee):
    """Returns (discount_on_items, new_shipping_fee). Percent applies to items only."""
    if coupon.kind == Coupon.FREE_DELIVERY:
        return Decimal("0.00"), Decimal("0.00")
    discount = (subtotal * coupon.percent / 100).quantize(Decimal("0.01"))
    return discount, shipping_fee