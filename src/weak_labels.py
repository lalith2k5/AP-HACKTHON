"""
StoreSignal AI — Weak Supervision Labeler
==========================================
Generates noisy training labels from keyword rules over the normalized text.
This is a stand-in for a hand-labelled training set.

IMPORTANT: This module NEVER reads data/raw/hidden_labels.jsonl.
The hidden labels are reserved for evaluation only (see evaluate.py).
"""

import re
from pathlib import Path

import pandas as pd

HOME = Path.home()
ROOT = HOME / "storesignal-ai"

# ---------------------------------------------------------------------------
# Keyword rules — ordered by priority (first match wins)
# Long multi-word phrases get higher precedence than short single words.
# ---------------------------------------------------------------------------
KEYWORD_RULES = [
    # -- Mandatory risk categories first (highest priority) -----------------
    ("allergen_or_labeling", [
        r"\ballergen\b", r"\bmislabel", r"\bmislabell", r"\ballergy\b",
        r"label la allergen", r"label pe allergen", r"label var allergen",
        r"peanut", r"contains milk but not listed", r"not declared",
    ]),
    ("food_safety_or_hygiene", [
        r"food safety", r"unhygienic", r"hygiene", r"uncovered",
        r"deli counter", r"food romba unhygienic", r"khana ugach",
    ]),
    ("safety_hazard", [
        r"wet floor", r"slipped", r"slip aayiten", r"broken glass",
        r"unsafe", r"no sign", r"koi sign nahi", r"sign nahi",
        r"safety hazard",
    ]),
    ("staff_misconduct", [
        r"manager misbehaved", r"mishandled", r"misbehaved",
        r"personal favour", r"badtameezi", r"thappa pesinaar",
        r"chuki vaagani", r"shouted",
    ]),

    # -- Equipment / refrigeration ------------------------------------------
    ("equipment_or_refrigeration", [
        r"freezer", r"fridge", r"refrigerat", r"cooling",
        r"thanda nahi", r"freezer sari", r"ice cream melting",
        r"items kharab", r"bandh hai",
    ]),

    # -- Cold chain ---------------------------------------------------------
    ("cold_chain_integrity", [
        r"cold chain", r"frozen items", r"frozen items melt",
        r"ice cream was melted", r"pighal", r"vite gele",
    ]),

    # -- Expiry -------------------------------------------------------------
    ("expired_or_near_expiry", [
        r"expired", r"expires tomorrow", r"near expiry",
        r"expired saman", r"expired item",
    ]),

    # -- Product quality / freshness ----------------------------------------
    ("product_quality_or_freshness", [
        r"wilted", r"rotten", r"not fresh", r"taazi nahi",
        r"fresh illa", r"taaji nahi", r"sadh gayi",
    ]),

    # -- Out of stock / allocation ------------------------------------------
    ("stock_shortage_or_allocation", [
        r"allocation", r"same items missing every week", r"unfair",
        r"allocation kam", r"stock romba kammi", r"stock kami",
    ]),
    ("out_of_stock", [
        r"out of stock", r"stock me nahi", r"stock illa",
        r"stock madhe nahi", r"missing from shelves",
        r"essential items missing", r"doodh stock", r"pal stock",
        r"dudh stock",
    ]),

    # -- Queue / checkout / billing -----------------------------------------
    ("queue_or_wait_time", [
        r"long queue", r"queue", r"line thi", r"line khup",
        r"wait", r"one counter", r"huge line", r"queue romba",
    ]),
    ("checkout_experience", [
        r"checkout", r"billing process", r"cashier", r"billing counter",
        r"checkout la khup vel",
    ]),
    ("billing_staff_behaviour", [
        r"billing staff", r"impatient", r"kept chatting",
        r"billing staff ne ignore", r"billing staff ignore",
        r"billing staff ni ignore",
    ]),

    # -- Pricing / promotion ------------------------------------------------
    ("pricing_or_price_tag_error", [
        r"price on shelf", r"overcharged", r"price alag", r"price tag",
        r"bill pe alag", r"price vera", r"bill vera", r"price tag vera",
        r"price tag vegla", r"bill vegla",
    ]),
    ("promotion_or_offer_issue", [
        r"buy-one-get-one", r"bogo", r"promotion", r"offer not applied",
        r"offer apply", r"offer lagu", r"offer bill pe",
    ]),

    # -- Cleanliness / restroom / lighting ----------------------------------
    ("store_cleanliness", [
        r"dirty", r"dusty", r"safai nahi", r"ghaliche",
        r"unclean", r"gandagi", r"spills",
    ]),
    ("restroom_condition", [
        r"restroom", r"washroom", r"toilet", r"no soap",
        r"no water", r"paani nahi", r"saaf nahi",
    ]),
    ("store_lighting_or_ambience", [
        r"flickering", r"lights", r"dim and stuffy",
        r"lights kharab", r"lights flicker", r"lights khup kami",
    ]),

    # -- Trolley / parking / hours ------------------------------------------
    ("trolley_or_basket_availability", [
        r"trolley", r"basket", r"trolleys available",
        r"trolley nahi", r"trolley illa", r"trolley uplabdh",
    ]),
    ("parking_or_entrance", [
        r"parking", r"entrance", r"attendant",
        r"parking me jagah", r"parking romba", r"parking khup",
    ]),
    ("store_hours_or_closure", [
        r"store closed earlier", r"store timings", r"store time",
        r"store hours", r"store vel", r"closed earlier",
    ]),

    # -- Layout / assortment / packaging ------------------------------------
    ("planogram_or_shelf_layout", [
        r"aisle layout", r"shelf arrangement", r"shelf layout",
        r"layout changed", r"shelf mandani", r"cannot find items",
    ]),
    ("product_assortment", [
        r"assortment", r"does not carry", r"brand i need",
        r"brand nahi milta", r"brand kidaikkala", r"brand milat",
        r"limited assortment",
    ]),
    ("packaging_or_labeling", [
        r"package was torn", r"packaging", r"tampered",
        r"packet phata", r"packet keelain", r"leaking",
    ]),

    # -- Delivery / receiving -----------------------------------------------
    ("delivery_or_receiving", [
        r"delivery arrived late", r"vendor delivery", r"delivery late",
        r"delivery ushir", r"incomplete",
    ]),

    # -- Digital ------------------------------------------------------------
    ("app_crash_or_bug", [
        r"app crash", r"app crashes", r"app freezes", r"app bar bar crash",
        r"app crash aaguthu", r"app crash hoto",
    ]),
    ("app_login_or_account", [
        r"cannot log in", r"otp", r"account locked", r"login nahi",
        r"login aagala", r"login hot nahi",
    ]),
    ("app_offer_or_loyalty", [
        r"loyalty", r"points not credited", r"points add",
        r"points credit", r"offer not visible",
    ]),
    ("online_order_fulfillment", [
        r"online order", r"order arrived late", r"substitution",
        r"order late", r"order ushir",
    ]),
    ("app_payment_issue", [
        r"payment failed", r"payment fail", r"upi not working",
        r"money deducted", r"paisa kata", r"cash pochu", r"paisa geli",
    ]),

    # -- HR ------------------------------------------------------------------
    ("staff_conduct", [
        r"staff was rude", r"rude", r"ignored me at the counter",
        r"staff ne jawab", r"staff romba rude", r"staff rude",
    ]),
    ("staff_helpfulness", [
        r"helped me find", r"excellent help", r"acchi help",
        r"staff help pannaar", r"chan madad",
    ]),
]

_COMPILED_RULES = [
    (cat, [re.compile(rx, re.IGNORECASE) for rx in rxs])
    for cat, rxs in KEYWORD_RULES
]

FALLBACK_CATEGORY = "store_cleanliness"  # generic default when nothing matches


def weak_label_text(text: str) -> str:
    if not isinstance(text, str) or not text.strip():
        return FALLBACK_CATEGORY
    for cat, patterns in _COMPILED_RULES:
        for pat in patterns:
            if pat.search(text):
                return cat
    return FALLBACK_CATEGORY


def weak_label_frame(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["weak_category"] = out["text_norm"].apply(weak_label_text)
    return out


if __name__ == "__main__":
    from pathlib import Path
    p = Path.home() / "storesignal-ai" / "data" / "processed" / "normalized_feedback.parquet"
    df = pd.read_parquet(p)
    df = weak_label_frame(df)
    print(df["weak_category"].value_counts().to_string())
    print()
    print("Total weak-labelled rows:", len(df))
