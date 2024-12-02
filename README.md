# CrisisCompass: Emergency Severity Web Scraper

**CrisisCompass** is a web application that analyzes online text to rank the severity of emergency situations, such as natural disasters. By combining web scraping, natural language processing, and an intuitive user interface, it assigns severity levels to incidents and provides trust scores to evaluate information reliability.

---

## **Features**

- **Web Scraping**: Extracts text content from online articles to identify emergency-related information.
- **Severity and Trust Ranking**:
  - Assigns a severity score based on emergency keywords.
  - Provides a trust score based on trust-related keywords.
- **Dynamic Incident Tracking**:
  - Visualizes active incidents with severity badges and trust scores.
  - Sorts incidents by severity score for quick access to critical events.
- **Interactive Frontend**:
  - Enter a URL to fetch and rank emergency content.
  - Displays incidents with categorized icons, severity levels, and locations.

---

## **Technologies Used**

### Backend
- **Python**:
  - `Flask`: For API development.
  - `BeautifulSoup`: For web scraping.
  - `spaCy`: For natural language processing.
- **Logging**: Provides insights into scraping activity.

### Frontend
- **React**:
  - **Material-UI**: For styling and layout.
  - Dynamic components to visualize incidents.
  - Integrated Axios for API communication.

---

## **Setup**

### Prerequisites
- **Backend**:
  - Python 3.9 or above.
- **Frontend**:
  - Node.js (v14 or above).

---

### **Backend Setup**
1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/crisis-compass.git
   cd crisis-compass/backend
