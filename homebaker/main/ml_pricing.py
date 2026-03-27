"""
ML-Based Dynamic Cake Pricing Engine
Uses a Random Forest Regressor to predict a price multiplier based on order features.
Falls back to rule-based pricing when training data is insufficient.
"""

import logging
from decimal import Decimal

logger = logging.getLogger(__name__)

# --- Feature encoding maps ---
FLAVOR_PREMIUMS = {
    'chocolate': 1.0,
    'vanilla': 0.9,
    'red_velvet': 1.25,
    'strawberry': 1.1,
    'butterscotch': 1.05,
    'fruit': 1.1,
    'black_forest': 1.2,
    'pineapple': 1.0,
    'mango': 1.05,
}

OCCASION_PREMIUMS = {
    'birthday': 1.0,
    'wedding': 1.35,
    'anniversary': 1.2,
    'graduation': 1.1,
    'custom': 1.15,
    'festival': 1.05,
}

# Cached model (loaded once per process)
_model = None
_model_trained = False


def _build_features(weight: float, flavor: str, occasion: str,
                    has_message: bool, is_custom: bool) -> list:
    """Encode order features into a numeric vector."""
    flavor_enc = FLAVOR_PREMIUMS.get(flavor, 1.0)
    occasion_enc = OCCASION_PREMIUMS.get(occasion, 1.0)
    return [
        float(weight),
        flavor_enc,
        occasion_enc,
        1.0 if has_message else 0.0,
        1.0 if is_custom else 0.0,
    ]


def _rule_based_multiplier(weight: float, flavor: str, occasion: str,
                            has_message: bool, is_custom: bool) -> float:
    """Fallback rule-based pricing multiplier."""
    multiplier = 1.0

    # Weight bonus: heavier cakes get a small premium
    if weight >= 3:
        multiplier += 0.15
    elif weight >= 2:
        multiplier += 0.08
    elif weight >= 1:
        multiplier += 0.03

    # Flavor premium
    multiplier *= FLAVOR_PREMIUMS.get(flavor, 1.0)

    # Occasion premium
    multiplier *= OCCASION_PREMIUMS.get(occasion, 1.0)

    # Message bonus
    if has_message:
        multiplier += 0.05

    # Custom order bonus
    if is_custom:
        multiplier += 0.10

    return round(min(max(multiplier, 0.7), 2.5), 4)


def _train_model():
    """Train a RandomForestRegressor from historical order data."""
    global _model, _model_trained

    try:
        from sklearn.ensemble import RandomForestRegressor
        import numpy as np
        from .models import OrderItem

        items = OrderItem.objects.select_related('cake', 'order').filter(
            order__status='delivered'
        )

        X, y = [], []
        for item in items:
            try:
                weight = float(item.quantity)
                flavor = item.cake.flavor
                occasion = item.cake.occasion
                has_message = bool(item.message_on_cake)
                is_custom = 'Custom' in item.cake.name or item.cake.occasion == 'custom'

                base_price = float(item.cake.price)
                if base_price <= 0:
                    continue

                # Target: the actual multiplier used (actual unit_price / base_price)
                actual_multiplier = float(item.unit_price) / base_price

                # Sanity-check: ignore outlier multipliers
                if 0.5 <= actual_multiplier <= 3.0:
                    features = _build_features(weight, flavor, occasion, has_message, is_custom)
                    X.append(features)
                    y.append(actual_multiplier)
            except Exception:
                continue

        if len(X) < 10:
            logger.info("ML pricing: insufficient training data (%d samples), using rule-based fallback.", len(X))
            _model = None
            _model_trained = True
            return

        X_arr = np.array(X)
        y_arr = np.array(y)

        model = RandomForestRegressor(
            n_estimators=100,
            max_depth=6,
            random_state=42,
            n_jobs=-1
        )
        model.fit(X_arr, y_arr)

        _model = model
        _model_trained = True
        logger.info("ML pricing: trained RandomForest on %d samples.", len(X))

    except Exception as e:
        logger.warning("ML pricing: model training failed (%s), using rule-based fallback.", e)
        _model = None
        _model_trained = True


def get_price_multiplier(weight: float, flavor: str, occasion: str,
                          has_message: bool = False, is_custom: bool = False) -> float:
    """
    Returns a price multiplier for a cake order item.

    Args:
        weight: Weight in kg
        flavor: Cake flavor string (e.g. 'chocolate')
        occasion: Occasion string (e.g. 'wedding')
        has_message: Whether a message is written on the cake
        is_custom: Whether this is a custom cake order

    Returns:
        A float multiplier (e.g. 1.2 means 20% above base price)
    """
    global _model_trained

    if not _model_trained:
        _train_model()

    if _model is not None:
        try:
            import numpy as np
            features = _build_features(weight, flavor, occasion, has_message, is_custom)
            pred = _model.predict(np.array([features]))[0]
            return round(float(min(max(pred, 0.7), 2.5)), 4)
        except Exception as e:
            logger.warning("ML pricing: prediction failed (%s), falling back to rules.", e)

    return _rule_based_multiplier(weight, flavor, occasion, has_message, is_custom)


def get_adjusted_price(base_price_per_kg: Decimal, weight: float, flavor: str,
                        occasion: str, has_message: bool = False,
                        is_custom: bool = False) -> tuple[Decimal, float]:
    """
    Returns (adjusted_unit_price_per_kg, multiplier).

    The adjusted price is the per-kg price after applying the ML multiplier.
    The caller should then multiply by weight to get the item total.
    """
    multiplier = get_price_multiplier(weight, flavor, occasion, has_message, is_custom)
    adjusted = base_price_per_kg * Decimal(str(multiplier))
    return adjusted.quantize(Decimal('0.01')), multiplier


def retrain():
    """Force retrain the model (call from management command or admin action)."""
    global _model_trained
    _model_trained = False
    _train_model()
