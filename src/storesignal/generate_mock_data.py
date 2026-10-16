"""
StoreSignal AI - Mock Data Generator
=====================================
Reproducible mock dataset matching the R5 brief:
  - ~40,000 feedback records across 4 channels
  - Multilingual / code-mixed noise (EN, Hinglish, transliterated Tamil/Marathi)
  - Store master + taxonomy (~30 categories with owning function)
  - Hidden labels (issue type, severity, actionable) on a sample
  - EXACTLY 3 seeded "planted" incidents for the Early-Warning Radar to catch
"""

import csv
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

from storesignal.paths import (
    CODE_ROOT,
    DATA_DIR,
    PROCESSED_DIR,
    RAW_DIR,
    REFERENCE_DIR,
    REPORTS_DIR,
)

ROOT = CODE_ROOT
DATA_RAW = RAW_DIR
DATA_REF = REFERENCE_DIR
DATA_RAW.mkdir(parents=True, exist_ok=True)
DATA_REF.mkdir(parents=True, exist_ok=True)

RANDOM_SEED = 20260214
RNG = random.Random(RANDOM_SEED)

WINDOW_END = datetime(2026, 10, 1, 12, 0, 0, tzinfo=timezone.utc)
WINDOW_DAYS = 28
WINDOW_START = WINDOW_END - timedelta(days=WINDOW_DAYS)

REGIONS = [
    ("North",   "S-DEL"),
    ("South",   "S-BLR"),
    ("East",    "S-KOL"),
    ("West",    "S-MUM"),
    ("Central", "S-HYD"),
]

SIZE_BANDS = ["small", "medium", "large", "flagship"]
SIZE_FOOTFALL = {"small": 1500, "medium": 5000, "large": 12000, "flagship": 25000}


def build_stores(rng):
    stores = []
    for region_name, prefix in REGIONS:
        for i in range(1, 11):
            size = rng.choice(SIZE_BANDS)
            footfall = int(SIZE_FOOTFALL[size] * rng.uniform(0.8, 1.2))
            stores.append({
                "store_id": f"{prefix}-{i:03d}",
                "region_id": f"R-{region_name.upper()}",
                "region_name": region_name,
                "store_name": f"{region_name} Store {i}",
                "size_band": size,
                "weekly_footfall": footfall,
                "opened_year": rng.randint(2005, 2024),
            })
    return stores


def write_store_master(stores):
    path = DATA_REF / "store_master.csv"
    fields = ["store_id", "region_id", "region_name", "store_name",
              "size_band", "weekly_footfall", "opened_year"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(stores)
    print(f"[generate_mock_data] Wrote {len(stores)} stores -> {path}")


TAXONOMY = [
    ("equipment_or_refrigeration",     "Equipment or Refrigeration Failure", "Store Ops",     False),
    ("store_cleanliness",              "Store Cleanliness",                  "Store Ops",     False),
    ("queue_or_wait_time",             "Queue or Wait Time",                 "Store Ops",     False),
    ("checkout_experience",            "Checkout Experience",                "Store Ops",     False),
    ("store_lighting_or_ambience",     "Store Lighting or Ambience",         "Store Ops",     False),
    ("restroom_condition",             "Restroom Condition",                 "Store Ops",     False),
    ("trolley_or_basket_availability", "Trolley or Basket Availability",     "Store Ops",     False),
    ("parking_or_entrance",            "Parking or Entrance",                "Store Ops",     False),
    ("store_hours_or_closure",         "Store Hours or Closure",             "Store Ops",     False),
    ("safety_hazard",                  "Safety Hazard",                      "Store Ops",     True),
    ("allergen_or_labeling",           "Allergen or Labeling Concern",       "Store Ops",     True),
    ("food_safety_or_hygiene",         "Food Safety or Hygiene",             "Store Ops",     True),
    ("out_of_stock",                   "Out of Stock",                       "Supply Chain",  False),
    ("stock_shortage_or_allocation",   "Stock Shortage or Allocation",       "Supply Chain",  False),
    ("product_quality_or_freshness",   "Product Quality or Freshness",       "Supply Chain",  False),
    ("delivery_or_receiving",          "Delivery or Receiving",              "Supply Chain",  False),
    ("cold_chain_integrity",           "Cold Chain Integrity",               "Supply Chain",  False),
    ("expired_or_near_expiry",         "Expired or Near Expiry",             "Merchandising", False),
    ("pricing_or_price_tag_error",     "Pricing or Price Tag Error",         "Merchandising", False),
    ("promotion_or_offer_issue",       "Promotion or Offer Issue",           "Merchandising", False),
    ("planogram_or_shelf_layout",      "Planogram or Shelf Layout",          "Merchandising", False),
    ("product_assortment",             "Product Assortment",                 "Merchandising", False),
    ("packaging_or_labeling",          "Packaging or Labeling",              "Merchandising", False),
    ("app_crash_or_bug",               "App Crash or Bug",                   "Digital",       False),
    ("app_login_or_account",           "App Login or Account",               "Digital",       False),
    ("app_offer_or_loyalty",           "App Offer or Loyalty",               "Digital",       False),
    ("online_order_fulfillment",       "Online Order Fulfillment",           "Digital",       False),
    ("app_payment_issue",              "App Payment Issue",                  "Digital",       False),
    ("staff_conduct",                  "Staff Conduct",                      "HR",            False),
    ("staff_helpfulness",              "Staff Helpfulness",                  "HR",            False),
    ("billing_staff_behaviour",        "Billing Staff Behaviour",            "HR",            False),
    ("staff_misconduct",               "Staff Misconduct",                   "HR",            True),
]

CATEGORY_IDS = [t[0] for t in TAXONOMY]
MANDATORY_CATEGORIES = {t[0] for t in TAXONOMY if t[3]}


def write_taxonomy():
    path = DATA_REF / "taxonomy.csv"
    fields = ["category_id", "category_name", "default_owner", "mandatory_escalation"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(fields)
        for cid, cname, owner, mand in TAXONOMY:
            w.writerow([cid, cname, owner, str(mand).lower()])
    print(f"[generate_mock_data] Wrote {len(TAXONOMY)} categories -> {path}")


PHRASES = {
    "equipment_or_refrigeration": [
        "The freezer is not cooling properly since morning",
        "Fridge broke down, milk is spoiling",
        "Refrigerator bandh hai, thanda nahi ho raha",
        "Freezer sari illa, ice cream melting",
        "Fridge nit chalat nahi, items kharab ho rahe hain",
    ],
    "store_cleanliness": [
        "Floors are dirty, spills not cleaned",
        "Store is very dusty near the aisles",
        "Dukan khup ghaliche ahe, safai nahi",
        "Kadai romba unclean, floor la water",
        "Bhai safai nahi hai, bahut gandagi",
    ],
    "queue_or_wait_time": [
        "Long queue at billing, waited 20 minutes",
        "Only one counter open, huge line",
        "Billing pe bahut line thi, 15 min wait",
        "Queue romba long, wait panna mudiyala",
        "Counter var line khup lamb ahe",
    ],
    "checkout_experience": [
        "Checkout staff was slow and unhelpful",
        "Billing process took very long",
        "Cashier ne jaldi jaldi kaam kiya, rude tha",
        "Billing counter la slow service",
        "Checkout la khup vel gela",
    ],
    "store_lighting_or_ambience": [
        "Lights are flickering in aisle 3",
        "Store feels dim and stuffy",
        "Lights kharab hai, andhera hai",
        "Lights flicker aaguthu, romba dark",
        "Lights khup kami ahet",
    ],
    "restroom_condition": [
        "Restroom is unclean and no water",
        "Washroom has no soap or tissue",
        "Toilet saaf nahi hai, paani nahi",
        "Restroom romba dirty",
        "Toilet khup ghaliche ahe",
    ],
    "trolley_or_basket_availability": [
        "No trolleys available at entrance",
        "Baskets are all broken or missing",
        "Trolley nahi mili, bahut wait kiya",
        "Trolley illa entrance la",
        "Trolley uplabdh nahi",
    ],
    "parking_or_entrance": [
        "Parking is chaotic and no attendant",
        "Entrance is blocked, hard to enter",
        "Parking me jagah nahi mili",
        "Parking romba kastam",
        "Parking khup tight ahe",
    ],
    "store_hours_or_closure": [
        "Store closed earlier than website says",
        "Store timings are wrong on Google",
        "Store time pe khula nahi tha",
        "Store time la open illa",
        "Store vel evejhi band hoto",
    ],
    "safety_hazard": [
        "Wet floor without warning sign, I slipped",
        "Broken glass on aisle floor, unsafe",
        "Farsh pe paani tha, koi sign nahi",
        "Floor la water, slip aayiten",
        "Farshavar pani aahe, sign nahi",
    ],
    "allergen_or_labeling": [
        "Peanut allergen not declared on the label",
        "Mislabelled product, contains milk but not listed",
        "Label pe allergen nahi likha hai, khatarnak",
        "Label la allergen illa, romba danger",
        "Label var allergen nahi, dhoka",
    ],
    "food_safety_or_hygiene": [
        "Cooked food kept uncovered near billing",
        "Deli counter hygiene is very poor",
        "Khana khula rakha hai, hygiene nahi",
        "Food romba unhygienic",
        "Khana ugach aahe, safai nahi",
    ],
    "out_of_stock": [
        "Milk is out of stock again",
        "Essential items missing from shelves",
        "Doodh stock me nahi hai",
        "Pal stock illa",
        "Dudh stock madhe nahi",
    ],
    "stock_shortage_or_allocation": [
        "Same items missing every week at this store",
        "Allocation is unfair to our store",
        "Stock allocation kam hai humare store me",
        "Stock romba kammi",
        "Stock kami ahe",
    ],
    "product_quality_or_freshness": [
        "Vegetables are wilted and old",
        "Fruits not fresh, half rotten",
        "Sabzi taazi nahi hai, sadh gayi",
        "Kaai fresh illa",
        "Bhaji taaji nahi",
    ],
    "delivery_or_receiving": [
        "Delivery arrived late and half missing",
        "Vendor delivery was incomplete",
        "Delivery late aayi, items missing",
        "Delivery late vandhuchu",
        "Delivery ushir aali",
    ],
    "cold_chain_integrity": [
        "Frozen items are soft, cold chain broken",
        "Ice cream was melted when I picked it",
        "Frozen items pighal gaye the",
        "Frozen items melt aagirundhathu",
        "Frozen items vite gele",
    ],
    "expired_or_near_expiry": [
        "Found expired yogurt on the shelf",
        "Curd expires tomorrow but sold today",
        "Expired saman rakha hai shelf pe",
        "Expired item shelf la iruku",
        "Expired item shelf var aahe",
    ],
    "pricing_or_price_tag_error": [
        "Price on shelf does not match billing",
        "Overcharged at checkout versus tag",
        "Shelf pe price alag, bill pe alag",
        "Price tag vera, bill vera",
        "Price tag vegla, bill vegla",
    ],
    "promotion_or_offer_issue": [
        "Buy-one-get-one offer not applied",
        "Promotion not honoured at billing",
        "Offer bill pe apply nahi hua",
        "Offer apply aagala",
        "Offer lagu zala nahi",
    ],
    "planogram_or_shelf_layout": [
        "Aisle layout changed, cannot find items",
        "Shelf arrangement is confusing",
        "Shelf arrangement samajh nahi aata",
        "Shelf layout puriyala",
        "Shelf mandani kalat nahi",
    ],
    "product_assortment": [
        "Store does not carry the brand I need",
        "Very limited assortment in this store",
        "Yahan brand nahi milta",
        "Brand kidaikkala",
        "Brand milat nahi",
    ],
    "packaging_or_labeling": [
        "Package was torn and leaking",
        "Packaging looks tampered",
        "Packet phata hua tha",
        "Packet keelain pochu",
        "Packet phata hota",
    ],
    "app_crash_or_bug": [
        "App crashes whenever I open offers",
        "App freezes on checkout screen",
        "App bar bar crash hota hai",
        "App crash aaguthu",
        "App crash hoto",
    ],
    "app_login_or_account": [
        "Cannot log in, OTP never arrives",
        "Account locked without reason",
        "Login nahi ho raha, OTP nahi aata",
        "Login aagala, OTP varala",
        "Login hot nahi, OTP yet nahi",
    ],
    "app_offer_or_loyalty": [
        "Loyalty points not credited",
        "Offer not visible in app",
        "Points add nahi hue",
        "Points add aagala",
        "Points credit zale nahi",
    ],
    "online_order_fulfillment": [
        "Online order arrived late and incomplete",
        "Substitution not communicated",
        "Order late aaya aur adhura",
        "Order late vandhuchu",
        "Order ushir aala",
    ],
    "app_payment_issue": [
        "Payment failed but money deducted",
        "UPI not working in app",
        "Payment fail hua, paisa kata",
        "Payment fail aachu, cash pochu",
        "Payment fail zala, paisa geli",
    ],
    "staff_conduct": [
        "Staff was rude when I asked for help",
        "Staff ignored me at the counter",
        "Staff ne jawab nahi diya, rude tha",
        "Staff romba rude",
        "Staff rude hota",
    ],
    "staff_helpfulness": [
        "Staff helped me find items, very good",
        "Excellent help at the bakery counter",
        "Staff ne acchi help ki",
        "Staff help pannaar",
        "Staff ne chan madad keli",
    ],
    "billing_staff_behaviour": [
        "Billing staff was impatient and rude",
        "Billing staff kept chatting, ignored me",
        "Billing staff ne ignore kiya",
        "Billing staff ignore pannaar",
        "Billing staff ni ignore kela",
    ],
    "staff_misconduct": [
        "Manager misbehaved with me and shouted",
        "Staff asked for personal favour, unacceptable",
        "Manager ne badtameezi ki",
        "Manager thappa pesinaar",
        "Manager ne chuki vaagani keli",
    ],
}

DEFAULT_PHRASES = ["Issue reported at this store", "Something is not right here"]

EMOJIS = ["\U0001F621", "\U0001F624", "\U0001F61E", "\U0001F64F", "\U0001F62D",
          "\U0001F611", "\U0001F92C", "\U0001F610", "\U0001F926", "\U0001F629",
          "\U0001F44E", "\U0001F972"]


def _apply_typo(text, rng):
    if len(text) < 6:
        return text
    i = rng.randint(1, len(text) - 3)
    chars = list(text)
    chars[i], chars[i + 1] = chars[i + 1], chars[i]
    return "".join(chars)


def apply_noise(text, rng):
    if rng.random() < 0.15:
        text = text.lower()
    if rng.random() < 0.12 and len(text) > 12:
        cut = int(len(text) * rng.uniform(0.5, 0.9))
        text = text[:cut].rstrip() + "..."
    if rng.random() < 0.20:
        text = _apply_typo(text, rng)
    if rng.random() < 0.25:
        text = text + " " + rng.choice(EMOJIS)
    if rng.random() < 0.08:
        text = text + rng.choice([" yaar", " bhai", " please", " seriously"])
    return text


CATEGORY_WEIGHTS = {
    "out_of_stock": 12,
    "queue_or_wait_time": 10,
    "pricing_or_price_tag_error": 8,
    "staff_helpfulness": 8,
    "store_cleanliness": 6,
    "product_quality_or_freshness": 6,
    "app_crash_or_bug": 6,
    "equipment_or_refrigeration": 5,
    "checkout_experience": 5,
    "app_offer_or_loyalty": 5,
    "trolley_or_basket_availability": 4,
    "promotion_or_offer_issue": 4,
    "product_assortment": 4,
    "parking_or_entrance": 3,
    "store_lighting_or_ambience": 3,
    "restroom_condition": 3,
    "store_hours_or_closure": 3,
    "online_order_fulfillment": 3,
    "app_login_or_account": 3,
    "app_payment_issue": 3,
    "delivery_or_receiving": 2,
    "planogram_or_shelf_layout": 2,
    "stock_shortage_or_allocation": 2,
    "expired_or_near_expiry": 2,
    "packaging_or_labeling": 2,
    "cold_chain_integrity": 1,
    "billing_staff_behaviour": 2,
    "staff_conduct": 2,
    "staff_misconduct": 1,
    "allergen_or_labeling": 1,
    "food_safety_or_hygiene": 1,
    "safety_hazard": 1,
}

_weighted_pool = []
for cid, w in CATEGORY_WEIGHTS.items():
    _weighted_pool.extend([cid] * w)


def pick_category(rng):
    return rng.choice(_weighted_pool)


def severity_for_category(cid, rng):
    if cid in MANDATORY_CATEGORIES:
        return rng.choice(["high", "critical", "review_required"])
    if cid in {"out_of_stock", "queue_or_wait_time", "app_crash_or_bug",
               "product_quality_or_freshness", "expired_or_near_expiry"}:
        return rng.choice(["medium", "high"])
    return rng.choice(["low", "medium", "medium", "high"])


def actionable_for_severity(sev, rng):
    if sev in {"critical", "review_required"}:
        return True
    if sev == "high":
        return rng.random() < 0.85
    if sev == "medium":
        return rng.random() < 0.55
    return rng.random() < 0.30


CHANNEL_CONFIG = {
    "reviews":          {"channel": "online_review",    "prefix": "FB-R", "count": 20000, "rating": True},
    "app_feedback":     {"channel": "app_feedback",     "prefix": "FB-A", "count": 10000, "rating": True},
    "staff_notes":      {"channel": "staff_shift_note", "prefix": "FB-S", "count": 5000,  "rating": False},
    "call_transcripts": {"channel": "call_transcript",  "prefix": "FB-C", "count": 5000,  "rating": False},
}


def random_timestamp(rng, start, days):
    day_offset = rng.randint(0, days - 1)
    hour = rng.randint(6, 23)
    minute = rng.randint(0, 59)
    second = rng.randint(0, 59)
    return start + timedelta(days=day_offset, hours=hour, minutes=minute, seconds=second)


def generate_records_for_channel(channel_key, stores, rng):
    cfg = CHANNEL_CONFIG[channel_key]
    channel = cfg["channel"]
    prefix = cfg["prefix"]
    count = cfg["count"]
    has_rating = cfg["rating"]

    records = []
    for i in range(count):
        store = rng.choice(stores)
        cid = pick_category(rng)
        phrase_pool = PHRASES.get(cid, DEFAULT_PHRASES)
        base = rng.choice(phrase_pool)
        noisy = apply_noise(base, rng)

        if channel == "call_transcript":
            text = f"Agent: How can I help? Customer: {noisy}"
        elif channel == "staff_shift_note":
            text = f"Shift note: {noisy}"
        else:
            text = noisy

        ts = random_timestamp(rng, WINDOW_START, WINDOW_DAYS)
        sev = severity_for_category(cid, rng)

        rec = {
            "record_id": f"{prefix}-{i + 1:07d}",
            "source_id": f"{channel_key.upper()}-{i + 1:07d}",
            "channel": channel,
            "store_id": store["store_id"],
            "timestamp": ts.isoformat(),
            "text_raw": text,
            "language_hint": rng.choice(["en", "hi", "ta", "mr", "mixed"]),
            "rating": rng.randint(1, 5) if has_rating else None,
            "_truth_category": cid,
            "_truth_severity": sev,
            "_truth_actionable": actionable_for_severity(sev, rng),
            "_is_seeded": False,
            "_seeded_incident_id": None,
        }
        records.append(rec)
    return records


SEEDED_INCIDENT_DEFS = [
    {
        "incident_id": "SEED-1",
        "category_id": "equipment_or_refrigeration",
        "store_id": "S-MUM-003",
        "region_id": "R-WEST",
        "start_day_offset": 21,
        "daily_counts": [1, 2, 3, 4, 5, 6, 7],
        "channels": ["online_review", "app_feedback", "staff_shift_note", "call_transcript"],
        "severity": "high",
        "narrative": "Freezer failure escalating at West region flagship store.",
    },
    {
        "incident_id": "SEED-2",
        "category_id": "allergen_or_labeling",
        "store_id": "S-BLR-007",
        "region_id": "R-SOUTH",
        "start_day_offset": 23,
        "daily_counts": [1, 2, 3, 4, 5],
        "channels": ["online_review", "app_feedback", "call_transcript"],
        "severity": "critical",
        "narrative": "Allergen mislabeling concern rising sharply at South region store.",
    },
    {
        "incident_id": "SEED-3",
        "category_id": "staff_misconduct",
        "store_id": "S-DEL-002",
        "region_id": "R-NORTH",
        "start_day_offset": 24,
        "daily_counts": [1, 2, 3, 4],
        "channels": ["staff_shift_note", "call_transcript", "online_review"],
        "severity": "critical",
        "narrative": "Staff misconduct reports spiking at North region store.",
    },
]


def seed_incidents(all_records, stores):
    store_index = {s["store_id"]: s for s in stores}
    metadata = []

    counters = {
        "online_review":    sum(1 for r in all_records if r["channel"] == "online_review"),
        "app_feedback":     sum(1 for r in all_records if r["channel"] == "app_feedback"),
        "staff_shift_note": sum(1 for r in all_records if r["channel"] == "staff_shift_note"),
        "call_transcript":  sum(1 for r in all_records if r["channel"] == "call_transcript"),
    }
    prefix_map = {
        "online_review":    "FB-R",
        "app_feedback":     "FB-A",
        "staff_shift_note": "FB-S",
        "call_transcript":  "FB-C",
    }

    for inc in SEEDED_INCIDENT_DEFS:
        store = store_index[inc["store_id"]]
        first_ts = None
        last_ts = None
        record_ids = []

        for day_idx, daily_count in enumerate(inc["daily_counts"]):
            day_offset = inc["start_day_offset"] + day_idx
            for _ in range(daily_count):
                ch = RNG.choice(inc["channels"])
                counters[ch] += 1
                rid = f"{prefix_map[ch]}-{counters[ch]:07d}"

                phrase_pool = PHRASES.get(inc["category_id"], DEFAULT_PHRASES)
                base = RNG.choice(phrase_pool)
                noisy = apply_noise(base, RNG)

                if ch == "call_transcript":
                    text = f"Agent: How can I help? Customer: {noisy}"
                elif ch == "staff_shift_note":
                    text = f"Shift note: {noisy}"
                else:
                    text = noisy

                hour = RNG.randint(7, 22)
                minute = RNG.randint(0, 59)
                ts = WINDOW_START + timedelta(days=day_offset, hours=hour, minutes=minute)

                if first_ts is None or ts < first_ts:
                    first_ts = ts
                if last_ts is None or ts > last_ts:
                    last_ts = ts

                rec = {
                    "record_id": rid,
                    "source_id": f"{ch.upper()}-{counters[ch]:07d}",
                    "channel": ch,
                    "store_id": store["store_id"],
                    "timestamp": ts.isoformat(),
                    "text_raw": text,
                    "language_hint": RNG.choice(["en", "hi", "ta", "mr", "mixed"]),
                    "rating": RNG.randint(1, 5) if ch in {"online_review", "app_feedback"} else None,
                    "_truth_category": inc["category_id"],
                    "_truth_severity": inc["severity"],
                    "_truth_actionable": True,
                    "_is_seeded": True,
                    "_seeded_incident_id": inc["incident_id"],
                }
                all_records.append(rec)
                record_ids.append(rid)

        metadata.append({
            "incident_id": inc["incident_id"],
            "category_id": inc["category_id"],
            "store_id": inc["store_id"],
            "region_id": inc["region_id"],
            "severity": inc["severity"],
            "narrative": inc["narrative"],
            "start_day_offset": inc["start_day_offset"],
            "first_seen": first_ts.isoformat() if first_ts else None,
            "last_seen": last_ts.isoformat() if last_ts else None,
            "record_count": len(record_ids),
            "record_ids": record_ids,
        })

    return metadata


def write_jsonl(path, records):
    with open(path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"[generate_mock_data] Wrote {len(records)} records -> {path}")


def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    print(f"[generate_mock_data] Wrote JSON -> {path}")


def public_record(rec):
    return {k: v for k, v in rec.items() if not k.startswith("_")}


def sample_hidden_labels(all_records, seeded_metadata, sample_size=2000):
    seeded_ids = set()
    for meta in seeded_metadata:
        seeded_ids.update(meta["record_ids"])

    seeded_records = [r for r in all_records if r["record_id"] in seeded_ids]
    non_seeded = [r for r in all_records if r["record_id"] not in seeded_ids]

    remaining_slots = max(0, sample_size - len(seeded_records))
    sample = RNG.sample(non_seeded, min(remaining_slots, len(non_seeded)))

    combined = seeded_records + sample
    RNG.shuffle(combined)

    hidden = []
    for r in combined:
        hidden.append({
            "record_id": r["record_id"],
            "issue_category": r["_truth_category"],
            "severity": r["_truth_severity"],
            "actionable": r["_truth_actionable"],
            "is_seeded": r["_is_seeded"],
            "seeded_incident_id": r["_seeded_incident_id"],
        })
    return hidden


def main():
    print("[generate_mock_data] Building stores and taxonomy...")
    stores = build_stores(RNG)
    write_store_master(stores)
    write_taxonomy()

    print("[generate_mock_data] Generating baseline feedback across 4 channels...")
    all_records = []
    for channel_key in CHANNEL_CONFIG.keys():
        recs = generate_records_for_channel(channel_key, stores, RNG)
        all_records.extend(recs)
        print(f"  - {channel_key}: {len(recs)} records")

    print("[generate_mock_data] Seeding 3 hidden incidents...")
    seeded_metadata = seed_incidents(all_records, stores)
    total_after_seed = len(all_records)

    print("[generate_mock_data] Writing channel JSONL files...")
    for channel_key, cfg in CHANNEL_CONFIG.items():
        chan = cfg["channel"]
        subset = [public_record(r) for r in all_records if r["channel"] == chan]
        write_jsonl(DATA_RAW / f"{channel_key}.jsonl", subset)

    print("[generate_mock_data] Writing hidden labels and seeded-incident metadata...")
    hidden = sample_hidden_labels(all_records, seeded_metadata, sample_size=2000)
    write_jsonl(DATA_RAW / "hidden_labels.jsonl", hidden)
    write_json(DATA_RAW / "seeded_incidents.json", seeded_metadata)

    print("")
    print("[generate_mock_data] SUMMARY")
    print(f"  Total records (incl. seeds): {total_after_seed}")
    print(f"  Hidden labels sampled      : {len(hidden)}")
    print(f"  Seeded incidents           : {len(seeded_metadata)}")
    for m in seeded_metadata:
        print(f"    - {m['incident_id']}: store={m['store_id']} "
              f"category={m['category_id']} records={m['record_count']} "
              f"first_seen={m['first_seen']}")
    print("[generate_mock_data] DONE.")


if __name__ == "__main__":
    main()
