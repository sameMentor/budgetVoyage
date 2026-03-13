from fastapi import FastAPI, APIRouter, Query, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
from jwt import PyJWTError
import csv
import random
import requests

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
SECRET_KEY = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production-' + str(uuid.uuid4()))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

security = HTTPBearer()

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# ==================== MODELS ====================

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str
    phone: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    name: str
    phone: Optional[str] = None
    preferences: Optional[dict] = {}
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class UserProfile(BaseModel):
    email: EmailStr
    name: str
    phone: Optional[str] = None
    preferences: Optional[dict] = {}

class UpdateProfile(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    preferences: Optional[dict] = None

class Flight(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    airline: str
    flight: str
    source_city: str
    destination_city: str
    departure_time: str
    arrival_time: str
    departure_date: str
    duration: float
    stops: str
    class_type: str
    days_left: int
    price: float

class Hotel(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    location: str
    city: str
    rating: float
    price_per_night: float
    amenities: List[str]
    platform: str
    deal_url: str
    image_url: str
    description: str

class Restaurant(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    location: str
    city: str
    cuisine: str
    avg_price: float
    rating: float
    platform: str
    deal_url: str
    image_url: str
    description: str

class Attraction(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    city: str
    state: str
    attraction_type: str
    rating: float
    entrance_fee: float
    time_needed_hours: float
    significance: str
    best_time: str
    weekly_off: str
    dslr_allowed: str

class Train(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    train_number: str
    train_name: str
    source_station_code: str
    destination_station_code: str
    departure_time: Optional[str] = None
    arrival_time: Optional[str] = None
    travel_time: Optional[str] = None
    run_days: Optional[List[str]] = []
    available_classes: Optional[List[str]] = []
    train_type: Optional[str] = None
    booking_url: Optional[str] = None

class Booking(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_email: str
    booking_type: str  # flight, hotel, restaurant
    item_id: str
    item_details: dict
    booking_date: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class BookingCreate(BaseModel):
    booking_type: str
    item_id: str
    item_details: dict

class ItineraryItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_email: str
    item_type: str  # attraction, flight, hotel, restaurant, train
    item_id: str
    item_details: dict
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ItineraryCreate(BaseModel):
    item_type: str
    item_id: str
    item_details: dict

class SavedTrip(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_email: str
    title: str
    trip_details: dict
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class SavedTripCreate(BaseModel):
    title: str
    trip_details: dict

class TripPlanRequest(BaseModel):
    city: str
    budget: float
    start_date: str  # YYYY-MM-DD
    end_date: str    # YYYY-MM-DD
    people: int = 1
    travel_mode: Optional[str] = None
    interests: Optional[List[str]] = None

class TripPlanDay(BaseModel):
    date: str
    attractions: List[Attraction]
    estimated_cost: float

class TripPlanResponse(BaseModel):
    city: str
    budget: float
    people: int
    days: int
    travel_mode: Optional[str] = None
    total_estimated_cost: float
    remaining_budget: float
    plan: List[TripPlanDay]

class RecommendationRequest(BaseModel):
    from_city: Optional[str] = None
    city: str
    budget: float
    start_date: str
    end_date: str
    people: int = 1
    travel_mode: str = "Train"
    interests: Optional[List[str]] = None

class RecommendationResponse(BaseModel):
    city: str
    budget: float
    people: int
    days: int
    travel_mode: str
    transport: Optional[dict] = None
    hotel: Optional[dict] = None
    plan: List[dict]
    total_estimated_cost: float
    remaining_budget: float

class TravelBuddy(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_email: str
    user_name: str
    destination: str
    travel_dates: str
    message: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class TravelBuddyCreate(BaseModel):
    destination: str
    travel_dates: str
    message: str

class Review(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_email: str
    item_id: str
    item_type: str  # flight, hotel, restaurant
    rating: int = Field(ge=1, le=5)
    comment: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ReviewCreate(BaseModel):
    item_id: str
    item_type: str
    rating: int = Field(ge=1, le=5)
    comment: str

# Wallet models
class Wallet(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_email: str
    balance: float = 0.0
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class WalletTransaction(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    wallet_id: str
    amount: float
    type: str  # credit or debit
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class WalletAdd(BaseModel):
    amount: float

# ==================== AUTH HELPERS ====================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return email
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


async def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    if not credentials:
        return None
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except Exception:
        return None

# ==================== SEED DATA ====================

async def load_csv_flights():
    # Use airline homepages as the default booking redirect (better than random aggregator login pages)
    airline_booking_urls = {
        "SPICEJET": "https://www.spicejet.com/",
        "AIRASIA": "https://www.airasia.com/",
        "VISTARA": "https://www.airvistara.com/",
        "GO_FIRST": "https://www.flygofirst.com/",
        "INDIGO": "https://www.goindigo.in/",
        "AIR_INDIA": "https://www.airindia.in/",
    }

    async def get_booking_info(airline: str):
        key = airline.strip().upper().replace(" ", "_")
        url = airline_booking_urls.get(key)
        if url:
            return airline.replace('_', ' '), url
        # fall back to a random aggregator if airline is unknown
        aggregators = [
            {"name": "MakeMyTrip", "url": "https://www.makemytrip.com/flights"},
            {"name": "Cleartrip", "url": "https://www.cleartrip.com/flights"},
            {"name": "Goibibo", "url": "https://www.goibibo.com/flights"},
            {"name": "Expedia", "url": "https://www.expedia.co.in/Flights"},
            {"name": "Yatra", "url": "https://www.yatra.com/flights"},
        ]
        choice = random.choice(aggregators)
        return choice["name"], choice["url"]

    # If flights already exist, update their redirect URLs to match the airline mapping.
    existing = await db.flights.count_documents({})
    if existing > 0:
        logger.info(f"Flights already loaded: {existing} documents")
        cursor = db.flights.find({}, {"_id": 1, "airline": 1})
        async for doc in cursor:
            platform_name, deal_url = await get_booking_info(doc.get("airline", ""))
            await db.flights.update_one(
                {"_id": doc["_id"]},
                {"$set": {"platform": platform_name, "deal_url": deal_url}}
            )
        return

    csv_path = ROOT_DIR / 'flights.csv'
    if not csv_path.exists():
        logger.warning("flights.csv not found")
        return

    logger.info("Loading flights from CSV...")
    batch = []
    batch_size = 1000

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            platform_name, deal_url = await get_booking_info(row['airline'])
            departure_days = int(row['days_left'])
            departure_date = (datetime.now(timezone.utc) + timedelta(days=departure_days)).date().isoformat()
            doc = {
                "id": str(uuid.uuid4()),
                "airline": row['airline'].replace('_', ' '),
                "flight": row['flight'],
                "source_city": row['source_city'],
                "destination_city": row['destination_city'],
                "departure_time": row['departure_time'].replace('_', ' '),
                "arrival_time": row['arrival_time'].replace('_', ' '),
                "departure_date": departure_date,
                "duration": float(row['duration']),
                "stops": row['stops'],
                "class_type": row['class'],
                "days_left": int(row['days_left']),
                "price": float(row['price']),
                "platform": platform_name,
                "deal_url": deal_url,
            }
            batch.append(doc)
            count += 1

            if len(batch) >= batch_size:
                await db.flights.insert_many(batch)
                batch = []
                logger.info(f"Loaded {count} flights...")

        if batch:
            await db.flights.insert_many(batch)

    logger.info(f"CSV loading complete: {count} flights loaded")

async def load_csv_restaurants():
    """Load restaurants from CSV into the database.

    Expects a file named 'indian_restaurants.csv' in the backend directory.

    If the database already has some restaurants but fewer than a threshold,
    we clear and reload to ensure the full dataset is available.
    """
    existing_restaurants = await db.restaurants.count_documents({})

    # If we already have a large dataset, skip reloading.
    if existing_restaurants >= 1000:
        logger.info(f"Restaurants already loaded: {existing_restaurants} documents")
        return

    if existing_restaurants > 0:
        logger.info(f"Restaurants collection is small ({existing_restaurants} docs), reloading from CSV")
        await db.restaurants.delete_many({})

    csv_path = ROOT_DIR / 'indian_restaurants.csv'
    if not csv_path.exists():
        logger.warning("indian_restaurants.csv not found, skipping restaurant seed")
        return

    logger.info("Loading restaurants from CSV...")
    batch = []
    batch_size = 1000
    count = 0

    def truthy(val):
        if val is None:
            return False
        return str(val).strip().lower() in ("1", "true", "yes", "y")

    def pick_cuisine(row):
        if truthy(row.get("south_indian_or_not")):
            return "South Indian"
        if truthy(row.get("north_indian_or_not")):
            return "North Indian"
        if truthy(row.get("biryani_or_not")):
            return "Biryani"
        if truthy(row.get("fast_food_or_not")):
            return "Fast Food"
        if truthy(row.get("street_food")):
            return "Street Food"
        if truthy(row.get("bakery_or_not")):
            return "Bakery"
        return "Indian"

    with open(csv_path, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                rating = float(row.get("rating", 0) or 0)
            except ValueError:
                rating = 0.0

            try:
                avg_price = float(row.get("average_price", 0) or 0)
            except ValueError:
                avg_price = 0.0

            restaurant = {
                "id": str(uuid.uuid4()),
                "name": row.get("restaurant_name", "").strip(),
                "location": row.get("location", "").strip(),
                "city": row.get("location", "").strip(),
                "cuisine": pick_cuisine(row),
                "avg_price": avg_price,
                "rating": rating,
                "platform": "Zomato",
                "deal_url": "https://www.zomato.com",
                "image_url": "",
                "description": f"Average delivery time: {row.get('average _delivery_time', '').strip()} mins",
            }
            batch.append(restaurant)
            count += 1

            if len(batch) >= batch_size:
                await db.restaurants.insert_many(batch)
                batch = []
                logger.info(f"Loaded {count} restaurants...")

        if batch:
            await db.restaurants.insert_many(batch)

    logger.info(f"CSV loading complete: {count} restaurants loaded")


async def seed_hotels_restaurants():
    existing_hotels = await db.hotels.count_documents({})
    if existing_hotels > 0:
        # Still attempt to load restaurants if they are missing
        await load_csv_restaurants()
        return

    hotels_data = [
        {
            "id": str(uuid.uuid4()),
            "name": "Taj Mahal Palace",
            "location": "Colaba",
            "city": "Mumbai",
            "rating": 4.8,
            "price_per_night": 18000.0,
            "amenities": ["Pool", "Spa", "Restaurant", "WiFi", "Gym"],
            "platform": "Booking.com",
            "deal_url": "https://www.booking.com",
            "image_url": "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=800",
            "description": "Iconic luxury hotel with stunning sea views"
        },

        {
            "id": str(uuid.uuid4()),
            "name": "The Oberoi",
            "location": "Nariman Point",
            "city": "Mumbai",
            "rating": 4.7,
            "price_per_night": 15000.0,
            "amenities": ["Pool", "Restaurant", "WiFi", "Gym", "Bar"],
            "platform": "MakeMyTrip",
            "deal_url": "https://www.makemytrip.com/hotels",
            "image_url": "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?w=800",
            "description": "Elegant hotel with panoramic city views"
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Hyatt Regency",
            "location": "Sakinaka",
            "city": "Mumbai",
            "rating": 4.5,
            "price_per_night": 8500.0,
            "amenities": ["Pool", "Restaurant", "WiFi", "Gym"],
            "platform": "Agoda",
            "deal_url": "https://www.agoda.com",
            "image_url": "https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?w=800",
            "description": "Modern hotel near international airport"
        },
        {
            "id": str(uuid.uuid4()),
            "name": "ITC Maurya",
            "location": "Diplomatic Enclave",
            "city": "Delhi",
            "rating": 4.6,
            "price_per_night": 12000.0,
            "amenities": ["Spa", "Restaurant", "WiFi", "Gym", "Bar"],
            "platform": "Expedia",
            "deal_url": "https://www.expedia.com/hotels",
            "image_url": "https://images.unsplash.com/photo-1571003123894-1f0594d2b5d9?w=800",
            "description": "Luxury hotel in diplomatic area"
        },
        {
            "id": str(uuid.uuid4()),
            "name": "The Leela Palace",
            "location": "Chanakyapuri",
            "city": "Delhi",
            "rating": 4.9,
            "price_per_night": 16500.0,
            "amenities": ["Pool", "Spa", "Restaurant", "WiFi", "Gym", "Concierge"],
            "platform": "Hotels.com",
            "deal_url": "https://www.hotels.com",
            "image_url": "https://images.unsplash.com/photo-1618773928121-c32242e63f39?w=800",
            "description": "Opulent palace-style hotel with world-class service"
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Taj West End",
            "location": "Race Course Road",
            "city": "Bangalore",
            "rating": 4.7,
            "price_per_night": 11000.0,
            "amenities": ["Pool", "Restaurant", "WiFi", "Gym", "Garden"],
            "platform": "MakeMyTrip",
            "deal_url": "https://www.makemytrip.com/hotels",
            "image_url": "https://images.unsplash.com/photo-1564501049412-61c2a3083791?w=800",
            "description": "Heritage hotel with lush gardens"
        }
    ]
    await db.hotels.insert_many(hotels_data)
    
    restaurants_data = [
        {
            "id": str(uuid.uuid4()),
            "name": "Bukhara",
            "location": "ITC Maurya",
            "city": "Delhi",
            "cuisine": "North Indian",
            "avg_price": 3500.0,
            "rating": 4.8,
            "platform": "Zomato",
            "deal_url": "https://www.zomato.com",
            "image_url": "https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=800",
            "description": "Legendary restaurant for North Indian cuisine"
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Indian Accent",
            "location": "Lodhi Road",
            "city": "Delhi",
            "cuisine": "Contemporary Indian",
            "avg_price": 4000.0,
            "rating": 4.9,
            "platform": "Dineout",
            "deal_url": "https://www.dineout.co.in",
            "image_url": "https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=800",
            "description": "Innovative Indian cuisine with modern twist"
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Trishna",
            "location": "Kala Ghoda",
            "city": "Mumbai",
            "cuisine": "Seafood",
            "avg_price": 2500.0,
            "rating": 4.6,
            "platform": "Zomato",
            "deal_url": "https://www.zomato.com",
            "image_url": "https://images.unsplash.com/photo-1559339352-11d035aa65de?w=800",
            "description": "Famous for butter garlic crab and seafood"
        },
        {
            "id": str(uuid.uuid4()),
            "name": "The Bombay Canteen",
            "location": "Lower Parel",
            "city": "Mumbai",
            "cuisine": "Modern Indian",
            "avg_price": 2000.0,
            "rating": 4.5,
            "platform": "EazyDiner",
            "deal_url": "https://www.eazydiner.com",
            "image_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=800",
            "description": "Regional Indian food with creative presentations"
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Karavalli",
            "location": "The Gateway Hotel",
            "city": "Bangalore",
            "cuisine": "Coastal Indian",
            "avg_price": 2800.0,
            "rating": 4.7,
            "platform": "Zomato",
            "deal_url": "https://www.zomato.com",
            "image_url": "https://images.unsplash.com/photo-1540189549336-e6e99c3679fe?w=800",
            "description": "Authentic coastal cuisine from South India"
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Caperberry",
            "location": "Vittal Mallya Road",
            "city": "Bangalore",
            "cuisine": "European",
            "avg_price": 3200.0,
            "rating": 4.6,
            "platform": "Dineout",
            "deal_url": "https://www.dineout.co.in",
            "image_url": "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=800",
            "description": "Fine dining European restaurant"
        }
    ]
    await db.restaurants.insert_many(restaurants_data)
    
    # Load any additional restaurants from CSV, if available
    await load_csv_restaurants()

    logger.info("Hotels and restaurants seeded")

async def load_csv_attractions():
    existing = await db.attractions.count_documents({})
    if existing > 0:
        logger.info(f"Attractions already loaded: {existing} documents")
        return

    csv_path = ROOT_DIR / 'attractions.csv'
    if not csv_path.exists():
        logger.warning("attractions.csv not found")
        return

    logger.info("Loading attractions from CSV...")
    batch = []
    batch_size = 1000

    def to_float(value: str) -> float:
        try:
            return float(value)
        except Exception:
            return 0.0

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            doc = {
                "id": str(uuid.uuid4()),
                "name": row.get("Name", "") or "",
                "city": row.get("City", "") or "",
                "state": row.get("State", "") or "",
                "attraction_type": row.get("Type", "") or "",
                "rating": to_float(row.get("Google review rating", "")),
                "entrance_fee": to_float(row.get("Entrance Fee in INR", "")),
                "time_needed_hours": to_float(row.get("time needed to visit in hrs", "")),
                "significance": row.get("Significance", "") or "",
                "best_time": row.get("Best Time to visit", "") or "",
                "weekly_off": row.get("Weekly Off", "") or "",
                "dslr_allowed": row.get("DSLR Allowed", "") or "",
            }
            batch.append(doc)
            count += 1

            if len(batch) >= batch_size:
                await db.attractions.insert_many(batch)
                batch = []
                logger.info(f"Loaded {count} attractions...")

        if batch:
            await db.attractions.insert_many(batch)

    logger.info(f"CSV loading complete: {count} attractions loaded")

# ==================== AUTH ROUTES ====================

@api_router.post("/auth/register")
async def register(user: UserRegister):
    existing = await db.users.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_doc = {
        "id": str(uuid.uuid4()),
        "email": user.email,
        "password": hash_password(user.password),
        "name": user.name,
        "phone": user.phone,
        "preferences": {},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(user_doc)
    
    token = create_access_token({"sub": user.email})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"email": user.email, "name": user.name}
    }

@api_router.post("/auth/login")
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email})
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_access_token({"sub": credentials.email})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"email": user["email"], "name": user["name"]}
    }

# ==================== PROFILE ROUTES ====================

@api_router.get("/profile", response_model=UserProfile)
async def get_profile(current_user: str = Depends(get_current_user)):
    user = await db.users.find_one({"email": current_user}, {"_id": 0, "password": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@api_router.put("/profile")
async def update_profile(profile: UpdateProfile, current_user: str = Depends(get_current_user)):
    update_data = {k: v for k, v in profile.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    
    await db.users.update_one({"email": current_user}, {"$set": update_data})
    return {"message": "Profile updated successfully"}

# ==================== BOOKING ROUTES ====================

@api_router.post("/bookings", response_model=Booking)
async def create_booking(booking: BookingCreate, current_user: str = Depends(get_current_user)):
    booking_obj = Booking(
        user_email=current_user,
        booking_type=booking.booking_type,
        item_id=booking.item_id,
        item_details=booking.item_details
    )
    doc = booking_obj.model_dump()
    await db.bookings.insert_one(doc)
    return booking_obj

@api_router.get("/bookings", response_model=List[Booking])
async def get_bookings(current_user: str = Depends(get_current_user)):
    bookings = await db.bookings.find({"user_email": current_user}, {"_id": 0}).to_list(1000)
    return bookings

# ==================== ITINERARY ROUTES ====================

@api_router.post("/itinerary", response_model=ItineraryItem)
async def create_itinerary_item(item: ItineraryCreate, current_user: str = Depends(get_current_user)):
    itinerary_obj = ItineraryItem(
        user_email=current_user,
        item_type=item.item_type,
        item_id=item.item_id,
        item_details=item.item_details,
    )
    doc = itinerary_obj.model_dump()
    await db.itineraries.insert_one(doc)
    return itinerary_obj

@api_router.get("/itinerary", response_model=List[ItineraryItem])
async def get_itinerary(current_user: str = Depends(get_current_user)):
    items = await db.itineraries.find({"user_email": current_user}, {"_id": 0}).to_list(1000)
    return items

@api_router.delete("/itinerary/{item_id}")
async def delete_itinerary_item(item_id: str, current_user: str = Depends(get_current_user)):
    result = await db.itineraries.delete_one({"user_email": current_user, "id": item_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Itinerary item not found")
    return {"message": "Itinerary item removed"}

# ==================== SAVED TRIPS ====================

@api_router.post("/trips/saved", response_model=SavedTrip)
async def save_trip(trip: SavedTripCreate, current_user: str = Depends(get_current_user)):
    saved = SavedTrip(
        user_email=current_user,
        title=trip.title,
        trip_details=trip.trip_details,
    )
    await db.saved_trips.insert_one(saved.model_dump())
    return saved

@api_router.get("/trips/saved", response_model=List[SavedTrip])
async def get_saved_trips(current_user: str = Depends(get_current_user)):
    items = await db.saved_trips.find({"user_email": current_user}, {"_id": 0}).to_list(1000)
    return items

@api_router.delete("/trips/saved/{trip_id}")
async def delete_saved_trip(trip_id: str, current_user: str = Depends(get_current_user)):
    result = await db.saved_trips.delete_one({"user_email": current_user, "id": trip_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Saved trip not found")
    return {"message": "Saved trip removed"}

# ==================== TRIP PLANNER ====================

@api_router.post("/trip/plan", response_model=TripPlanResponse)
async def plan_trip(request: TripPlanRequest):
    if request.budget <= 0:
        raise HTTPException(status_code=400, detail="Budget must be greater than 0")
    if request.people <= 0:
        raise HTTPException(status_code=400, detail="People must be at least 1")

    try:
        start_dt = datetime.fromisoformat(request.start_date)
        end_dt = datetime.fromisoformat(request.end_date)
    except Exception:
        raise HTTPException(status_code=400, detail="Dates must be in YYYY-MM-DD format")

    if end_dt < start_dt:
        raise HTTPException(status_code=400, detail="End date must be after start date")

    days = (end_dt.date() - start_dt.date()).days + 1
    per_day_budget = request.budget / max(days, 1)

    query = {"city": {"$regex": request.city, "$options": "i"}}
    attractions = await db.attractions.find(query, {"_id": 0}).to_list(500)

    if request.interests:
        interests = [i.strip().lower() for i in request.interests if i.strip()]
        if interests:
            filtered = []
            for a in attractions:
                sig = str(a.get("significance", "")).lower()
                a_type = str(a.get("attraction_type", "")).lower()
                if any(i in sig or i in a_type for i in interests):
                    filtered.append(a)
            attractions = filtered

    attractions.sort(key=lambda x: (-x.get("rating", 0), x.get("entrance_fee", 0)))

    used_ids = set()
    plan = []
    total_cost = 0.0

    for offset in range(days):
        day_date = (start_dt.date() + timedelta(days=offset)).isoformat()
        day_budget = per_day_budget
        day_items = []
        day_cost = 0.0

        for a in attractions:
            if a.get("id") in used_ids:
                continue
            cost = float(a.get("entrance_fee", 0)) * request.people
            if day_cost + cost <= day_budget:
                day_items.append(a)
                day_cost += cost
                used_ids.add(a.get("id"))
            if day_cost >= day_budget:
                break

        if not day_items and attractions:
            for a in attractions:
                if a.get("id") in used_ids:
                    continue
                day_items.append(a)
                used_ids.add(a.get("id"))
                day_cost += float(a.get("entrance_fee", 0)) * request.people
                break

        plan.append(
            TripPlanDay(
                date=day_date,
                attractions=day_items,
                estimated_cost=round(day_cost, 2),
            )
        )
        total_cost += day_cost

    remaining = max(0.0, round(request.budget - total_cost, 2))

    return TripPlanResponse(
        city=request.city,
        budget=request.budget,
        people=request.people,
        days=days,
        travel_mode=request.travel_mode,
        total_estimated_cost=round(total_cost, 2),
        remaining_budget=remaining,
        plan=plan,
    )

@api_router.post("/recommendations", response_model=RecommendationResponse)
async def get_recommendations(request: RecommendationRequest):
    from services import recommender_service
    if request.budget <= 0:
        raise HTTPException(status_code=400, detail="Budget must be greater than 0")
    if request.people <= 0:
        raise HTTPException(status_code=400, detail="People must be at least 1")

    result = recommender_service.recommend_trip(
        from_city=request.from_city,
        to_city=request.city,
        budget=request.budget,
        start_date=request.start_date,
        end_date=request.end_date,
        people=request.people,
        travel_mode=request.travel_mode,
        interests=request.interests,
    )
    return result

# ==================== TRAVEL BUDDY ROUTES ====================

@api_router.post("/travel-buddies", response_model=TravelBuddy)
async def create_travel_buddy(buddy: TravelBuddyCreate, current_user: str = Depends(get_current_user)):
    user = await db.users.find_one({"email": current_user})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    buddy_obj = TravelBuddy(
        user_email=current_user,
        user_name=user["name"],
        destination=buddy.destination,
        travel_dates=buddy.travel_dates,
        message=buddy.message
    )
    doc = buddy_obj.model_dump()
    await db.travel_buddies.insert_one(doc)
    return buddy_obj

@api_router.get("/travel-buddies", response_model=List[TravelBuddy])
async def get_travel_buddies(
    destination: Optional[str] = Query(None),
    current_user: Optional[str] = Depends(get_current_user_optional)
):
    query = {}
    if destination:
        query["destination"] = {"$regex": destination, "$options": "i"}

    # Exclude current user's own posts when authenticated
    if current_user:
        query["user_email"] = {"$ne": current_user}

    buddies = await db.travel_buddies.find(query, {"_id": 0}).to_list(1000)
    return buddies
# ==================== WALLET ROUTES ====================

@api_router.get("/wallet")
async def get_wallet(current_user: str = Depends(get_current_user)):
    wallet = await db.wallets.find_one({"user_email": current_user}, {"_id": 0})
    if not wallet:
        wallet = Wallet(user_email=current_user).model_dump()
        await db.wallets.insert_one(wallet)
    return wallet

@api_router.post("/wallet/add")
async def add_funds(payload: WalletAdd, current_user: str = Depends(get_current_user)):
    wallet = await db.wallets.find_one({"user_email": current_user}, {"_id": 0})
    if not wallet:
        wallet = Wallet(user_email=current_user).model_dump()
        await db.wallets.insert_one(wallet)

    new_balance = wallet.get("balance", 0.0) + payload.amount
    await db.wallets.update_one(
        {"user_email": current_user},
        {"$set": {"balance": new_balance, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )

    # Create a transaction record but don't fail the request if this part fails.
    try:
        wallet_id = wallet.get("id") or str(uuid.uuid4())
        txn = WalletTransaction(wallet_id=wallet_id, amount=payload.amount, type="credit").model_dump()
        await db.wallet_transactions.insert_one(txn)
    except Exception as e:
        logger.error("Failed to create wallet transaction: %s", e)

    # Return a JSON-serializable wallet (exclude internal Mongo _id)
    wallet = await db.wallets.find_one({"user_email": current_user}, {"_id": 0})
    return wallet

# ==================== WEATHER ROUTE ====================

# simple mapping for commonly used cities
_city_coords = {
    "DELHI": {"lat": 28.7041, "lon": 77.1025},
    "MUMBAI": {"lat": 19.0760, "lon": 72.8777},
    "BENGALURU": {"lat": 12.9716, "lon": 77.5946},
    "BANGALORE": {"lat": 12.9716, "lon": 77.5946},
    "CHENNAI": {"lat": 13.0827, "lon": 80.2707},
    "HYDERABAD": {"lat": 17.3850, "lon": 78.4867},
    "KOLKATA": {"lat": 22.5726, "lon": 88.3639},
    "GOA": {"lat": 15.2993, "lon": 74.1240},
    "JAIPUR": {"lat": 26.9124, "lon": 75.7873},
    "PUNE": {"lat": 18.5204, "lon": 73.8567},
}

# simple list of attractions per city for sample tours
_city_attractions = {
    "DELHI": [
        {"name": "Red Fort + Old Delhi Walk", "description": "Explore historic monuments and street food in Old Delhi."},
        {"name": "Qutub Minar & Garden Tour", "description": "Visit iconic monuments and enjoy a peaceful garden walk."},
        {"name": "Evening Light Show at India Gate", "description": "See the national monument lit up at night with a guided narration."},
    ],
    "MUMBAI": [
        {"name": "Gateway of India & Marine Drive", "description": "Coastal walk from the Gateway to Queen's Necklace."},
        {"name": "Street Food Tour in Colaba", "description": "Sample vada pav, bhel puri, and pav bhaji from local stalls."},
        {"name": "Elephanta Caves Ferry", "description": "Take a ferry to the UNESCO-listed caves and return by sunset."},
    ],
    "BANGALORE": [
        {"name": "Lalbagh Botanical Garden", "description": "Morning stroll among rare trees and glasshouse flowers."},
        {"name": "Bangalore Palace Tour", "description": "Visit the royal palace and learn about its history."},
        {"name": "Food Walk in Indiranagar", "description": "Try popular cafes and street bites in the buzzing neighborhood."},
    ],
    "GOA": [
        {"name": "North Goa Beach Hopping", "description": "Explore Calangute, Baga, and Anjuna with sunset views."},
        {"name": "Cultural Old Goa Tour", "description": "Visit basilicas, museums, and colonial architecture."},
        {"name": "Goa Spice Plantation Visit", "description": "Learn about spices, enjoy a farm lunch, and do a short nature walk."},
    ],
}


@api_router.get("/weather")
async def get_weather(city: str = Query(...)):
    coords = _city_coords.get(city.strip().upper())
    if not coords:
        raise HTTPException(status_code=404, detail="City not supported")
    url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={coords['lat']}"
        f"&longitude={coords['lon']}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=auto"
    )
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
    except Exception:
        raise HTTPException(status_code=502, detail="Weather service error")
    data = resp.json()
    forecast = []
    daily = data.get("daily", {})
    dates = daily.get("time", [])
    maxs = daily.get("temperature_2m_max", [])
    mins = daily.get("temperature_2m_min", [])
    prec = daily.get("precipitation_sum", [])
    for i, d in enumerate(dates):
        forecast.append({
            "date": d,
            "temp_max": maxs[i] if i < len(maxs) else None,
            "temp_min": mins[i] if i < len(mins) else None,
            "precip": prec[i] if i < len(prec) else None,
        })
    return {"city": city, "forecast": forecast}


# ==================== ATTRACTIONS / TOURS ROUTE ====================

class Attraction(BaseModel):
    name: str
    description: str

@api_router.get("/attractions")
async def get_attractions(city: str = Query(...), date: Optional[str] = Query(None)):
    key = city.strip().upper()
    if key not in _city_attractions:
        raise HTTPException(status_code=404, detail="No attractions found for this city")

    # Basic logic: rotate activities based on date to show some variation
    activities = _city_attractions[key]
    if date:
        # pick a starting index based on date hash to add variability
        idx = sum(ord(c) for c in date) % len(activities)
        rotated = activities[idx:] + activities[:idx]
    else:
        rotated = activities

    return {"city": city, "date": date, "attractions": rotated}
# ==================== REVIEWS ROUTES ====================

@api_router.post("/reviews", response_model=Review)
async def create_review(review: ReviewCreate, current_user: str = Depends(get_current_user)):
    user = await db.users.find_one({"email": current_user})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    review_obj = Review(
        user_email=current_user,
        item_id=review.item_id,
        item_type=review.item_type,
        rating=review.rating,
        comment=review.comment,
    )
    await db.reviews.insert_one(review_obj.model_dump())
    return review_obj

@api_router.get("/reviews")
async def get_reviews(
    item_id: Optional[str] = Query(None),
    item_type: Optional[str] = Query(None),
    limit: int = Query(20, le=100)
):
    query = {}
    if item_id:
        query["item_id"] = item_id
    if item_type:
        query["item_type"] = item_type

    reviews = await db.reviews.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)
    return reviews

# ==================== FLIGHTS ROUTES ====================
from services import flight_service

@api_router.get("/flights")
async def get_flights(
    source: Optional[str] = Query(None),
    destination: Optional[str] = Query(None),
    max_price: Optional[float] = Query(None),
    stops: Optional[str] = Query(None),
    departure_date: Optional[str] = Query(None),
    return_date: Optional[str] = Query(None),
    limit: int = Query(50, le=200)
):
    # try external provider first
    external = await flight_service.search_flights(
        source=source,
        destination=destination,
        max_price=max_price,
        stops=stops,
        limit=min(limit, 20),
    )
    if external is not None:
        return external

    # fallback to seeded mongodb data
    query = {}
    if source:
        query["source_city"] = {"$regex": source, "$options": "i"}
    if destination:
        query["destination_city"] = {"$regex": destination, "$options": "i"}
    if max_price:
        query["price"] = {"$lte": max_price}
    if stops:
        query["stops"] = stops
    if departure_date:
        query["departure_date"] = departure_date
    
    flights = await db.flights.find(query, {"_id": 0}).sort("price", 1).to_list(limit)
    return flights

# ==================== HOTELS ROUTES ====================
from services import booking_service

@api_router.get("/hotels", response_model=List[Hotel])
async def get_hotels(
    city: Optional[str] = Query(None),
    max_price: Optional[float] = Query(None),
    min_rating: Optional[float] = Query(None)
):
    # attempt live lookup
    external = await booking_service.search_hotels(
        city=city,
        max_price=max_price,
        min_rating=min_rating,
        limit=20,
    )
    if external is not None:
        return external

    # fallback to DB
    query = {}
    if city:
        query["city"] = {"$regex": city, "$options": "i"}
    if max_price:
        query["price_per_night"] = {"$lte": max_price}
    if min_rating:
        query["rating"] = {"$gte": min_rating}
    
    hotels = await db.hotels.find(query, {"_id": 0}).to_list(1000)
    hotels.sort(key=lambda x: x["price_per_night"])
    return hotels

# ==================== RESTAURANTS ROUTES ====================
from services import tripadvisor_service

@api_router.get("/restaurants", response_model=List[Restaurant])
async def get_restaurants(
    city: Optional[str] = Query(None),
    cuisine: Optional[str] = Query(None),
    max_price: Optional[float] = Query(None),
    min_rating: Optional[float] = Query(None)
):
    external = await tripadvisor_service.search_restaurants(
        city=city,
        cuisine=cuisine,
        max_price=max_price,
        min_rating=min_rating,
        limit=20,
    )
    if external is not None:
        return external

    query = {}
    if city:
        query["city"] = {"$regex": city, "$options": "i"}
    if cuisine:
        query["cuisine"] = {"$regex": cuisine, "$options": "i"}
    if max_price:
        query["avg_price"] = {"$lte": max_price}
    if min_rating:
        query["rating"] = {"$gte": min_rating}
    
    restaurants = await db.restaurants.find(query, {"_id": 0}).to_list(1000)
    restaurants.sort(key=lambda x: x["avg_price"])
    return restaurants

# ==================== ATTRACTIONS ROUTES ====================

@api_router.get("/attractions", response_model=List[Attraction])
async def get_attractions(
    city: Optional[str] = Query(None),
    max_fee: Optional[float] = Query(None),
    min_rating: Optional[float] = Query(None)
):
    query = {}
    if city:
        query["city"] = {"$regex": city, "$options": "i"}
    if max_fee is not None:
        query["entrance_fee"] = {"$lte": max_fee}
    if min_rating is not None:
        query["rating"] = {"$gte": min_rating}

    attractions = await db.attractions.find(query, {"_id": 0}).to_list(1000)
    attractions.sort(key=lambda x: (-x.get("rating", 0), x.get("entrance_fee", 0)))
    return attractions

# ==================== TRAINS ROUTES ====================
from services import train_service

@api_router.get("/trains", response_model=List[Train])
async def get_trains(
    query: Optional[str] = Query(None),
    limit: int = Query(20, le=100)
):
    external = await train_service.search_trains(query=query, limit=limit)
    if external is not None:
        return external
    return []

@api_router.get("/stations")
async def get_stations(
    query: Optional[str] = Query(None),
    limit: int = Query(20, le=100)
):
    external = await train_service.search_stations(query=query, limit=limit)
    if external is not None:
        return external
    return []

@api_router.get("/trains/between", response_model=List[Train])
async def get_trains_between(
    from_station: Optional[str] = Query(None, alias="from"),
    to_station: Optional[str] = Query(None, alias="to"),
    date: Optional[str] = Query(None),
    limit: int = Query(50, le=200)
):
    external = await train_service.search_trains_between(
        from_station=from_station,
        to_station=to_station,
        travel_date=date,
        limit=limit,
    )
    if external is not None:
        return external
    return []

@api_router.get("/trains/between-cities", response_model=List[Train])
async def get_trains_between_cities(
    from_city: Optional[str] = Query(None),
    to_city: Optional[str] = Query(None),
    date: Optional[str] = Query(None),
    limit: int = Query(50, le=200)
):
    external = await train_service.search_trains_between_cities(
        from_city=from_city,
        to_city=to_city,
        travel_date=date,
        station_limit=3,
        limit=limit,
    )
    if external is not None:
        return external
    return []

# ==================== CITIES ROUTE ====================

@api_router.get("/cities")
async def get_cities():
    flight_origins = await db.flights.distinct("source_city")
    flight_destinations = await db.flights.distinct("destination_city")
    hotel_cities = await db.hotels.distinct("city")
    restaurant_cities = await db.restaurants.distinct("city")
    attraction_cities = await db.attractions.distinct("city")
    
    all_cities = set(flight_origins + flight_destinations + hotel_cities + restaurant_cities + attraction_cities)
    return {"cities": sorted(list(all_cities))}


@api_router.get("/recommendations")
async def get_recommendations():
    """Return a small set of recommended deals for the home page."""
    cheapest_flights = await db.flights.find({}, {"_id": 0}).sort("price", 1).limit(5).to_list(5)
    cheapest_hotels = await db.hotels.find({}, {"_id": 0}).sort("price_per_night", 1).limit(5).to_list(5)
    return {"cheapest_flights": cheapest_flights, "cheapest_hotels": cheapest_hotels}

@api_router.get("/")
async def root():
    return {"message": "Budget Voyage API"}

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def ensure_flight_departure_dates():
    """Ensure existing flights have a departure_date field for better redirects."""
    cursor = db.flights.find({"departure_date": {"$exists": False}})
    async for doc in cursor:
        days_left = doc.get("days_left", 0) or 0
        try:
            days_left = int(days_left)
        except Exception:
            days_left = 0
        departure_date = (datetime.now(timezone.utc) + timedelta(days=days_left)).date().isoformat()
        await db.flights.update_one({"_id": doc["_id"]}, {"$set": {"departure_date": departure_date}})

@app.on_event("startup")
async def startup_event():
    await load_csv_flights()
    await seed_hotels_restaurants()
<<<<<<< HEAD
    await ensure_flight_departure_dates()
=======
    await load_csv_attractions()
>>>>>>> 97c3a57434d65a1e9e9fa6a84276966fc7406e96
    logger.info("Application started")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
