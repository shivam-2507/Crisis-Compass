# CrisisCompass: Location-Based Emergency Monitoring System

**CrisisCompass** is a web application that automatically detects your location and monitors local news sources for emergency situations and disasters. It uses semantic analysis to rank incidents by severity, providing a real-time dashboard of local emergencies with the most severe incidents at the top.

---

## **Features**

- **Automatic Location Detection**: Uses browser geolocation to detect your current location
- **Local News Monitoring**: Automatically scrapes local news sources for emergency incidents
- **Intelligent Severity Ranking**:
  - Assigns severity scores based on emergency keywords and context
  - Provides trust scores based on source reliability and keyword analysis
  - Ranks incidents with most severe at the top
- **Real-time Dashboard**:
  - Displays local incidents with severity badges and trust scores
  - Shows location-based emergency monitoring status
  - Automatic refresh functionality for up-to-date information
- **Smart Incident Analysis**:
  - Categorizes incidents by type (fire, medical, flood, etc.)
  - Extracts location information from news content
  - Filters and ranks incidents by relevance and severity

---

## **Technologies Used**

### Backend
- **Python**:
  - `Flask`: For API development and CORS handling
  - `BeautifulSoup`: For web scraping and content extraction
  - `spaCy`: For natural language processing and entity recognition
  - `feedparser`: For RSS feed parsing and news aggregation
  - `geopy`: For geocoding and location services
  - `requests`: For HTTP requests and web scraping
- **Location Services**: Automatic geocoding and reverse geocoding
- **News Aggregation**: RSS feed parsing from multiple sources

### Frontend
- **React**:
  - **Vite**: For fast development and building
  - **Tailwind CSS**: For modern styling and responsive design
  - **Lucide React**: For intuitive icons and UI elements
  - **Axios**: For API communication and data fetching
- **Browser APIs**: Geolocation API for automatic location detection

---

## **Setup**

### Prerequisites
- **Backend**:
  - Python 3.9 or above
  - Internet connection for news scraping
- **Frontend**:
  - Node.js (v14 or above)
  - Modern browser with geolocation support

---

### **Quick Setup**

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/crisis-compass.git
   cd crisis-compass
   ```

2. **Install backend dependencies**:
   ```bash
   python setup_backend.py
   ```

3. **Install frontend dependencies**:
   ```bash
   npm install
   ```

4. **Start the application**:
   ```bash
   # Terminal 1 - Start backend
   cd backend
   python app.py
   
   # Terminal 2 - Start frontend
   npm run dev
   ```

5. **Open your browser** and navigate to `http://localhost:5173`

### **Manual Backend Setup**
If the quick setup doesn't work, follow these steps:

1. **Navigate to backend directory**:
   ```bash
   cd crisis-compass/backend
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Download spaCy English model**:
   ```bash
   python -m spacy download en_core_web_sm
   ```

4. **Start the backend server**:
   ```bash
   python app.py
   ```

### **Frontend Setup**
1. **Navigate to project root**:
   ```bash
   cd crisis-compass
   ```

2. **Install Node.js dependencies**:
   ```bash
   npm install
   ```

3. **Start the development server**:
   ```bash
   npm run dev
   ```

---

## **How It Works**

1. **Location Detection**: When you open the app, it automatically requests your location permission
2. **News Scraping**: The backend scrapes local news sources based on your detected location
3. **Semantic Analysis**: Each news article is analyzed for emergency keywords and severity indicators
4. **Ranking**: Incidents are automatically ranked by severity with the most critical at the top
5. **Real-time Updates**: The dashboard refreshes to show the latest local incidents

---

## **API Endpoints**

- `GET /get-incidents` - Retrieve all stored incidents
- `POST /get-local-incidents` - Scrape and analyze local news based on coordinates
- `POST /scrape` - Manual URL scraping (legacy functionality)

---

## **Privacy & Security**

- Location data is only used locally and not stored on servers
- News scraping respects robots.txt and rate limits
- All analysis is performed locally on your device
