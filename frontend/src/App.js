import { useState, useEffect, useRef } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import "@/App.css";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Plane, Hotel, UtensilsCrossed, Train, Search, ArrowRight, Star, Clock, MapPin, User, LogOut, Heart, Calendar, MessageCircle, Users, Wallet as WalletIcon, Cloud, Sun, Moon, Landmark, Compass } from "lucide-react";
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
  const navigate = useNavigate();
  const location = useLocation();
  const isProfilePage = location.pathname === "/profile";
  
  // Auth form
  const [authEmail, setAuthEmail] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [authName, setAuthName] = useState("");
  const [authPhone, setAuthPhone] = useState("");
  
  // Data
  const [flights, setFlights] = useState([]);
  const [hotels, setHotels] = useState([]);
  const [restaurants, setRestaurants] = useState([]);
  const [attractions, setAttractions] = useState([]);
  const [tripPlan, setTripPlan] = useState(null);
  const [cities, setCities] = useState([]);
  const [recommendations, setRecommendations] = useState({ cheapest_flights: [], cheapest_hotels: [] });
  const [trains, setTrains] = useState([]);
  const [loading, setLoading] = useState(false);
  
  // Profile
  const [bookings, setBookings] = useState([]);
  const [itinerary, setItinerary] = useState([]);
  const [savedTrips, setSavedTrips] = useState([]);
  const [profileTab, setProfileTab] = useState("account");
  const [profileName, setProfileName] = useState("");
  const [profilePhone, setProfilePhone] = useState("");

  // Theme
  const [theme, setTheme] = useState(localStorage.getItem("theme") || "light");
  
  // Travel Buddy
  const [showBuddy, setShowBuddy] = useState(false);
  const [buddies, setBuddies] = useState([]);
  const [buddyDestination, setBuddyDestination] = useState("");
  const [buddyDates, setBuddyDates] = useState("");
  const [buddyMessage, setBuddyMessage] = useState("");

  // Chat / FAQ widget
  const [showChat, setShowChat] = useState(false);
  const [chatInput, setChatInput] = useState("");
  const [chatMessages, setChatMessages] = useState([
    { from: "bot", text: "Hi! I'm BudgetBot. Ask me something about flights, hotels, or how to use the app." },
  ]);

  // Reviews
  const [showReview, setShowReview] = useState(false);
  const [reviewTarget, setReviewTarget] = useState(null);
  const [reviewRating, setReviewRating] = useState(5);
  const [reviewComment, setReviewComment] = useState("");
  const [reviewList, setReviewList] = useState([]);

  // Wallet
  const [showWallet, setShowWallet] = useState(false);
  const [walletBalance, setWalletBalance] = useState(0);
  const [walletAmount, setWalletAmount] = useState(0);

  // Weather
  const [weatherCity, setWeatherCity] = useState("");
  const [weatherForecast, setWeatherForecast] = useState([]);

  // Flight filters
  const [flightSource, setFlightSource] = useState("");
  const [flightDestination, setFlightDestination] = useState("");
  const [flightDate, setFlightDate] = useState("");
  const [flightReturnDate, setFlightReturnDate] = useState("");
  const [flightStops, setFlightStops] = useState("");
  const flightMaxPriceRef = useRef(null);

  // Hotel filters
  const [hotelCity, setHotelCity] = useState("");
  const [hotelMinRating, setHotelMinRating] = useState("");
  const hotelMaxPriceRef = useRef(null);

  // Restaurant filters
  const [restaurantCity, setRestaurantCity] = useState("");
  const [restaurantCuisine, setRestaurantCuisine] = useState("");
  const restaurantMaxPriceRef = useRef(null);
  const [attractionCity, setAttractionCity] = useState("");
  const [attractionMaxFee, setAttractionMaxFee] = useState("");
  const [attractionMinRating, setAttractionMinRating] = useState("");

  // Trip planner
  const [tripCity, setTripCity] = useState("");
  const [tripFromCity, setTripFromCity] = useState("");
  const [tripBudget, setTripBudget] = useState("");
  const [tripStartDate, setTripStartDate] = useState("");
  const [tripEndDate, setTripEndDate] = useState("");
  const [tripPeople, setTripPeople] = useState("1");
  const [tripMode, setTripMode] = useState("Train");
  const [tripInterests, setTripInterests] = useState("");

  // Train search
  const [trainFrom, setTrainFrom] = useState("");
  const [trainTo, setTrainTo] = useState("");
  const [trainFromName, setTrainFromName] = useState("");
  const [trainToName, setTrainToName] = useState("");
  const [trainDate, setTrainDate] = useState("");
  const [stationQueryFrom, setStationQueryFrom] = useState("");
  const [stationQueryTo, setStationQueryTo] = useState("");
  const [stationsFrom, setStationsFrom] = useState([]);
  const [stationsTo, setStationsTo] = useState([]);
  const [useCitySearch, setUseCitySearch] = useState(true);

  useEffect(() => {
    if (token) {
      setIsAuthenticated(true);
      fetchProfile();
      fetchWallet();
    }
    fetchCities();
    searchFlights();
  }, [token]);

  useEffect(() => {
    // Automatically load restaurant recommendations when cities are available.
    if (cities.length && !restaurantCity) {
      const defaultCity = cities[0];
      setRestaurantCity(defaultCity);
      searchRestaurants(defaultCity, "");
    }
  }, [cities, restaurantCity]);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    localStorage.setItem("theme", theme);
  }, [theme]);

  useEffect(() => {
    if (isProfilePage && token) {
      fetchBookings();
      fetchItinerary();
      fetchSavedTrips();
    }
  }, [isProfilePage, token]);

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
      setProfileName(user?.name || "");
      setProfilePhone(user?.phone || "");
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
      await axios.put(
        `${API}/profile`,
        { name: profileName, phone: profilePhone },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success("Profile updated!");
      fetchProfile();
    } catch (error) {
      const status = error.response?.status;
      const detail = error.response?.data?.detail || error.message;
      console.error("Profile update error:", status, detail);
      if (status === 401) {
        toast.error("Session expired, please log in again.");
        handleLogout();
        return;
      }
      toast.error(`Failed to update profile: ${detail}`);
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

  const fetchItinerary = async () => {
    try {
      const response = await axios.get(`${API}/itinerary`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setItinerary(response.data);
    } catch (error) {
      console.error("Error fetching itinerary:", error);
    }
  };

  const fetchSavedTrips = async () => {
    try {
      const response = await axios.get(`${API}/trips/saved`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSavedTrips(response.data);
    } catch (error) {
      console.error("Error fetching saved trips:", error);
    }
  };

  const handleLogout = () => {
    setToken("");
    setUser(null);
    setIsAuthenticated(false);
    localStorage.removeItem("token");
    toast.success("Logged out successfully");
  };

  const getBotReply = (message) => {
    const normalized = message.trim().toLowerCase();

    const faqAnswers = [
      {
        question: "how do i search for flights",
        answer: "Use the Flights tab and enter your origin, destination and dates. Then click 'Search Flights' to see results.",
      },
      {
        question: "how do i save a booking",
        answer: "Login first, then click 'Book Now' on any flight/hotel/restaurant result to save it to your bookings.",
      },
      {
        question: "can i change my profile",
        answer: "Open the profile panel (click your name in the top bar) to update your name or phone number.",
      },
      {
        question: "how do i find travel buddies",
        answer: "Click 'Need a Buddy?' in the top bar and post your trip details to find companions.",
      },
      {
        question: "why are prices different",
        answer: "We compare deals from multiple platforms. Prices can change often, so we always redirect you to the provider for the latest rate.",
      },
    ];

    const match = faqAnswers.find((faq) => normalized.includes(faq.question));
    if (match) return match.answer;

    if (normalized.includes("flight")) {
      return "Try the Flights tab and use the filters to find the best itinerary.";
    }
    if (normalized.includes("hotel")) {
      return "Use the Hotels tab to compare nightly prices and view details before booking.";
    }
    if (normalized.includes("restaurant")) {
      return "Check the Restaurants tab to find top-rated places and open the booking link.";
    }
    if (normalized.includes("login") || normalized.includes("sign in")) {
      return "Click 'Login / Sign Up' in the top-right to access your account and save your bookings.";
    }
    if (normalized.includes("travel buddy") || normalized.includes("buddy")) {
      return "Use the 'Need a Buddy?' button to post your travel plans and find others going to the same destination.";
    }

    return "I'm here to help! Ask me about searching flights, hotels, restaurants, or how to use the app.";
  };

  const sendChatMessage = () => {
    const trimmed = chatInput.trim();
    if (!trimmed) return;

    setChatMessages((prev) => [...prev, { from: "user", text: trimmed }]);
    setChatInput("");

    const reply = getBotReply(trimmed);
    setTimeout(() => {
      setChatMessages((prev) => [...prev, { from: "bot", text: reply }]);
    }, 300);
  };

  const fetchReviews = async (itemId) => {
    try {
      const response = await axios.get(`${API}/reviews`, { params: { item_id: itemId } });
      setReviewList(response.data);
    } catch (error) {
      console.error("Error fetching reviews:", error);
    }
  };

  const openReviewDialog = async (type, item) => {
    // Allow opening the review dialog even when not authenticated so users can see existing reviews
    // and prepare their review before logging in.
    setReviewTarget({ type, item });
    setReviewRating(5);
    setReviewComment("");
    setShowReview(true);
    await fetchReviews(item.id);
  };

  // Wallet helpers
  const fetchWallet = async () => {
    if (!isAuthenticated) return;
    try {
      const response = await axios.get(`${API}/wallet`, { headers: { Authorization: `Bearer ${token}` } });
      setWalletBalance(response.data.balance || 0);
    } catch (error) {
      console.error("Error fetching wallet:", error);
    }
  };

  const addWalletFunds = async () => {
    if (!isAuthenticated) {
      toast.error("Please login to add funds");
      setShowAuth(true);
      return;
    }
    try {
      await axios.post(
        `${API}/wallet/add`,
        { amount: parseFloat(walletAmount) || 0 },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success("Wallet topped up!");
      setWalletAmount(0);
      fetchWallet();
    } catch (error) {
      console.error("Error adding funds:", error);
      toast.error("Failed to add funds");
    }
  };

  // Weather helpers
  const fetchWeather = async (city) => {
    try {
      const response = await axios.get(`${API}/weather`, { params: { city } });
      setWeatherForecast(response.data.forecast || []);
    } catch (error) {
      console.error("Error fetching weather:", error);
      toast.error("Could not load weather");
    }
  };

  const openWeather = (city) => {
    const selectedCity = city || (cities.length ? cities[0] : "Mumbai");
    if (!selectedCity) {
      toast.error("Please select a city to view weather");
      return;
    }

    setWeatherCity(selectedCity);
    setWeatherForecast([]);
    fetchWeather(selectedCity);
  };



  const submitReview = async () => {
    if (!isAuthenticated) {
      toast.error("Please login to submit a review");
      setShowAuth(true);
      return;
    }

    if (!reviewTarget) return;

    if (!reviewComment.trim()) {
      toast.error("Please add a comment to submit a review");
      return;
    }

    if (reviewRating < 1 || reviewRating > 5) {
      toast.error("Rating must be between 1 and 5");
      return;
    }

    try {
      await axios.post(
        `${API}/reviews`,
        {
          item_id: reviewTarget.item.id,
          item_type: reviewTarget.type,
          rating: reviewRating,
          comment: reviewComment,
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success("Review submitted!");
      setReviewComment("");
      setReviewRating(5);
      await fetchReviews(reviewTarget.item.id);
    } catch (error) {
      console.error("Error submitting review:", error);
      const errMsg = error.response?.data?.detail || error.response?.data || error.message;
      toast.error(`Failed to submit review: ${errMsg}`);
    }
  };

  const searchFlights = async () => {
    setLoading(true);
    try {
      const params = {};
      if (flightSource) params.source = flightSource;
      if (flightDestination) params.destination = flightDestination;
      if (flightDate) params.departure_date = flightDate;
      if (flightReturnDate) params.return_date = flightReturnDate;
      const flightMaxPriceValue = flightMaxPriceRef.current?.value || "";
      const flightMaxPriceNumeric = parseFloat(flightMaxPriceValue);
      if (!Number.isNaN(flightMaxPriceNumeric)) params.max_price = flightMaxPriceNumeric;
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
      const hotelMaxPriceValue = hotelMaxPriceRef.current?.value || "";
      const hotelMaxPriceNumeric = parseFloat(hotelMaxPriceValue);
      if (!Number.isNaN(hotelMaxPriceNumeric)) params.max_price = hotelMaxPriceNumeric;
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

  const searchRestaurants = async (overrideCity, overrideCuisine) => {
    const params = {};
    const city = overrideCity ?? restaurantCity;
    const cuisine = overrideCuisine ?? restaurantCuisine;
    console.log('searchRestaurants called', {overrideCity, city, overrideCuisine, cuisine});

    setLoading(true);
    try {
      if (city) params.city = city;
      if (cuisine) params.cuisine = cuisine;
      const restaurantMaxPriceValue = restaurantMaxPriceRef.current?.value || "";
      const restaurantMaxPriceNumeric = parseFloat(restaurantMaxPriceValue);
      if (!Number.isNaN(restaurantMaxPriceNumeric)) params.max_price = restaurantMaxPriceNumeric;

      console.log('params', params);

      const response = await axios.get(`${API}/restaurants`, { params });
      const restaurantsFound = response.data || [];

      // If no results found and a cuisine filter was applied, retry without cuisine.
      if (restaurantsFound.length === 0 && cuisine) {
        const retryParams = { ...params };
        delete retryParams.cuisine;
        const retryResponse = await axios.get(`${API}/restaurants`, { params: retryParams });
        const retryResults = retryResponse.data || [];
        setRestaurants(retryResults);
        if (retryResults.length > 0) {
          toast.success(`No restaurants matched "${cuisine}" - showing all in ${city || "selected city"}`);
        } else {
          toast.success(`Found ${retryResults.length} restaurants`);
        }
      } else {
        setRestaurants(restaurantsFound);
        toast.success(`Found ${restaurantsFound.length} restaurants`);
      }
    } catch (error) {
      console.error("Error fetching restaurants:", error);
      toast.error("Failed to fetch restaurants");
    } finally {
      setLoading(false);
    }
  };

  const searchAttractions = async () => {
    setLoading(true);
    try {
      const params = {};
      if (attractionCity) params.city = attractionCity;
      if (attractionMaxFee) params.max_fee = attractionMaxFee;
      if (attractionMinRating) params.min_rating = attractionMinRating;

      const response = await axios.get(`${API}/attractions`, { params });
      const attractionsData = Array.isArray(response.data)
        ? response.data
        : response.data?.attractions || [];
      setAttractions(attractionsData);
      toast.success(`Found ${attractionsData.length} attractions`);
    } catch (error) {
      console.error("Error fetching attractions:", error);
      toast.error("Failed to fetch attractions");
    } finally {
      setLoading(false);
    }
  };

  const createTripPlan = async () => {
    if (!tripCity || !tripBudget || !tripStartDate || !tripEndDate) {
      toast.error("Please fill city, budget, and dates");
      return;
    }
    setLoading(true);
    try {
      const payload = {
        from_city: tripFromCity || undefined,
        city: tripCity,
        budget: Number(tripBudget),
        start_date: tripStartDate,
        end_date: tripEndDate,
        people: Number(tripPeople || 1),
        travel_mode: tripMode,
        interests: tripInterests
          ? tripInterests.split(",").map((s) => s.trim()).filter(Boolean)
          : undefined,
      };
      const response = await axios.post(`${API}/recommendations`, payload);
      setTripPlan(response.data);
      toast.success("Trip plan created");
    } catch (error) {
      console.error("Error creating trip plan:", error);
      toast.error(error.response?.data?.detail || "Failed to create trip plan");
    } finally {
      setLoading(false);
    }
  };

  const saveTripPlanToItinerary = async () => {
    if (!tripPlan?.plan?.length) return;
    for (const day of tripPlan.plan) {
      for (const attraction of day.attractions || []) {
        await saveToItinerary("attraction", attraction);
      }
    }
  };

  const saveTripPlan = async () => {
    if (!tripPlan) return;
    if (!isAuthenticated) {
      toast.error("Please login to save trips");
      setShowAuth(true);
      return;
    }
    try {
      await axios.post(
        `${API}/trips/saved`,
        { title: `${tripPlan.city} Trip`, trip_details: tripPlan },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success("Trip saved");
      fetchSavedTrips();
    } catch (error) {
      toast.error("Failed to save trip");
    }
  };

  const removeSavedTrip = async (tripId) => {
    try {
      await axios.delete(`${API}/trips/saved/${tripId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success("Saved trip removed");
      fetchSavedTrips();
    } catch (error) {
      toast.error("Failed to remove trip");
    }
  };

  const searchTrains = async () => {
    setLoading(true);
    try {
      let response;
      if (useCitySearch) {
        if (!stationQueryFrom.trim() || !stationQueryTo.trim()) {
          toast.error("Enter source and destination cities");
          setLoading(false);
          return;
        }
        response = await axios.get(`${API}/trains/between-cities`, {
          params: { from_city: stationQueryFrom, to_city: stationQueryTo, date: trainDate || undefined }
        });
      } else {
        if (!trainFrom.trim() || !trainTo.trim()) {
          toast.error("Enter source and destination station codes");
          setLoading(false);
          return;
        }
        response = await axios.get(`${API}/trains/between`, {
          params: { from: trainFrom, to: trainTo, date: trainDate || undefined }
        });
      }
      setTrains(response.data);
      toast.success(`Found ${response.data.length} trains`);
    } catch (error) {
      console.error("Error fetching trains:", error);
      toast.error("Failed to fetch trains");
    } finally {
      setLoading(false);
    }
  };

  const searchStations = async (kind) => {
    const query = kind === "from" ? stationQueryFrom : stationQueryTo;
    if (!query.trim()) {
      toast.error("Enter a city or station name");
      return;
    }
    try {
      const response = await axios.get(`${API}/stations`, { params: { query } });
      if (kind === "from") {
        setStationsFrom(response.data || []);
      } else {
        setStationsTo(response.data || []);
      }
      toast.success(`Found ${response.data.length} stations`);
    } catch (error) {
      console.error("Error fetching stations:", error);
      toast.error("Failed to fetch stations");
    }
  };

  const getRedirectUrl = (type, item, date, returnDate) => {
    // For flights we use Google Flights search with the source/destination prefilled
    const getAirportCode = (city) => {
      if (!city) return "";
      const normalized = city.trim().toUpperCase();
      const mapping = {
        DELHI: "DEL",
        MUMBAI: "BOM",
        BENGALURU: "BLR",
        BANGALORE: "BLR",
        CHENNAI: "MAA",
        HYDERABAD: "HYD",
        KOLKATA: "CCU",
        GOA: "GOI",
        JAIPUR: "JAI",
        PUNE: "PNQ",
        AHMEDABAD: "AMD",
        COIMBATORE: "CJB",
        TRIVANDRUM: "TRV",
        VADODARA: "BDQ",
        LUCKNOW: "LKO",
      };
      return mapping[normalized] || normalized.slice(0, 3);
    };

    const dateParam = date ? date : item.departure_date;
    const returnParam = returnDate ? returnDate : item.return_date;

    if (type === "flight") {
      const srcCode = getAirportCode(item.source_city);
      const dstCode = getAirportCode(item.destination_city);
      const departure = dateParam || "";
      const ret = returnParam || "";

      // Airline-specific booking URLs (common ones) so users go to the search page, not homepage.
      const airlineKey = (item.airline || "").toString().trim().toUpperCase().replace(/\s+/g, "_");
      const airlineUrls = {
        INDIGO: (s, d, dep, ret) =>
          `https://www.goindigo.in/?origin=${s}&destination=${d}&departDate=${dep}${ret ? `&returnDate=${ret}` : ""}`,
        SPICEJET: (s, d, dep, ret) =>
          `https://book.spicejet.com/?origin=${s}&destination=${d}&tripType=O&departureDate=${dep}${ret ? `&returnDate=${ret}` : ""}`,
        VISTARA: (s, d, dep, ret) =>
          `https://www.airvistara.com/in/en/book-flight?departureStation=${s}&arrivalStation=${d}&departureDate=${dep}${ret ? `&returnDate=${ret}` : ""}`,
        GO_FIRST: (s, d, dep, ret) =>
          `https://book.gofirst.com/flights?from=${s}&to=${d}&depart=${dep}${ret ? `&return=${ret}` : ""}`,
        AIR_ASIA: (s, d, dep, ret) =>
          `https://www.airasia.com/en/gb?origin=${s}&destination=${d}&departureDate=${dep}${ret ? `&returnDate=${ret}` : ""}`,
        AIR_INDIA: (s, d, dep, ret) =>
          `https://www.airindia.in/booking/flight-search.htm?origin=${s}&destination=${d}&departureDate=${dep}${ret ? `&returnDate=${ret}` : ""}`,
      };

      if (airlineUrls[airlineKey]) {
        return airlineUrls[airlineKey](srcCode, dstCode, departure, ret);
      }

      // Use the platform/deal_url if it exists and is a valid URL
      if (item.deal_url) {
        try {
          const url = new URL(item.deal_url);
          url.searchParams.set("origin", srcCode);
          url.searchParams.set("destination", dstCode);
          if (departure) url.searchParams.set("departDate", departure);
          if (ret) url.searchParams.set("returnDate", ret);
          return url.toString();
        } catch (e) {
          // if item.deal_url is not a valid URL, fall back to Google Flights
        }
      }

      // Fallback to Google Flights
      const retPart = ret ? `*${dstCode}.${srcCode}.${ret}` : "";
      return `https://www.google.com/flights?hl=en#flt=${srcCode}.${dstCode}.${departure}${retPart}`;
    }

    // For hotels we direct to a search / booking page on the corresponding platform
    if (type === "hotel") {
      const city = encodeURIComponent(item.city || item.location || "");
      const hotelName = encodeURIComponent(item.name || "");

      if (item.platform?.toLowerCase().includes("booking")) {
        return `https://www.booking.com/searchresults.html?ss=${city}`;
      }
      if (item.platform?.toLowerCase().includes("makemytrip")) {
        return `https://www.makemytrip.com/hotels/?city=${city}`;
      }
      if (item.platform?.toLowerCase().includes("agoda")) {
        return `https://www.agoda.com/search?city=${city}`;
      }
      if (item.platform?.toLowerCase().includes("expedia")) {
        return `https://www.expedia.co.in/Hotel-Search?destination=${city}`;
      }

      // Fallback: Google Hotels search
      return `https://www.google.com/travel/hotels?q=${city}`;
    }

    // For restaurants we direct to Google Maps with the cuisine/city
    if (type === "restaurant") {
      const city = encodeURIComponent(item.city || item.location || "");
      const cuisine = encodeURIComponent(item.cuisine || "");
      const query = `${cuisine}${cuisine && city ? " in " : ""}${city}`.trim();
      return `https://www.google.com/maps/search/${query}`;
    }

    return item.deal_url;
  };

  const handleBooking = async (type, item, date, returnDate) => {
    if (!isAuthenticated) {
      toast.error("Please login to save bookings");
      setShowAuth(true);
      return;
    }

    const redirectUrl = getRedirectUrl(type, item, date, returnDate);

    try {
      await axios.post(
        `${API}/bookings`,
        { booking_type: type, item_id: item.id, item_details: item },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success("Booking saved! Redirecting...");
      console.log("Redirecting to:", redirectUrl);
      window.open(redirectUrl, "_blank");
    } catch (error) {
      toast.error("Failed to save booking");
      console.log("Redirecting to (fallback):", redirectUrl);
      window.open(redirectUrl, "_blank");
    }
  };

  const saveToItinerary = async (type, item) => {
    if (!isAuthenticated) {
      toast.error("Please login to save itinerary items");
      setShowAuth(true);
      return;
    }
    try {
      await axios.post(
        `${API}/itinerary`,
        { item_type: type, item_id: item.id || item.name || "", item_details: item },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success("Saved to itinerary");
      fetchItinerary();
    } catch (error) {
      if (error.response?.status === 401) {
        toast.error("Session expired. Please login again.");
        setShowAuth(true);
        return;
      }
      const detail = error.response?.data?.detail || error.response?.data?.message;
      toast.error(detail || "Failed to save to itinerary");
    }
  };

  const removeItineraryItem = async (itemId) => {
    try {
      await axios.delete(`${API}/itinerary/${itemId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success("Removed from itinerary");
      fetchItinerary();
    } catch (error) {
      toast.error("Failed to remove item");
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
                    fetchBookings();
                    fetchItinerary();
                    navigate("/profile");
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
                <Button 
                  variant="ghost"
                  className="nav-btn"
                  onClick={() => {
                    setShowWallet(true);
                    fetchWallet();
                  }}
                  data-testid="wallet-btn"
                >
                  <WalletIcon className="nav-icon" />
                  Wallet
                </Button>
                <Button 
                  variant="ghost"
                  className="nav-btn"
                  onClick={() => openWeather(user?.preferences?.defaultCity || "")}
                  data-testid="weather-btn"
                >
                  <Cloud className="nav-icon" />
                  Weather
                </Button>
                <Button 
                  variant="ghost"
                  className="nav-btn"
                  onClick={() => setTheme((t) => (t === "dark" ? "light" : "dark"))}
                  data-testid="theme-toggle-btn"
                >
                  {theme === "dark" ? <Sun className="nav-icon" /> : <Moon className="nav-icon" />}
                  {theme === "dark" ? "Light" : "Dark"}
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

      {!isProfilePage && (
        <>
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
                <TabsTrigger value="trains" className="tab-trigger" data-testid="tab-trains">
                  <Train className="tab-icon" />
                  Trains
                </TabsTrigger>
                <TabsTrigger value="hotels" className="tab-trigger" data-testid="tab-hotels">
                  <Hotel className="tab-icon" />
                  Hotels
                </TabsTrigger>
                <TabsTrigger value="restaurants" className="tab-trigger" data-testid="tab-restaurants">
                  <UtensilsCrossed className="tab-icon" />
                  Restaurants
                </TabsTrigger>
                <TabsTrigger value="attractions" className="tab-trigger" data-testid="tab-attractions">
                  <Landmark className="tab-icon" />
                  Attractions
                </TabsTrigger>
                <TabsTrigger value="trip" className="tab-trigger" data-testid="tab-trip">
                  <Compass className="tab-icon" />
                  Trip Planner
                </TabsTrigger>
                <TabsTrigger value="weather" className="tab-trigger" data-testid="tab-weather">
                  <Cloud className="tab-icon" />
                  Weather
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
                    <label className="filter-label">Departure Date</label>
                    <Input
                      type="date"
                      value={flightDate}
                      onChange={(e) => setFlightDate(e.target.value)}
                      data-testid="flight-date-input"
                    />
                  </div>
                  <div className="filter-group">
                    <label className="filter-label">Return Date</label>
                    <Input
                      type="date"
                      value={flightReturnDate}
                      onChange={(e) => setFlightReturnDate(e.target.value)}
                      data-testid="flight-return-date-input"
                    />
                  </div>
                  <div className="filter-group">
                    <label className="filter-label">Max Price (₹)</label>
                    <Input
                      type="text"
                      inputMode="numeric"
                      placeholder="e.g., 8000"
                      ref={flightMaxPriceRef}
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
                      <div className="card-actions">
                        <Button
                          className="book-btn"
                          onClick={() => handleBooking(
                            "flight",
                            flight,
                            flightDate || flight.departure_date,
                            flightReturnDate || flight.return_date
                          )}
                          data-testid={`flight-book-btn-${index}`}
                        >
                          Book Now <ArrowRight className="btn-icon" />
                        </Button>
                        <Button
                          variant="outline"
                          className="review-btn"
                          onClick={() => openReviewDialog("flight", flight)}
                          data-testid={`flight-review-btn-${index}`}
                        >
                          Write Review
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          </TabsContent>

          {/* Trains Tab */}
          <TabsContent value="trains" className="tab-content">
            <Card className="filter-card">
              <CardHeader>
                <CardTitle className="filter-title" data-testid="train-filter-title">
                  <Search className="filter-icon" />
                  Search Trains
                </CardTitle>
                <CardDescription>Search by source, destination, and date</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="filter-grid">
                  <div className="filter-group">
                    <label className="filter-label">Search Mode</label>
                    <Select value={useCitySearch ? "city" : "station"} onValueChange={(v) => setUseCitySearch(v === "city")}>
                      <SelectTrigger data-testid="train-search-mode">
                        <SelectValue placeholder="Choose search mode" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="city">By City (Recommended)</SelectItem>
                        <SelectItem value="station">By Station Code</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="filter-group">
                    <label className="filter-label">From</label>
                    <div className="station-search">
                      <Input
                        type="text"
                        placeholder={useCitySearch ? "Enter source city" : "Search source station"}
                        value={stationQueryFrom}
                        onChange={(e) => setStationQueryFrom(e.target.value)}
                        data-testid="station-query-from-input"
                      />
                      {!useCitySearch && (
                        <Button
                          onClick={() => searchStations("from")}
                          className="search-btn"
                          disabled={loading}
                          data-testid="station-search-from-btn"
                        >
                          <Search className="btn-icon" />
                          Find
                        </Button>
                      )}
                    </div>
                    {!useCitySearch && (
                      <Select
                        value={trainFrom}
                        onValueChange={(value) => {
                          setTrainFrom(value);
                          const match = stationsFrom.find((s) => s.code === value);
                          setTrainFromName(match?.name || "");
                        }}
                      >
                        <SelectTrigger data-testid="train-from-input">
                          <SelectValue placeholder="Select source station" />
                        </SelectTrigger>
                        <SelectContent>
                          {stationsFrom.map((station) => (
                            <SelectItem key={`${station.code}-${station.name}`} value={station.code}>
                              {station.name} ({station.code})
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    )}
                  </div>
                  <div className="filter-group">
                    <label className="filter-label">To</label>
                    <div className="station-search">
                      <Input
                        type="text"
                        placeholder={useCitySearch ? "Enter destination city" : "Search destination station"}
                        value={stationQueryTo}
                        onChange={(e) => setStationQueryTo(e.target.value)}
                        data-testid="station-query-to-input"
                      />
                      {!useCitySearch && (
                        <Button
                          onClick={() => searchStations("to")}
                          className="search-btn"
                          disabled={loading}
                          data-testid="station-search-to-btn"
                        >
                          <Search className="btn-icon" />
                          Find
                        </Button>
                      )}
                    </div>
                    {!useCitySearch && (
                      <Select
                        value={trainTo}
                        onValueChange={(value) => {
                          setTrainTo(value);
                          const match = stationsTo.find((s) => s.code === value);
                          setTrainToName(match?.name || "");
                        }}
                      >
                        <SelectTrigger data-testid="train-to-input">
                          <SelectValue placeholder="Select destination station" />
                        </SelectTrigger>
                        <SelectContent>
                          {stationsTo.map((station) => (
                            <SelectItem key={`${station.code}-${station.name}-to`} value={station.code}>
                              {station.name} ({station.code})
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    )}
                  </div>
                  <div className="filter-group">
                    <label className="filter-label">Date</label>
                    <Input
                      type="date"
                      value={trainDate}
                      onChange={(e) => setTrainDate(e.target.value)}
                      data-testid="train-date-input"
                    />
                  </div>
                  <div className="filter-group">
                    <Button onClick={searchTrains} className="search-btn" disabled={loading} data-testid="train-search-btn">
                      <Search className="btn-icon" />
                      Search Trains
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Train Results */}
            <div className="results-container">
              <h2 className="results-title" data-testid="train-results-title">
                Available Trains ({trains.length})
              </h2>
              {(trainFromName || trainToName || stationQueryFrom || stationQueryTo) && (
                <p className="results-subtitle">
                  {useCitySearch ? (stationQueryFrom || "Source") : (trainFromName || trainFrom || "Source")} → {useCitySearch ? (stationQueryTo || "Destination") : (trainToName || trainTo || "Destination")}
                </p>
              )}
              <div className="results-grid">
                {trains.map((trainItem, index) => (
                  <Card key={trainItem.id || index} className="result-card train-card" data-testid={`train-card-${index}`}>
                    <CardHeader>
                      <CardTitle className="result-card-title">{trainItem.train_name || "Unknown Train"}</CardTitle>
                      <CardDescription className="train-number">{trainItem.train_number}</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="result-details">
                        <div className="result-row">
                          <MapPin className="detail-icon" />
                          <span>{useCitySearch ? (stationQueryFrom || "Source") : (trainFromName || "Source")} → {useCitySearch ? (stationQueryTo || "Destination") : (trainToName || "Destination")}</span>
                        </div>
                        {trainItem.departure_time && (
                          <div className="result-row">
                            <Clock className="detail-icon" />
                            <span>{trainItem.departure_time} - {trainItem.arrival_time}</span>
                          </div>
                        )}
                        {trainItem.travel_time && (
                          <div className="result-row">
                            <span>Travel Time: {trainItem.travel_time}</span>
                          </div>
                        )}
                      </div>
                      <Button
                        className="book-btn"
                        onClick={() => {
                          const url = trainItem.booking_url || "https://www.irctc.co.in/nget/train-search";
                          window.open(url, "_blank");
                        }}
                        data-testid={`train-book-btn-${index}`}
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
                      type="text"
                      inputMode="numeric"
                      placeholder="e.g., 10000"
                      ref={hotelMaxPriceRef}
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
                      <div className="card-actions">
                        <Button
                          className="book-btn"
                          onClick={() => handleBooking("hotel", hotel)}
                          data-testid={`hotel-book-btn-${index}`}
                        >
                          Book Now <ArrowRight className="btn-icon" />
                        </Button>
                        <Button
                          variant="outline"
                          className="review-btn"
                          onClick={() => openReviewDialog("hotel", hotel)}
                          data-testid={`hotel-review-btn-${index}`}
                        >
                          Write Review
                        </Button>
                      </div>
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
                    <Select value={restaurantCity} onValueChange={(val) => { setRestaurantCity(val); searchRestaurants(val, restaurantCuisine); }}>
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
                      type="text"
                      inputMode="numeric"
                      placeholder="e.g., 3000"
                      ref={restaurantMaxPriceRef}
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
                      <div className="card-actions">
                        <Button
                          className="book-btn"
                          onClick={() => handleBooking("restaurant", restaurant)}
                          data-testid={`restaurant-book-btn-${index}`}
                        >
                          View on {restaurant.platform} <ArrowRight className="btn-icon" />
                        </Button>
                        <Button
                          variant="outline"
                          className="review-btn"
                          onClick={() => openReviewDialog("restaurant", restaurant)}
                          data-testid={`restaurant-review-btn-${index}`}
                        >
                          Write Review
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          </TabsContent>

          {/* Weather Tab */}
          <TabsContent value="weather" className="tab-content">
            <Card className="filter-card">
              <CardHeader>
                <CardTitle className="filter-title">
                  <Cloud className="filter-icon" />
                  Weather Forecast
                </CardTitle>
                <CardDescription>See 7‑day forecast for a city</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="filter-grid">
                  <div className="filter-group">
                    <label className="filter-label">City</label>
                    <Select value={weatherCity} onValueChange={openWeather}>
                      <SelectTrigger>
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
                    <Button onClick={() => fetchWeather(weatherCity)} className="search-btn" disabled={loading || !weatherCity} data-testid="weather-search-btn">
                      <Search className="btn-icon" />
                      Get Forecast
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            {weatherForecast.length > 0 && (
              <div className="results-container">
                <h2 className="results-title">Forecast for {weatherCity}</h2>
                <div className="results-grid">
                  {weatherForecast.map((day, idx) => (
                    <Card key={idx} className="result-card weather-card">
                      <CardContent>
                        <div className="result-details">
                          <div className="result-row">
                            <span className="detail-label">{day.date}</span>
                          </div>
                          <div className="result-row">
                            <span>High: {day.temp_max}°C</span>
                          </div>
                          <div className="result-row">
                            <span>Low: {day.temp_min}°C</span>
                          </div>
                          {day.precip !== null && (
                            <div className="result-row">
                              <span>Precip: {day.precip} mm</span>
                            </div>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            )}
          </TabsContent>

          {/* Attractions Tab */}
          <TabsContent value="attractions" className="tab-content">
            <Card className="filter-card">
              <CardHeader>
                <CardTitle className="filter-title" data-testid="attraction-filter-title">
                  <Search className="filter-icon" />
                  Find Attractions
                </CardTitle>
                <CardDescription>Discover popular attractions in your city</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="filter-grid">
                  <div className="filter-group">
                    <label className="filter-label">City</label>
                    <Select value={attractionCity} onValueChange={setAttractionCity}>
                      <SelectTrigger data-testid="attraction-city-select">
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
                    <label className="filter-label">Max Fee (?)</label>
                    <Input
                      type="number"
                      placeholder="e.g., 200"
                      value={attractionMaxFee}
                      onChange={(e) => setAttractionMaxFee(e.target.value)}
                      data-testid="attraction-max-fee-input"
                    />
                  </div>
                  <div className="filter-group">
                    <label className="filter-label">Min Rating</label>
                    <Select value={attractionMinRating} onValueChange={setAttractionMinRating}>
                      <SelectTrigger data-testid="attraction-min-rating-select">
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
                    <Button onClick={searchAttractions} className="search-btn" disabled={loading} data-testid="attraction-search-btn">
                      <Search className="btn-icon" />
                      Search Attractions
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            <div className="results-container">
              <h2 className="results-title" data-testid="attraction-results-title">
                Attractions ({attractions.length})
              </h2>
              <div className="results-grid">
                {attractions.map((attraction, index) => (
                  <Card key={attraction.id || index} className="result-card attraction-card" data-testid={`attraction-card-${index}`}>
                    <CardHeader>
                      <CardTitle className="result-card-title">{attraction.name}</CardTitle>
                      <CardDescription>
                        <MapPin className="inline-icon" /> {attraction.city}, {attraction.state}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="result-details">
                        <div className="result-row">
                          <Star className="detail-icon star-icon" />
                          <span>{attraction.rating} Rating</span>
                        </div>
                        <div className="result-row">
                          <Badge variant="outline" className="meta-badge">{attraction.attraction_type}</Badge>
                        </div>
                        <div className="price-platform">
                          <div className="price">Rs. {Number(attraction.entrance_fee || 0).toLocaleString()}</div>
                          <div className="platform">{attraction.best_time}</div>
                        </div>
                      </div>
                      <Button
                        className="book-btn"
                        onClick={() => saveToItinerary("attraction", attraction)}
                        data-testid={`attraction-save-btn-${index}`}
                      >
                        Save to Itinerary <ArrowRight className="btn-icon" />
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          </TabsContent>

          {/* Trip Planner Tab */}
          <TabsContent value="trip" className="tab-content">
            <Card className="filter-card">
              <CardHeader>
                <CardTitle className="filter-title" data-testid="trip-filter-title">
                  <Compass className="filter-icon" />
                  Plan a Trip
                </CardTitle>
                <CardDescription>Answer a few questions and get a budget-friendly itinerary</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="filter-grid">
                  <div className="filter-group">
                    <label className="filter-label">From City</label>
                    <Input
                      type="text"
                      placeholder="Optional origin city"
                      value={tripFromCity}
                      onChange={(e) => setTripFromCity(e.target.value)}
                      data-testid="trip-from-city"
                    />
                  </div>
                  <div className="filter-group">
                    <label className="filter-label">City</label>
                    <Select value={tripCity} onValueChange={setTripCity}>
                      <SelectTrigger data-testid="trip-city-select">
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
                    <label className="filter-label">Budget (₹)</label>
                    <Input
                      type="number"
                      placeholder="e.g., 5000"
                      value={tripBudget}
                      onChange={(e) => setTripBudget(e.target.value)}
                      data-testid="trip-budget-input"
                    />
                  </div>
                  <div className="filter-group">
                    <label className="filter-label">Start Date</label>
                    <Input
                      type="date"
                      value={tripStartDate}
                      onChange={(e) => setTripStartDate(e.target.value)}
                      data-testid="trip-start-date"
                    />
                  </div>
                  <div className="filter-group">
                    <label className="filter-label">End Date</label>
                    <Input
                      type="date"
                      value={tripEndDate}
                      onChange={(e) => setTripEndDate(e.target.value)}
                      data-testid="trip-end-date"
                    />
                  </div>
                  <div className="filter-group">
                    <label className="filter-label">People</label>
                    <Input
                      type="number"
                      min="1"
                      value={tripPeople}
                      onChange={(e) => setTripPeople(e.target.value)}
                      data-testid="trip-people-input"
                    />
                  </div>
                  <div className="filter-group">
                    <label className="filter-label">Travel Mode</label>
                    <Select value={tripMode} onValueChange={setTripMode}>
                      <SelectTrigger data-testid="trip-mode-select">
                        <SelectValue placeholder="Select mode" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Train">Train</SelectItem>
                        <SelectItem value="Flight">Flight</SelectItem>
                        <SelectItem value="Bus">Bus</SelectItem>
                        <SelectItem value="Car">Car</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="filter-group">
                    <label className="filter-label">Interests</label>
                    <Input
                      type="text"
                      placeholder="e.g., historical, religious"
                      value={tripInterests}
                      onChange={(e) => setTripInterests(e.target.value)}
                      data-testid="trip-interests-input"
                    />
                  </div>
                  <div className="filter-group">
                    <Button onClick={createTripPlan} className="search-btn" disabled={loading} data-testid="trip-plan-btn">
                      <Search className="btn-icon" />
                      Create Plan
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            {tripPlan && (
              <div className="results-container">
                <h2 className="results-title">Trip Plan</h2>
                <div className="result-card">
                  <CardHeader>
                    <CardTitle className="result-card-title">{tripPlan.city} Trip</CardTitle>
                    <CardDescription>
                      {tripPlan.days} days • Budget ₹{tripPlan.budget} • Estimated ₹{tripPlan.total_estimated_cost}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="result-details">
                      {tripPlan.transport && (
                        <div className="result-row">
                          <span className="detail-label">Transport:</span>
                          <span>{tripPlan.transport.type} • {tripPlan.transport.name} • ₹{Number(tripPlan.transport.price || 0).toLocaleString()}</span>
                        </div>
                      )}
                      {tripPlan.hotel && (
                        <div className="result-row">
                          <span className="detail-label">Hotel:</span>
                          <span>{tripPlan.hotel.name} • ₹{Number(tripPlan.hotel.total_price || 0).toLocaleString()}</span>
                        </div>
                      )}
                      {tripPlan.plan.map((day, idx) => (
                        <div key={day.date} className="result-row">
                          <span className="detail-label">Day {idx + 1} ({day.date})</span>
                          <span>
                            Attractions: {day.attractions.map((a) => a.name).join(", ") || "None"} •
                            Restaurants: {day.restaurants.map((r) => r.name).join(", ") || "None"} •
                            Day Cost: ₹{Number(day.estimated_cost || 0).toLocaleString()}
                          </span>
                        </div>
                      ))}
                    </div>
                    <Button className="book-btn" onClick={saveTripPlanToItinerary}>
                      Save Plan to Itinerary <ArrowRight className="btn-icon" />
                    </Button>
                    <Button className="book-btn" onClick={saveTripPlan}>
                      Save Trip to Profile <ArrowRight className="btn-icon" />
                    </Button>
                  </CardContent>
                </div>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>
        </>
      )}

      {isProfilePage && (
        <div className="main-content profile-page">
          <Card className="filter-card">
            <CardHeader>
              <CardTitle className="filter-title">My Profile</CardTitle>
              <CardDescription>Manage your account, itinerary, and bookings</CardDescription>
            </CardHeader>
            <CardContent>
              {!isAuthenticated ? (
                <div className="profile-content">
                  <p className="no-bookings">Please login to view your profile details.</p>
                  <div className="buddy-actions">
                    <Button onClick={() => setShowAuth(true)}>Login / Sign Up</Button>
                    <Button variant="outline" onClick={() => navigate("/")}>Back Home</Button>
                  </div>
                </div>
              ) : (
                <div className="profile-content">
                  <Tabs value={profileTab} onValueChange={setProfileTab} className="tabs-container">
                    <TabsList className="tabs-list">
                      <TabsTrigger value="account" className="tab-trigger">Account</TabsTrigger>
                      <TabsTrigger value="itinerary" className="tab-trigger">Itinerary</TabsTrigger>
                      <TabsTrigger value="bookings" className="tab-trigger">Bookings</TabsTrigger>
                      <TabsTrigger value="trips" className="tab-trigger">Saved Trips</TabsTrigger>
                    </TabsList>
                  <TabsContent value="account" className="tab-content">
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
                      <div className="buddy-actions">
                        <Button onClick={updateProfile} data-testid="profile-update-btn">Update Profile</Button>
                        <Button variant="outline" onClick={() => navigate("/")} data-testid="profile-back-btn">Back Home</Button>
                      </div>
                    </div>
                  </div>
                  </TabsContent>
                  <TabsContent value="itinerary" className="tab-content">
                  <div className="profile-section">
                    <h3 className="section-title">My Itinerary ({itinerary.length})</h3>
                    <div className="bookings-list">
                      {itinerary.length === 0 ? (
                        <p className="no-bookings">No itinerary items yet</p>
                      ) : (
                        itinerary.slice(0, 10).map((item) => (
                          <div key={item.id} className="booking-item" data-testid={`itinerary-item-${item.id}`}>
                            <Badge variant="outline">{item.item_type}</Badge>
                            <span className="booking-name">{item.item_details?.name || item.item_id}</span>
                            <Button variant="ghost" onClick={() => removeItineraryItem(item.id)}>Remove</Button>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                  </TabsContent>
                  <TabsContent value="bookings" className="tab-content">
                  <div className="profile-section">
                    <h3 className="section-title">My Bookings ({bookings.length})</h3>
                    <div className="bookings-list">
                      {bookings.length === 0 ? (
                        <p className="no-bookings">No bookings yet</p>
                      ) : (
                        bookings.slice(0, 10).map((booking) => (
                          <div key={booking.id} className="booking-item" data-testid={`booking-item-${booking.id}`}>
                            <Badge variant="outline">{booking.booking_type}</Badge>
                            <span className="booking-name">{booking.item_details.name || `${booking.item_details.source_city} → ${booking.item_details.destination_city}`}</span>
                            <span className="booking-date">{new Date(booking.booking_date).toLocaleDateString()}</span>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                  </TabsContent>
                  <TabsContent value="trips" className="tab-content">
                  <div className="profile-section">
                    <h3 className="section-title">Saved Trips ({savedTrips.length})</h3>
                    <div className="bookings-list">
                      {savedTrips.length === 0 ? (
                        <p className="no-bookings">No saved trips yet</p>
                      ) : (
                        savedTrips.slice(0, 10).map((trip) => (
                          <div key={trip.id} className="booking-item" data-testid={`saved-trip-${trip.id}`}>
                            <Badge variant="outline">trip</Badge>
                            <span className="booking-name">{trip.title}</span>
                            <Button variant="ghost" onClick={() => removeSavedTrip(trip.id)}>Remove</Button>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                  </TabsContent>
                  </Tabs>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

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

      {/* Review Dialog */}
      <Dialog open={showReview} onOpenChange={setShowReview}>
        <DialogContent className="chat-dialog" data-testid="review-dialog">
          <DialogHeader>
            <DialogTitle>{reviewTarget ? `Reviews for ${reviewTarget.item.name || reviewTarget.item.flight || "item"}` : "Reviews"}</DialogTitle>
            <DialogDescription>Share your feedback and read what others are saying.</DialogDescription>
          </DialogHeader>

          <div className="chat-messages" data-testid="review-messages">
            {reviewList.length === 0 ? (
              <div className="chat-message chat-message-bot">No reviews yet. Be the first to leave one!</div>
            ) : (
              reviewList.map((review) => (
                <div key={review.id} className="chat-message chat-message-bot">
                  <div className="chat-message-text">
                    <strong>{review.user_email}</strong> • {review.rating}⭐
                    <div style={{ marginTop: 6 }}>{review.comment}</div>
                  </div>
                </div>
              ))
            )}
          </div>

          {!isAuthenticated && (
            <div className="review-warning" style={{ color: "#f97316", marginBottom: "0.5rem" }}>
              Please log in to submit a review.
            </div>
          )}
          <div className="chat-input-row">
            <Input
              type="number"
              min={1}
              max={5}
              placeholder="Rating (1-5)"
              value={reviewRating}
              onChange={(e) => setReviewRating(Number(e.target.value))}
              data-testid="review-rating-input"
            />
            <Input
              placeholder="Write your review..."
              value={reviewComment}
              onChange={(e) => setReviewComment(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && submitReview()}
              data-testid="review-comment-input"
            />
            <Button
              onClick={submitReview}
              className="chat-send-btn"
              data-testid="review-submit-btn"
              disabled={!isAuthenticated}
            >
              Submit
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Wallet Dialog */}
      <Dialog open={showWallet} onOpenChange={setShowWallet}>
        <DialogContent className="chat-dialog" data-testid="wallet-dialog">
          <DialogHeader>
            <DialogTitle>My Wallet</DialogTitle>
            <DialogDescription>Balance and add funds</DialogDescription>
          </DialogHeader>
          <div className="chat-messages">
            <div className="chat-message chat-message-bot">
              <div className="chat-message-text">
                Current balance: ₹{walletBalance.toLocaleString()}
              </div>
            </div>
          </div>
          <div className="chat-input-row">
            <Input
              type="number"
              min={0}
              placeholder="Amount to add"
              value={walletAmount}
              onChange={(e) => setWalletAmount(e.target.value)}
              data-testid="wallet-amount-input"
            />
            <Button onClick={addWalletFunds} className="chat-send-btn" data-testid="wallet-add-btn">
              Add
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Chat / FAQ widget */}
      <button className="chat-button" onClick={() => setShowChat(true)} data-testid="open-chat-btn">
        <MessageCircle className="chat-icon" />
        <span>Need help?</span>
      </button>

      <Dialog open={showChat} onOpenChange={setShowChat}>
        <DialogContent className="chat-dialog" data-testid="chat-dialog">
          <DialogHeader>
            <DialogTitle>BudgetBot</DialogTitle>
            <DialogDescription>Ask a question or browse the FAQ below.</DialogDescription>
          </DialogHeader>

          <div className="chat-messages" data-testid="chat-messages">
            {chatMessages.map((msg, idx) => (
              <div key={idx} className={`chat-message chat-message-${msg.from}`}>
                <div className="chat-message-text">{msg.text}</div>
              </div>
            ))}
          </div>

          <div className="chat-input-row">
            <Input
              placeholder="Type your question..."
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendChatMessage()}
              data-testid="chat-input"
            />
            <Button onClick={sendChatMessage} className="chat-send-btn" data-testid="chat-send-btn">
              Send
            </Button>
          </div>

          <div className="chat-faq">
            <h4>FAQ</h4>
            <ul>
              <li>How do I search for flights?</li>
              <li>How do I save a booking?</li>
              <li>How do I find travel buddies?</li>
            </ul>
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
