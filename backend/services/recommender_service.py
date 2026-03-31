import json
import ast
import logging
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import numpy as np
import xgboost as xgb

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent

_DATA_CACHE: Dict[str, pd.DataFrame] = {}
_MODEL_CACHE: Dict[str, xgb.Booster] = {}


def _safe_float(value) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def _in_list_case_insensitive(value: Optional[str], options: List[str]) -> bool:
    if not value:
        return False
    value_l = value.strip().lower()
    return any(value_l == o.strip().lower() for o in options if o)


def _contains_any(text: Optional[str], tokens: List[str]) -> int:
    if not text:
        return 0
    text_l = text.lower()
    return sum(1 for t in tokens if t and t.lower() in text_l)


def _get_pref_list(pref_obj: Optional[dict], key: str) -> List[str]:
    if not pref_obj:
        return []
    val = pref_obj.get(key)
    if not val:
        return []
    if isinstance(val, list):
        return [str(v) for v in val if v]
    return []


def _load_csv(name: str, filename: str) -> pd.DataFrame:
    if name in _DATA_CACHE:
        return _DATA_CACHE[name]
    path = ROOT_DIR / filename
    if not path.exists():
        logger.warning(f"{filename} not found")
        df = pd.DataFrame()
        _DATA_CACHE[name] = df
        return df
    df = pd.read_csv(path, low_memory=False)
    _DATA_CACHE[name] = df
    return df


def _load_trains_json() -> List[dict]:
    path = ROOT_DIR / "trains.json"
    if not path.exists():
        logger.warning("trains.json not found")
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _parse_station_list(raw: Optional[str]) -> List[dict]:
    if not raw:
        return []
    if isinstance(raw, list):
        return raw
    try:
        return ast.literal_eval(raw)
    except Exception:
        return []


def _station_name_contains(stations: List[dict], city: str) -> bool:
    city_l = city.strip().lower()
    if not city_l:
        return False
    for st in stations:
        name = str(st.get("stationName") or "").lower()
        if city_l in name:
            return True
    return False


def _train_model(kind: str, df: pd.DataFrame, feature_cols: List[str], target_col: str) -> xgb.Booster:
    if kind in _MODEL_CACHE:
        return _MODEL_CACHE[kind]
    if df.empty:
        d = xgb.DMatrix(np.zeros((1, len(feature_cols))), label=np.zeros(1))
        booster = xgb.train({"objective": "reg:squarederror"}, d, num_boost_round=1)
        _MODEL_CACHE[kind] = booster
        return booster
    X = df[feature_cols].fillna(0.0).to_numpy()
    y = df[target_col].fillna(0.0).to_numpy()
    dtrain = xgb.DMatrix(X, label=y)
    params = {
        "max_depth": 4,
        "eta": 0.1,
        "subsample": 0.9,
        "colsample_bytree": 0.9,
        "objective": "reg:squarederror",
        "seed": 42,
    }
    booster = xgb.train(params, dtrain, num_boost_round=80)
    _MODEL_CACHE[kind] = booster
    return booster


def _prepare_flights(from_city: str, to_city: str) -> pd.DataFrame:
    df = _load_csv("flights", "flights.csv")
    if df.empty:
        return df
    df = df.copy()
    df["price"] = df["price"].apply(_safe_float)
    df["duration"] = df["duration"].apply(_safe_float)
    df["stops"] = df["stops"].map({"zero": 0, "one": 1, "two_or_more": 2}).fillna(1)
    df = df[(df["source_city"].str.contains(from_city, case=False, na=False)) &
            (df["destination_city"].str.contains(to_city, case=False, na=False))]
    if df.empty:
        return df
    df["value_score"] = (10000 - df["price"]) - (df["duration"] * 200) - (df["stops"] * 500)
    return df


def _prepare_hotels(city: str) -> pd.DataFrame:
    df = _load_csv("hotels", "hotels.csv")
    if df.empty:
        return df
    df = df.copy()
    df = df[df["city"].str.contains(city, case=False, na=False)]
    df["hotel_star_rating"] = df["hotel_star_rating"].apply(_safe_float)
    df["site_review_rating"] = df["site_review_rating"].apply(_safe_float)
    df["review_count"] = df["site_review_count"].apply(_safe_float)
    df["estimated_price"] = (df["hotel_star_rating"].clip(lower=1) * 1500) + (df["site_review_rating"].clip(lower=0) * 200)
    df["value_score"] = (df["site_review_rating"] * 20) - (df["estimated_price"] / 100)
    return df


def _prepare_restaurants(city: str) -> pd.DataFrame:
    df = _load_csv("restaurants", "restaurants.csv")
    if df.empty:
        return df
    df = df.copy()
    df = df[df["location"].str.contains(city, case=False, na=False)]
    df["rating"] = df["rating"].apply(_safe_float)
    df["average_price"] = df["average_price"].apply(_safe_float)
    df["value_score"] = (df["rating"] * 20) - (df["average_price"] / 50)
    return df


def _prepare_attractions(city: str) -> pd.DataFrame:
    df = _load_csv("attractions", "attractions.csv")
    if df.empty:
        return df
    df = df.copy()
    df = df[df["City"].str.contains(city, case=False, na=False)]
    df["rating"] = df["Google review rating"].apply(_safe_float)
    df["fee"] = df["Entrance Fee in INR"].apply(_safe_float)
    df["time_needed"] = df["time needed to visit in hrs"].apply(_safe_float)
    df["value_score"] = (df["rating"] * 20) - (df["fee"] / 20)
    return df


# -------- preference & hybrid helpers --------

def _flight_pref_match(row: pd.Series, prefs: Optional[dict]) -> float:
    if not prefs:
        return 0.0
    preferred_modes = _get_pref_list(prefs, "preferred_modes")
    home_city = prefs.get("home_city", "")

    mode_pref = 1.0 if any(m.lower() == "flight" for m in preferred_modes) else 0.0
    home_city_match = 0.0 if not home_city else (0.0 if row.get("source_city", "").lower() == home_city.lower() else -0.2)
    stops_penalty = -0.15 * float(row.get("stops", 0) or 0)
    return mode_pref + home_city_match + stops_penalty


def _hotel_pref_match(row: pd.Series, prefs: Optional[dict]) -> float:
    if not prefs:
        return 0.0
    stay_style = (prefs.get("stay_style") or "").lower()
    amenities = _get_pref_list(prefs.get("seat_room_amenities") or {}, "amenities")
    facilities = str(row.get("hotel_facilities") or "").lower()
    property_type = str(row.get("property_type") or "").lower()
    star = _safe_float(row.get("hotel_star_rating"))

    style_score = 0.0
    if stay_style:
        if stay_style == "luxury" and star >= 4:
            style_score += 0.5
        elif stay_style == "budget" and star <= 3:
            style_score += 0.4
        elif stay_style == "boutique" and "boutique" in property_type:
            style_score += 0.4
        elif stay_style == "apartment" and "apartment" in property_type:
            style_score += 0.3

    amenity_hits = _contains_any(facilities, amenities)
    return style_score + (0.05 * amenity_hits)


def _food_pref_match(row: pd.Series, prefs: Optional[dict]) -> float:
    if not prefs:
        return 0.0
    foods = _get_pref_list(prefs, "food_preferences")
    return 0.1 * _contains_any(str(row.get("restaurant_name") or ""), foods)


def _interest_match(text_fields: List[str], interests: List[str]) -> float:
    if not interests:
        return 0.0
    score = 0.0
    for field in text_fields:
        score += 0.1 * _contains_any(field, interests)
    return score


def _blend_score(model_score: float, pref_score: float, popularity: float, recency: float = 0.0) -> float:
    # Tunable weights; simple defaults.
    w1, w2, w3, w4 = 0.6, 0.25, 0.1, 0.05
    return (w1 * model_score) + (w2 * pref_score) + (w3 * popularity) + (w4 * recency)


def _budget_split_from_prefs(prefs: Optional[dict]) -> Dict[str, float]:
    # Base fractions
    split = {"transport": 0.2, "hotel": 0.4, "food": 0.25, "attraction": 0.15}
    if not prefs:
        return split

    liked = prefs.get("liked_items") or []
    counts = {"hotel": 0, "restaurant": 0, "attraction": 0}
    for item in liked:
        itype = (item.get("item_type") or "").lower()
        if itype in counts:
            counts[itype] += 1

    # Re-weight based on expressed likes
    if counts["restaurant"] > counts["hotel"]:
        delta = 0.05
        split["food"] = min(0.35, split["food"] + delta)
        split["hotel"] = max(0.25, split["hotel"] - delta)
    if counts["attraction"] > max(counts["hotel"], counts["restaurant"]):
        delta = 0.05
        split["attraction"] = min(0.25, split["attraction"] + delta)
        split["transport"] = max(0.1, split["transport"] - delta)

    # Normalize to sum to 1
    total = sum(split.values())
    return {k: v / total for k, v in split.items()}


def _departure_window_bonus(row: pd.Series, prefs: Optional[dict]) -> float:
    if not prefs:
        return 0.0
    freq = (prefs.get("travel_frequency") or "").lower()
    dep_time = str(row.get("departure_time") or "")
    if len(dep_time) < 2 or ":" not in dep_time:
        return 0.0
    try:
        hour = int(dep_time.split(":")[0])
    except Exception:
        return 0.0

    bonus = 0.0
    # Heuristic: frequent travelers prefer morning to maximize day; rare travelers prefer evening after work.
    if freq in {"weekly", "monthly"} and 6 <= hour <= 10:
        bonus += 0.2
    elif freq in {"rarely", "quarterly"} and 18 <= hour <= 22:
        bonus += 0.15
    return bonus


def _veg_filter(df: pd.DataFrame, prefs: Optional[dict]) -> pd.DataFrame:
    if not prefs:
        return df
    foods = [f.lower() for f in _get_pref_list(prefs, "food_preferences")]
    if not foods:
        return df
    wants_veg = any("veg" in f or "vegetarian" in f or "vegan" in f for f in foods)
    if not wants_veg:
        return df

    taboo_terms = ["chicken", "mutton", "beef", "pork", "meat", "fish", "seafood", "steak"]
    mask = ~df["restaurant_name"].str.lower().str.contains("|".join(taboo_terms), na=False)
    filtered = df[mask]
    return filtered if not filtered.empty else df


# Public: lightweight personalization layer for lists
def personalize_items(kind: str, items: list, prefs: Optional[dict] = None, user_vector: Optional[dict] = None):
    if not items:
        return items
    if not isinstance(items, list):
        return items

    kind = (kind or "").lower()
    liked_counts = (user_vector or {}).get("vector", {}).get("liked_counts", {}) if user_vector else {}

    def _stops_value(v):
        if isinstance(v, str):
            mapping = {"zero": 0, "one": 1, "two_or_more": 2}
            return mapping.get(v, 0)
        try:
            return int(v)
        except Exception:
            return 0

    def popularity_score(x):
        if kind == "flight":
            return 1.0 / (1.0 + _stops_value(x.get("stops", 0)))
        if kind == "hotel":
            return _safe_float(x.get("rating") or x.get("site_review_rating"))
        if kind == "restaurant":
            return _safe_float(x.get("rating"))
        if kind == "attraction":
            return _safe_float(x.get("rating"))
        return 0.0

    def model_score(x):
        if kind == "flight":
            return 1.0 / (1.0 + _safe_float(x.get("price")))
        if kind == "hotel":
            return 1.0 / (1.0 + _safe_float(x.get("price_per_night")))
        if kind == "restaurant":
            return 1.0 / (1.0 + _safe_float(x.get("avg_price") or x.get("average_price")))
        if kind == "attraction":
            return 1.0 / (1.0 + _safe_float(x.get("entrance_fee") or x.get("fee")))
        return 0.0

    def pref_score(x):
        if kind == "flight":
            return _flight_pref_match(x, prefs) + _departure_window_bonus(x, prefs)
        if kind == "hotel":
            return _hotel_pref_match(x, prefs)
        if kind == "restaurant":
            return _food_pref_match(x, prefs) + _interest_match([str(x.get("cuisine") or "")], _get_pref_list(prefs, "interests"))
        if kind == "attraction":
            return _interest_match([str(x.get("significance") or x.get("Significance") or "")], _get_pref_list(prefs, "interests"))
        return 0.0

    liked_boost = liked_counts.get(kind, 0) * 0.02

    annotated = []
    for it in items:
        ps = pref_score(it)
        ms = model_score(it)
        pop = popularity_score(it)
        score = _blend_score(ms, ps + liked_boost, pop)
        it = dict(it)
        it["recommended_score"] = round(score, 4)
        annotated.append(it)

    annotated.sort(key=lambda x: x.get("recommended_score", 0), reverse=True)
    for idx, item in enumerate(annotated):
        item["recommended"] = idx < 3  # top 3 get badge
    return annotated


def recommend_trip(
    from_city: Optional[str],
    to_city: str,
    budget: float,
    start_date: str,
    end_date: str,
    people: int,
    travel_mode: str,
    interests: Optional[List[str]] = None,
    preferences: Optional[dict] = None,
) -> dict:
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    days = int((end_dt.date() - start_dt.date()).days) + 1
    days = max(days, 1)

    split = _budget_split_from_prefs(preferences)
    transport_budget = budget * split["transport"]
    hotel_budget = budget * split["hotel"]
    food_budget = budget * split["food"]
    attraction_budget = budget * split["attraction"]

    transport = None
    user_interests = [i.strip() for i in (interests or []) if i.strip()]
    pref_interests = _get_pref_list(preferences, "interests")
    all_interests = list({*user_interests, *pref_interests})
    not_interested_ids = { (item.get("item_type"), item.get("item_id")) for item in (preferences or {}).get("not_interested", []) if item }
    not_interested_names = { (item.get("item_type"), (item.get("name") or "").lower()) for item in (preferences or {}).get("not_interested", []) if item }
    preferred_modes = [m.lower() for m in _get_pref_list(preferences, "preferred_modes")]
    if from_city:
        chosen_mode = travel_mode.lower()
        if not chosen_mode and preferred_modes:
            chosen_mode = preferred_modes[0]
        if chosen_mode == "flight":
            flights = _prepare_flights(from_city, to_city)
            if not flights.empty:
                max_stops = 1 if "flight" in preferred_modes else None
                model = _train_model("flights", flights, ["price", "duration", "stops"], "value_score")
                dtest = xgb.DMatrix(flights[["price", "duration", "stops"]].fillna(0.0).to_numpy())
                flights["model_score"] = model.predict(dtest)
                flights["pref_score"] = flights.apply(lambda r: _flight_pref_match(r, preferences), axis=1)
                flights["pref_score"] += flights.apply(lambda r: _departure_window_bonus(r, preferences), axis=1)
                flights["popularity"] = 1.0 / (1.0 + flights["stops"])
                flights["score"] = _blend_score(flights["model_score"], flights["pref_score"], flights["popularity"])
                flights = flights.sort_values(by=["score", "price"], ascending=[False, True])
                if max_stops is not None:
                    flights = flights[flights["stops"] <= max_stops] or flights
                flights = flights[
                    ~flights.apply(
                        lambda r: ("flight", str(r.get("flight") or "")) in not_interested_ids,
                        axis=1,
                    )
                ]
                top = flights.iloc[0]
                transport = {
                    "type": "flight",
                    "name": f"{top['airline']} {top['flight']}",
                    "price": float(top["price"]) * people,
                    "details": {
                        "from": top["source_city"],
                        "to": top["destination_city"],
                        "duration": float(top["duration"]),
                        "stops": int(top["stops"]),
                    },
                }
        elif travel_mode.lower() == "train":
            trains = _load_trains_json()
            for item in trains:
                if item.get("errorMessage"):
                    continue
                stations = _parse_station_list(item.get("stationList"))
                if not stations:
                    continue
                if _station_name_contains(stations, from_city) and _station_name_contains(stations, to_city):
                    transport = {
                        "type": "train",
                        "name": item.get("trainName") or "",
                        "price": 0.0,
                        "details": {
                            "from": from_city,
                            "to": to_city,
                            "train_number": item.get("trainNumber"),
                        },
                    }
                    break
        else:
            # Auto: prefer cheapest available flight; fallback to train
            flights = _prepare_flights(from_city, to_city)
            if not flights.empty:
                flights = flights.sort_values(by=["price", "duration"])
                top = flights.iloc[0]
                transport = {
                    "type": "flight",
                    "name": f"{top['airline']} {top['flight']}",
                    "price": float(top["price"]) * people,
                    "details": {
                        "from": top["source_city"],
                        "to": top["destination_city"],
                        "duration": float(top["duration"]),
                        "stops": int(top["stops"]),
                    },
                }

    hotel = None
    hotels = _prepare_hotels(to_city)
    if not hotels.empty:
        model = _train_model("hotels", hotels, ["hotel_star_rating", "site_review_rating", "review_count", "estimated_price"], "value_score")
        dtest = xgb.DMatrix(hotels[["hotel_star_rating", "site_review_rating", "review_count", "estimated_price"]].fillna(0.0).to_numpy())
        hotels["model_score"] = model.predict(dtest)
        hotels["pref_score"] = hotels.apply(lambda r: _hotel_pref_match(r, preferences), axis=1)
        hotels["popularity"] = hotels["review_count"].fillna(0.0).apply(lambda x: _safe_float(x))
        hotels["score"] = _blend_score(hotels["model_score"], hotels["pref_score"], hotels["popularity"])
        per_night_budget = hotel_budget / max(days - 1, 1)
        # Apply user budget cap if present
        budget_max = None
        if preferences and preferences.get("budget_range", {}).get("max") is not None:
            budget_max = preferences["budget_range"]["max"]
        if budget_max:
            per_night_budget = min(per_night_budget, float(budget_max))
        candidates = hotels[hotels["estimated_price"] <= per_night_budget]
        if candidates.empty:
            candidates = hotels
        candidates = candidates.sort_values(by=["score", "estimated_price"], ascending=[False, True])
        top = candidates.iloc[0]
        hotel = {
            "name": top.get("property_name") or "",
            "city": top.get("city") or "",
            "price_per_night": float(top["estimated_price"]) * people,
            "total_price": float(top["estimated_price"]) * max(days - 1, 1) * people,
            "rating": float(top.get("site_review_rating") or 0.0),
            "id": top.get("property_id"),
        }

    restaurants = _prepare_restaurants(to_city)
    if not restaurants.empty:
        model = _train_model("restaurants", restaurants, ["rating", "average_price"], "value_score")
        dtest = xgb.DMatrix(restaurants[["rating", "average_price"]].fillna(0.0).to_numpy())
        restaurants["model_score"] = model.predict(dtest)
        restaurants["pref_score"] = restaurants.apply(lambda r: _food_pref_match(r, preferences), axis=1)
        restaurants["popularity"] = restaurants["rating"].fillna(0.0)
        restaurants["score"] = _blend_score(restaurants["model_score"], restaurants["pref_score"], restaurants["popularity"])
        restaurants = restaurants.sort_values(by=["score", "average_price"], ascending=[False, True])
        restaurants = _veg_filter(restaurants, preferences)
        restaurants = restaurants[
            ~restaurants.apply(
                lambda r: (r.get("restaurant_name") or "").lower() in {name for t,name in not_interested_names if t=="restaurant"}
                or ("restaurant", str(r.get("property_id") or r.get("uniq_id") or "")) in not_interested_ids,
                axis=1,
            )
        ]
        # keep top 100 to avoid emptying dataset too hard
        restaurants = restaurants.head(100)

    attractions = _prepare_attractions(to_city)
    if not attractions.empty:
        if all_interests:
            interests_l = [i.strip().lower() for i in all_interests if i.strip()]
            if interests_l:
                filtered = attractions[
                    attractions["Significance"].str.lower().str.contains("|".join(interests_l), na=False)
                    | attractions["Type"].str.lower().str.contains("|".join(interests_l), na=False)
                ]
                if not filtered.empty:
                    attractions = filtered
        model = _train_model("attractions", attractions, ["rating", "fee", "time_needed"], "value_score")
        dtest = xgb.DMatrix(attractions[["rating", "fee", "time_needed"]].fillna(0.0).to_numpy())
        attractions["model_score"] = model.predict(dtest)
        attractions["pref_score"] = 0.0  # interests already filtered; could add sentiment/likes later
        attractions["popularity"] = attractions["rating"].fillna(0.0)
        attractions["score"] = _blend_score(attractions["model_score"], attractions["pref_score"], attractions["popularity"])
        attractions = attractions.sort_values(by=["score", "fee"], ascending=[False, True])
        attractions = attractions[
            ~attractions.apply(
                lambda r: (r.get("Name") or "").lower() in {name for t,name in not_interested_names if t=="attraction"}
                or ("attraction", str(r.get("property_id") or r.get("uniq_id") or "")) in not_interested_ids,
                axis=1,
            )
        ]
        attractions = attractions.head(100)

    plan = []
    total_cost = 0.0
    per_day_food = food_budget / days
    per_day_attr = attraction_budget / days

    attraction_idx = 0
    restaurant_idx = 0

    for d in range(days):
        day_date = (start_dt.date() + pd.Timedelta(days=d)).isoformat()
        day_restaurants = []
        day_attractions = []
        day_cost = 0.0

        if not restaurants.empty:
            picks = 0
            while picks < 2 and restaurant_idx < len(restaurants):
                r = restaurants.iloc[restaurant_idx]
                restaurant_idx += 1
                cost = float(r.get("average_price", 0)) * people
                if day_cost + cost <= per_day_food:
                    day_restaurants.append({
                        "name": r.get("restaurant_name") or "",
                        "price": float(r.get("average_price") or 0.0),
                        "rating": float(r.get("rating") or 0.0),
                    })
                    day_cost += cost
                    picks += 1

        if not attractions.empty:
            picks = 0
            while picks < 3 and attraction_idx < len(attractions):
                a = attractions.iloc[attraction_idx]
                attraction_idx += 1
                cost = float(a.get("fee") or 0.0) * people
                if day_cost + cost <= (per_day_food + per_day_attr):
                    day_attractions.append({
                        "name": a.get("Name") or "",
                        "price": float(a.get("fee") or 0.0),
                        "rating": float(a.get("rating") or 0.0),
                        "type": a.get("Type") or "",
                    })
                    day_cost += cost
                    picks += 1

        plan.append({
            "date": day_date,
            "restaurants": day_restaurants,
            "attractions": day_attractions,
            "estimated_cost": round(day_cost, 2),
        })
        total_cost += day_cost

    if transport:
        total_cost += float(transport.get("price", 0.0))
    if hotel:
        total_cost += float(hotel.get("total_price", 0.0))

    remaining = max(0.0, round(budget - total_cost, 2))

    return {
        "city": to_city,
        "budget": budget,
        "people": people,
        "days": days,
        "travel_mode": travel_mode,
        "transport": transport,
        "hotel": hotel,
        "plan": plan,
        "total_estimated_cost": round(total_cost, 2),
        "remaining_budget": remaining,
    }
