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
import csv
import random

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
    except jwt.JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

# ==================== SEED DATA ====================

async def load_csv_flights():
    existing = await db.flights.count_documents({})
    if existing > 0:
        logger.info(f"Flights already loaded: {existing} documents")
        return
    
    csv_path = ROOT_DIR / 'flights.csv'
    if not csv_path.exists():
        logger.warning("flights.csv not found")
        return
    
    logger.info("Loading flights from CSV...")
    batch = []
    batch_size = 1000
    
    # Booking platforms for redirection
    platforms = [
        {"name": "MakeMyTrip", "url": "https://www.makemytrip.com/flights"},
        {"name": "Cleartrip", "url": "https://www.cleartrip.com/flights"},
        {"name": "Goibibo", "url": "https://www.goibibo.com/flights"},
        {"name": "Expedia", "url": "https://www.expedia.co.in/Flights"},
        {"name": "Yatra", "url": "https://www.yatra.com/flights"},
    ]
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            platform = random.choice(platforms)
            doc = {
                "id": str(uuid.uuid4()),
                "airline": row['airline'].replace('_', ' '),
                "flight": row['flight'],
                "source_city": row['source_city'],
                "destination_city": row['destination_city'],
                "departure_time": row['departure_time'].replace('_', ' '),
                "arrival_time": row['arrival_time'].replace('_', ' '),
                "duration": float(row['duration']),
                "stops": row['stops'],
                "class_type": row['class'],
                "days_left": int(row['days_left']),
                "price": float(row['price']),
                "platform": platform["name"],
                "deal_url": platform["url"]
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

async def seed_hotels_restaurants():
    existing_hotels = await db.hotels.count_documents({})
    if existing_hotels > 0:
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
    
    logger.info("Hotels and restaurants seeded")

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
    current_user: str = Depends(get_current_user)
):
    query = {}
    if destination:
        query["destination"] = {"$regex": destination, "$options": "i"}
    
    # Exclude current user's own posts
    query["user_email"] = {"$ne": current_user}
    
    buddies = await db.travel_buddies.find(query, {"_id": 0}).to_list(1000)
    return buddies

# ==================== FLIGHTS ROUTES ====================

@api_router.get("/flights")
async def get_flights(
    source: Optional[str] = Query(None),
    destination: Optional[str] = Query(None),
    max_price: Optional[float] = Query(None),
    stops: Optional[str] = Query(None),
    limit: int = Query(50, le=200)
):
    query = {}
    if source:
        query["source_city"] = {"$regex": source, "$options": "i"}
    if destination:
        query["destination_city"] = {"$regex": destination, "$options": "i"}
    if max_price:
        query["price"] = {"$lte": max_price}
    if stops:
        query["stops"] = stops
    
    flights = await db.flights.find(query, {"_id": 0}).sort("price", 1).to_list(limit)
    return flights

# ==================== HOTELS ROUTES ====================

@api_router.get("/hotels", response_model=List[Hotel])
async def get_hotels(
    city: Optional[str] = Query(None),
    max_price: Optional[float] = Query(None),
    min_rating: Optional[float] = Query(None)
):
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

@api_router.get("/restaurants", response_model=List[Restaurant])
async def get_restaurants(
    city: Optional[str] = Query(None),
    cuisine: Optional[str] = Query(None),
    max_price: Optional[float] = Query(None),
    min_rating: Optional[float] = Query(None)
):
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

# ==================== CITIES ROUTE ====================

@api_router.get("/cities")
async def get_cities():
    flight_origins = await db.flights.distinct("source_city")
    flight_destinations = await db.flights.distinct("destination_city")
    hotel_cities = await db.hotels.distinct("city")
    restaurant_cities = await db.restaurants.distinct("city")
    
    all_cities = set(flight_origins + flight_destinations + hotel_cities + restaurant_cities)
    return {"cities": sorted(list(all_cities))}

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

@app.on_event("startup")
async def startup_event():
    await load_csv_flights()
    await seed_hotels_restaurants()
    logger.info("Application started")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
