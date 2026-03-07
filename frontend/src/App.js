import { useState, useEffect } from "react";
import "@/App.css";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Plane, Hotel, UtensilsCrossed, Search, ArrowRight, Star, Clock, MapPin, User, LogOut, Heart, Calendar, MessageCircle, Users } from "lucide-react";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [activeTab, setActiveTab] = useState("flights");
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [token, setToken] = useState(localStorage.getItem("token") || "");
  const [user, setUser] = useState(null);
  const [showAuth, setShowAuth] = useState(false);
  const [isLogin, setIsLogin] = useState(true);
  
  // Auth form
  const [authEmail, setAuthEmail] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [authName, setAuthName] = useState("");
  const [authPhone, setAuthPhone] = useState("");
  
  // Data
  const [flights, setFlights] = useState([]);
  const [hotels, setHotels] = useState([]);
  const [restaurants, setRestaurants] = useState([]);
  const [cities, setCities] = useState([]);
  const [loading, setLoading] = useState(false);
  
  // Profile
  const [showProfile, setShowProfile] = useState(false);
  const [bookings, setBookings] = useState([]);
  const [profileName, setProfileName] = useState("");
  const [profilePhone, setProfilePhone] = useState("");
  
  // Travel Buddy
  const [showBuddy, setShowBuddy] = useState(false);
  const [buddies, setBuddies] = useState([]);
  const [buddyDestination, setBuddyDestination] = useState("");
  const [buddyDates, setBuddyDates] = useState("");
  const [buddyMessage, setBuddyMessage] = useState("");
  
  // Flight filters
  const [flightSource, setFlightSource] = useState("");
  const [flightDestination, setFlightDestination] = useState("");
  const [flightMaxPrice, setFlightMaxPrice] = useState("");
  const [flightStops, setFlightStops] = useState("");

  // Hotel filters
  const [hotelCity, setHotelCity] = useState("");
  const [hotelMaxPrice, setHotelMaxPrice] = useState("");
  const [hotelMinRating, setHotelMinRating] = useState("");

  // Restaurant filters
  const [restaurantCity, setRestaurantCity] = useState("");
  const [restaurantCuisine, setRestaurantCuisine] = useState("");
  const [restaurantMaxPrice, setRestaurantMaxPrice] = useState("");

  useEffect(() => {
    if (token) {
      setIsAuthenticated(true);
      fetchProfile();
    }
    fetchCities();
    searchFlights();
  }, []);

  const fetchCities = async () => {
    try {
      const response = await axios.get(`${API}/cities`);
      setCities(response.data.cities);
    } catch (error) {
      console.error("Error fetching cities:", error);
    }
  };

  const handleAuth = async () => {
    try {
      const endpoint = isLogin ? "/auth/login" : "/auth/register";
      const payload = isLogin 
        ? { email: authEmail, password: authPassword }
        : { email: authEmail, password: authPassword, name: authName, phone: authPhone };
      
      const response = await axios.post(`${API}${endpoint}`, payload);
      const { access_token, user } = response.data;
      
      setToken(access_token);
      setUser(user);
      setIsAuthenticated(true);
      localStorage.setItem("token", access_token);
      setShowAuth(false);
      toast.success(isLogin ? "Welcome back!" : "Account created successfully!");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Authentication failed");
    }
  };

  const fetchProfile = async () => {
    try {
      const response = await axios.get(`${API}/profile`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUser(response.data);
      setProfileName(response.data.name);
      setProfilePhone(response.data.phone || "");
    } catch (error) {
      console.error("Error fetching profile:", error);
    }
  };

  const updateProfile = async () => {
    try {
      await axios.put(`${API}/profile`, 
        { name: profileName, phone: profilePhone },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success("Profile updated!");
      fetchProfile();
    } catch (error) {
      toast.error("Failed to update profile");
    }
  };

  const fetchBookings = async () => {
    try {
      const response = await axios.get(`${API}/bookings`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setBookings(response.data);
    } catch (error) {
      console.error("Error fetching bookings:", error);
    }
  };

  const handleLogout = () => {
    setToken("");
    setUser(null);
    setIsAuthenticated(false);
    localStorage.removeItem("token");
    toast.success("Logged out successfully");
  };

  const searchFlights = async () => {
    setLoading(true);
    try {
      const params = {};
      if (flightSource) params.source = flightSource;
      if (flightDestination) params.destination = flightDestination;
      if (flightMaxPrice) params.max_price = flightMaxPrice;
      if (flightStops) params.stops = flightStops;

      const response = await axios.get(`${API}/flights`, { params });
      setFlights(response.data);
      toast.success(`Found ${response.data.length} flights`);
    } catch (error) {
      console.error("Error fetching flights:", error);
      toast.error("Failed to fetch flights");
    } finally {
      setLoading(false);
    }
  };

  const searchHotels = async () => {
    setLoading(true);
    try {
      const params = {};
      if (hotelCity) params.city = hotelCity;
      if (hotelMaxPrice) params.max_price = hotelMaxPrice;
      if (hotelMinRating) params.min_rating = hotelMinRating;

      const response = await axios.get(`${API}/hotels`, { params });
      setHotels(response.data);
      toast.success(`Found ${response.data.length} hotels`);
    } catch (error) {
      console.error("Error fetching hotels:", error);
      toast.error("Failed to fetch hotels");
    } finally {
      setLoading(false);
    }
  };

  const searchRestaurants = async () => {
    setLoading(true);
    try {
      const params = {};
      if (restaurantCity) params.city = restaurantCity;
      if (restaurantCuisine) params.cuisine = restaurantCuisine;
      if (restaurantMaxPrice) params.max_price = restaurantMaxPrice;

      const response = await axios.get(`${API}/restaurants`, { params });
      setRestaurants(response.data);
      toast.success(`Found ${response.data.length} restaurants`);
    } catch (error) {
      console.error("Error fetching restaurants:", error);
      toast.error("Failed to fetch restaurants");
    } finally {
      setLoading(false);
    }
  };

  const handleBooking = async (type, item) => {
    if (!isAuthenticated) {
      toast.error("Please login to save bookings");
      setShowAuth(true);
      return;
    }

    try {
      await axios.post(
        `${API}/bookings`,
        { booking_type: type, item_id: item.id, item_details: item },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success("Booking saved! Redirecting...");
      window.open(item.deal_url, "_blank");
    } catch (error) {
      toast.error("Failed to save booking");
      window.open(item.deal_url, "_blank");
    }
  };

  const createBuddyPost = async () => {
    if (!isAuthenticated) {
      toast.error("Please login to find travel buddies");
      return;
    }

    try {
      await axios.post(
        `${API}/travel-buddies`,
        { destination: buddyDestination, travel_dates: buddyDates, message: buddyMessage },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success("Your post is live! Others can now find you.");
      setBuddyDestination("");
      setBuddyDates("");
      setBuddyMessage("");
      fetchBuddies();
    } catch (error) {
      toast.error("Failed to create post");
    }
  };

  const fetchBuddies = async () => {
    if (!isAuthenticated) return;
    try {
      const params = {};
      if (buddyDestination) params.destination = buddyDestination;
      const response = await axios.get(`${API}/travel-buddies`, {
        params,
        headers: { Authorization: `Bearer ${token}` }
      });
      setBuddies(response.data);
    } catch (error) {
      console.error("Error fetching buddies:", error);
    }
  };

  const getBestDealIndex = (items, priceKey) => {
    if (items.length === 0) return -1;
    let minPrice = Infinity;
    let minIndex = 0;
    items.forEach((item, index) => {
      if (item[priceKey] < minPrice) {
        minPrice = item[priceKey];
        minIndex = index;
      }
    });
    return minIndex;
  };

  return (
    <div className="app-container">
      {/* Navigation Bar */}
      <nav className="navbar">
        <div className="navbar-content">
          <h1 className="navbar-logo" data-testid="navbar-logo">Budget Voyage</h1>
          <div className="navbar-actions">
            {isAuthenticated ? (
              <>
                <Button 
                  variant="ghost" 
                  className="nav-btn"
                  onClick={() => {
                    setShowProfile(true);
                    fetchBookings();
                  }}
                  data-testid="profile-btn"
                >
                  <User className="nav-icon" />
                  {user?.name}
                </Button>
                <Button 
                  variant="ghost" 
                  className="nav-btn buddy-btn"
                  onClick={() => {
                    setShowBuddy(true);
                    fetchBuddies();
                  }}
                  data-testid="buddy-btn"
                >
                  <Users className="nav-icon" />
                  Need a Buddy?
                </Button>
                <Button variant="ghost" className="nav-btn" onClick={handleLogout} data-testid="logout-btn">
                  <LogOut className="nav-icon" />
                </Button>
              </>
            ) : (
              <Button className="login-btn" onClick={() => setShowAuth(true)} data-testid="show-auth-btn">
                Login / Sign Up
              </Button>
            )}
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="hero-section">
        <div className="hero-content">
          <h1 className="hero-title" data-testid="hero-title">Budget Voyage</h1>
          <p className="hero-subtitle" data-testid="hero-subtitle">
            Find the best travel deals across flights, hotels, and restaurants
          </p>
          <div className="hero-features">
            <div className="hero-feature">
              <Plane className="feature-icon" />
              <span>Compare 300k+ Flights</span>
            </div>
            <div className="hero-feature">
              <Hotel className="feature-icon" />
              <span>Hotel Deals</span>
            </div>
            <div className="hero-feature">
              <UtensilsCrossed className="feature-icon" />
              <span>Top Restaurants</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="main-content">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="tabs-container">
          <TabsList className="tabs-list" data-testid="tabs-list">
            <TabsTrigger value="flights" className="tab-trigger" data-testid="tab-flights">
              <Plane className="tab-icon" />
              Flights
            </TabsTrigger>
            <TabsTrigger value="hotels" className="tab-trigger" data-testid="tab-hotels">
              <Hotel className="tab-icon" />
              Hotels
            </TabsTrigger>
            <TabsTrigger value="restaurants" className="tab-trigger" data-testid="tab-restaurants">
              <UtensilsCrossed className="tab-icon" />
              Restaurants
            </TabsTrigger>
          </TabsList>

          {/* Flights Tab */}
          <TabsContent value="flights" className="tab-content">
            <Card className="filter-card">
              <CardHeader>
                <CardTitle className="filter-title" data-testid="flight-filter-title">
                  <Search className="filter-icon" />
                  Search Flights
                </CardTitle>
                <CardDescription>Compare from 300,000+ real flight options</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="filter-grid">
                  <div className="filter-group">
                    <label className="filter-label">From</label>
                    <Select value={flightSource} onValueChange={setFlightSource}>
                      <SelectTrigger data-testid="flight-source-select">
                        <SelectValue placeholder="Select origin" />
                      </SelectTrigger>
                      <SelectContent>
                        {cities.map((city) => (
                          <SelectItem key={city} value={city}>{city}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="filter-group">
                    <label className="filter-label">To</label>
                    <Select value={flightDestination} onValueChange={setFlightDestination}>
                      <SelectTrigger data-testid="flight-destination-select">
                        <SelectValue placeholder="Select destination" />
                      </SelectTrigger>
                      <SelectContent>
                        {cities.map((city) => (
                          <SelectItem key={city} value={city}>{city}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="filter-group">
                    <label className="filter-label">Max Price (₹)</label>
                    <Input
                      type="number"
                      placeholder="e.g., 8000"
                      value={flightMaxPrice}
                      onChange={(e) => setFlightMaxPrice(e.target.value)}
                      data-testid="flight-max-price-input"
                    />
                  </div>
                  <div className="filter-group">
                    <label className="filter-label">Stops</label>
                    <Select value={flightStops} onValueChange={setFlightStops}>
                      <SelectTrigger data-testid="flight-stops-select">
                        <SelectValue placeholder="Any" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="zero">Non-stop</SelectItem>
                        <SelectItem value="one">1 Stop</SelectItem>
                        <SelectItem value="two_or_more">2+ Stops</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="filter-group">
                    <Button onClick={searchFlights} className="search-btn" disabled={loading} data-testid="flight-search-btn">
                      <Search className="btn-icon" />
                      Search Flights
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Flight Results */}
            <div className="results-container">
              <h2 className="results-title" data-testid="flight-results-title">
                Available Flights ({flights.length})
              </h2>
              <div className="results-grid">
                {flights.map((flight, index) => (
                  <Card key={flight.id} className="result-card flight-card" data-testid={`flight-card-${index}`}>
                    {index === getBestDealIndex(flights, "price") && (
                      <Badge className="best-deal-badge" data-testid={`best-deal-badge-${index}`}>
                        Best Deal
                      </Badge>
                    )}
                    <CardHeader>
                      <CardTitle className="result-card-title">{flight.airline}</CardTitle>
                      <CardDescription className="flight-number">{flight.flight}</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="result-details">
                        <div className="flight-route">
                          <div className="route-city">
                            <span className="city-name">{flight.source_city}</span>
                            <span className="route-time">{flight.departure_time}</span>
                          </div>
                          <div className="route-line">
                            <ArrowRight className="route-arrow" />
                            <span className="route-duration">{flight.duration}h</span>
                          </div>
                          <div className="route-city">
                            <span className="city-name">{flight.destination_city}</span>
                            <span className="route-time">{flight.arrival_time}</span>
                          </div>
                        </div>
                        <div className="flight-meta">
                          <Badge variant="outline" className="meta-badge">
                            {flight.stops === "zero" ? "Non-stop" : flight.stops === "one" ? "1 Stop" : "2+ Stops"}
                          </Badge>
                          <Badge variant="outline" className="meta-badge">{flight.class_type}</Badge>
                        </div>
                        <div className="price-platform">
                          <div className="price">₹{flight.price.toLocaleString()}</div>
                          <div className="platform">{flight.platform}</div>
                        </div>
                      </div>
                      <Button
                        className="book-btn"
                        onClick={() => handleBooking("flight", flight)}
                        data-testid={`flight-book-btn-${index}`}
                      >
                        Book Now <ArrowRight className="btn-icon" />
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          </TabsContent>

          {/* Hotels Tab */}
          <TabsContent value="hotels" className="tab-content">
            <Card className="filter-card">
              <CardHeader>
                <CardTitle className="filter-title" data-testid="hotel-filter-title">
                  <Search className="filter-icon" />
                  Search Hotels
                </CardTitle>
                <CardDescription>Compare hotel prices across booking platforms</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="filter-grid">
                  <div className="filter-group">
                    <label className="filter-label">City</label>
                    <Select value={hotelCity} onValueChange={setHotelCity}>
                      <SelectTrigger data-testid="hotel-city-select">
                        <SelectValue placeholder="Select city" />
                      </SelectTrigger>
                      <SelectContent>
                        {cities.map((city) => (
                          <SelectItem key={city} value={city}>{city}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="filter-group">
                    <label className="filter-label">Max Price per Night (₹)</label>
                    <Input
                      type="number"
                      placeholder="e.g., 10000"
                      value={hotelMaxPrice}
                      onChange={(e) => setHotelMaxPrice(e.target.value)}
                      data-testid="hotel-max-price-input"
                    />
                  </div>
                  <div className="filter-group">
                    <label className="filter-label">Min Rating</label>
                    <Select value={hotelMinRating} onValueChange={setHotelMinRating}>
                      <SelectTrigger data-testid="hotel-min-rating-select">
                        <SelectValue placeholder="Any rating" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="4.0">4.0+</SelectItem>
                        <SelectItem value="4.5">4.5+</SelectItem>
                        <SelectItem value="4.8">4.8+</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="filter-group">
                    <Button onClick={searchHotels} className="search-btn" disabled={loading} data-testid="hotel-search-btn">
                      <Search className="btn-icon" />
                      Search Hotels
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Hotel Results */}
            <div className="results-container">
              <h2 className="results-title" data-testid="hotel-results-title">Available Hotels ({hotels.length})</h2>
              <div className="results-grid">
                {hotels.map((hotel, index) => (
                  <Card key={hotel.id} className="result-card hotel-card" data-testid={`hotel-card-${index}`}>
                    {index === getBestDealIndex(hotels, "price_per_night") && (
                      <Badge className="best-deal-badge" data-testid={`hotel-best-deal-badge-${index}`}>Best Deal</Badge>
                    )}
                    <div className="hotel-image" style={{backgroundImage: `url(${hotel.image_url})`}}></div>
                    <CardHeader>
                      <CardTitle className="result-card-title">{hotel.name}</CardTitle>
                      <CardDescription>
                        <MapPin className="inline-icon" /> {hotel.location}, {hotel.city}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="result-details">
                        <div className="result-row">
                          <Star className="detail-icon star-icon" />
                          <span>{hotel.rating} Rating</span>
                        </div>
                        <div className="amenities">
                          {hotel.amenities.slice(0, 3).map((amenity) => (
                            <Badge key={amenity} variant="outline" className="amenity-badge">{amenity}</Badge>
                          ))}
                        </div>
                        <p className="hotel-description">{hotel.description}</p>
                        <div className="price-platform">
                          <div className="price">₹{hotel.price_per_night.toLocaleString()}/night</div>
                          <div className="platform">{hotel.platform}</div>
                        </div>
                      </div>
                      <Button
                        className="book-btn"
                        onClick={() => handleBooking("hotel", hotel)}
                        data-testid={`hotel-book-btn-${index}`}
                      >
                        Book Now <ArrowRight className="btn-icon" />
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          </TabsContent>

          {/* Restaurants Tab */}
          <TabsContent value="restaurants" className="tab-content">
            <Card className="filter-card">
              <CardHeader>
                <CardTitle className="filter-title" data-testid="restaurant-filter-title">
                  <Search className="filter-icon" />
                  Find Restaurants
                </CardTitle>
                <CardDescription>Discover top-rated restaurants with exclusive offers</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="filter-grid">
                  <div className="filter-group">
                    <label className="filter-label">City</label>
                    <Select value={restaurantCity} onValueChange={setRestaurantCity}>
                      <SelectTrigger data-testid="restaurant-city-select">
                        <SelectValue placeholder="Select city" />
                      </SelectTrigger>
                      <SelectContent>
                        {cities.map((city) => (
                          <SelectItem key={city} value={city}>{city}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="filter-group">
                    <label className="filter-label">Cuisine</label>
                    <Input
                      type="text"
                      placeholder="e.g., Italian, Indian"
                      value={restaurantCuisine}
                      onChange={(e) => setRestaurantCuisine(e.target.value)}
                      data-testid="restaurant-cuisine-input"
                    />
                  </div>
                  <div className="filter-group">
                    <label className="filter-label">Max Avg Price (₹)</label>
                    <Input
                      type="number"
                      placeholder="e.g., 3000"
                      value={restaurantMaxPrice}
                      onChange={(e) => setRestaurantMaxPrice(e.target.value)}
                      data-testid="restaurant-max-price-input"
                    />
                  </div>
                  <div className="filter-group">
                    <Button onClick={searchRestaurants} className="search-btn" disabled={loading} data-testid="restaurant-search-btn">
                      <Search className="btn-icon" />
                      Search Restaurants
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Restaurant Results */}
            <div className="results-container">
              <h2 className="results-title" data-testid="restaurant-results-title">Top Restaurants ({restaurants.length})</h2>
              <div className="results-grid">
                {restaurants.map((restaurant, index) => (
                  <Card key={restaurant.id} className="result-card restaurant-card" data-testid={`restaurant-card-${index}`}>
                    {index === getBestDealIndex(restaurants, "avg_price") && (
                      <Badge className="best-deal-badge" data-testid={`restaurant-best-deal-badge-${index}`}>Best Value</Badge>
                    )}
                    <div className="restaurant-image" style={{backgroundImage: `url(${restaurant.image_url})`}}></div>
                    <CardHeader>
                      <CardTitle className="result-card-title">{restaurant.name}</CardTitle>
                      <CardDescription>
                        <MapPin className="inline-icon" /> {restaurant.location}, {restaurant.city}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="result-details">
                        <div className="result-row">
                          <Star className="detail-icon star-icon" />
                          <span>{restaurant.rating} Rating</span>
                        </div>
                        <div className="result-row">
                          <UtensilsCrossed className="detail-icon" />
                          <span>{restaurant.cuisine}</span>
                        </div>
                        <p className="restaurant-description">{restaurant.description}</p>
                        <div className="price-platform">
                          <div className="price">₹{restaurant.avg_price.toLocaleString()} avg</div>
                          <div className="platform">{restaurant.platform}</div>
                        </div>
                      </div>
                      <Button
                        className="book-btn"
                        onClick={() => handleBooking("restaurant", restaurant)}
                        data-testid={`restaurant-book-btn-${index}`}
                      >
                        View on {restaurant.platform} <ArrowRight className="btn-icon" />
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </div>

      {/* Auth Dialog */}
      <Dialog open={showAuth} onOpenChange={setShowAuth}>
        <DialogContent className="auth-dialog" data-testid="auth-dialog">
          <DialogHeader>
            <DialogTitle>{isLogin ? "Welcome Back" : "Create Account"}</DialogTitle>
            <DialogDescription>
              {isLogin ? "Login to save your bookings and find travel buddies" : "Sign up to get started"}
            </DialogDescription>
          </DialogHeader>
          <div className="auth-form">
            <Input
              type="email"
              placeholder="Email"
              value={authEmail}
              onChange={(e) => setAuthEmail(e.target.value)}
              data-testid="auth-email-input"
            />
            <Input
              type="password"
              placeholder="Password"
              value={authPassword}
              onChange={(e) => setAuthPassword(e.target.value)}
              data-testid="auth-password-input"
            />
            {!isLogin && (
              <>
                <Input
                  type="text"
                  placeholder="Full Name"
                  value={authName}
                  onChange={(e) => setAuthName(e.target.value)}
                  data-testid="auth-name-input"
                />
                <Input
                  type="tel"
                  placeholder="Phone (optional)"
                  value={authPhone}
                  onChange={(e) => setAuthPhone(e.target.value)}
                  data-testid="auth-phone-input"
                />
              </>
            )}
            <Button onClick={handleAuth} className="auth-submit-btn" data-testid="auth-submit-btn">
              {isLogin ? "Login" : "Sign Up"}
            </Button>
            <p className="auth-toggle">
              {isLogin ? "Don't have an account?" : "Already have an account?"}
              <span onClick={() => setIsLogin(!isLogin)} data-testid="auth-toggle-btn">
                {isLogin ? " Sign Up" : " Login"}
              </span>
            </p>
          </div>
        </DialogContent>
      </Dialog>

      {/* Profile Dialog */}
      <Dialog open={showProfile} onOpenChange={setShowProfile}>
        <DialogContent className="profile-dialog" data-testid="profile-dialog">
          <DialogHeader>
            <DialogTitle>My Profile</DialogTitle>
            <DialogDescription>Manage your account and view bookings</DialogDescription>
          </DialogHeader>
          <div className="profile-content">
            <div className="profile-section">
              <h3 className="section-title">Account Details</h3>
              <div className="profile-form">
                <Input
                  type="text"
                  placeholder="Name"
                  value={profileName}
                  onChange={(e) => setProfileName(e.target.value)}
                  data-testid="profile-name-input"
                />
                <Input
                  type="email"
                  value={user?.email}
                  disabled
                  data-testid="profile-email-input"
                />
                <Input
                  type="tel"
                  placeholder="Phone"
                  value={profilePhone}
                  onChange={(e) => setProfilePhone(e.target.value)}
                  data-testid="profile-phone-input"
                />
                <Button onClick={updateProfile} data-testid="profile-update-btn">Update Profile</Button>
              </div>
            </div>
            <div className="profile-section">
              <h3 className="section-title">My Bookings ({bookings.length})</h3>
              <div className="bookings-list">
                {bookings.length === 0 ? (
                  <p className="no-bookings">No bookings yet</p>
                ) : (
                  bookings.slice(0, 5).map((booking) => (
                    <div key={booking.id} className="booking-item" data-testid={`booking-item-${booking.id}`}>
                      <Badge variant="outline">{booking.booking_type}</Badge>
                      <span className="booking-name">{booking.item_details.name || `${booking.item_details.source_city} → ${booking.item_details.destination_city}`}</span>
                      <span className="booking-date">{new Date(booking.booking_date).toLocaleDateString()}</span>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Travel Buddy Dialog */}
      <Dialog open={showBuddy} onOpenChange={setShowBuddy}>
        <DialogContent className="buddy-dialog" data-testid="buddy-dialog">
          <DialogHeader>
            <DialogTitle>Need a Travel Buddy?</DialogTitle>
            <DialogDescription>Find companions traveling to the same destination</DialogDescription>
          </DialogHeader>
          <div className="buddy-content">
            <div className="buddy-create">
              <h3 className="section-title">Post Your Travel Plans</h3>
              <div className="buddy-form">
                <Input
                  type="text"
                  placeholder="Destination"
                  value={buddyDestination}
                  onChange={(e) => setBuddyDestination(e.target.value)}
                  data-testid="buddy-destination-input"
                />
                <Input
                  type="text"
                  placeholder="Travel Dates (e.g., Jan 15-20)"
                  value={buddyDates}
                  onChange={(e) => setBuddyDates(e.target.value)}
                  data-testid="buddy-dates-input"
                />
                <Input
                  type="text"
                  placeholder="Message (e.g., Looking for a hiking buddy)"
                  value={buddyMessage}
                  onChange={(e) => setBuddyMessage(e.target.value)}
                  data-testid="buddy-message-input"
                />
                <div className="buddy-actions">
                  <Button onClick={createBuddyPost} data-testid="buddy-post-btn">Post</Button>
                  <Button variant="outline" onClick={fetchBuddies} data-testid="buddy-search-btn">
                    Search Buddies
                  </Button>
                </div>
              </div>
            </div>
            <div className="buddy-list">
              <h3 className="section-title">Travel Buddies ({buddies.length})</h3>
              {buddies.length === 0 ? (
                <p className="no-buddies">No travel buddies found. Be the first to post!</p>
              ) : (
                buddies.map((buddy) => (
                  <Card key={buddy.id} className="buddy-card" data-testid={`buddy-card-${buddy.id}`}>
                    <CardHeader>
                      <CardTitle className="buddy-name">{buddy.user_name}</CardTitle>
                      <CardDescription>
                        <MapPin className="inline-icon" /> Going to {buddy.destination}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="buddy-details">
                        <div className="buddy-row">
                          <Calendar className="buddy-icon" />
                          <span>{buddy.travel_dates}</span>
                        </div>
                        <div className="buddy-row">
                          <MessageCircle className="buddy-icon" />
                          <span>{buddy.message}</span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Footer */}
      <footer className="footer">
        <p>Budget Voyage - Your Travel Comparison Platform</p>
        <p className="footer-note">We compare deals from top platforms and redirect you to book directly</p>
      </footer>
    </div>
  );
}

export default App;
