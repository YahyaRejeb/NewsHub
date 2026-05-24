# NewsHub - Full Project Documentation

## Project Overview

**NewsHub** is a modern, full-stack news aggregation web application built with a **Python FastAPI backend** and an **Angular frontend**. It combines curated news articles from external APIs with a personalized user experience, including authentication, premium features, and an AI-powered chatbot assistant.

### Key Features
- **News Aggregation**: Fetches articles from external news APIs (NewsData) by category
- **User Authentication**: Secure login/registration with password hashing
- **Personalization**: Users can save favorite categories and articles
- **Premium Features**: Simulated premium membership with special access to AI assistant
- **AI Chatbot**: Article-aware chat powered by **Ollama** with **qwen3:14b** model
- **Comments System**: Users can post and view comments on articles
- **Live Events**: Support for live streaming events with real-time messaging
- **Profile Management**: Users can manage their profile, interests, and saved articles

---

## Technology Stack

### Backend Technologies
- **Framework**: FastAPI (Python web framework for building APIs)
- **Server**: Uvicorn (ASGI application server)
- **Database**: MySQL 8.0+ with PyMySQL connector
- **ORM**: SQLAlchemy (Object-Relational Mapping)
- **Authentication**: 
  - bcrypt (password hashing)
  - python-jose with cryptography (JWT tokens)
- **AI/Chatbot**: 
  - Ollama (local AI runtime)
  - qwen3:14b (primary generation model)
  - nomic-embed-text (embedding model for retrieval)
- **Real-time**: WebSockets (for live events)
- **External APIs**: NewsData API (news fetching)

### Frontend Technologies
- **Framework**: Angular 21.1.0 (standalone components)
- **Styling**: Bootstrap 5.3.8 + Custom CSS
- **State Management**: RxJS (reactive programming)
- **Routing**: Angular Router
- **Forms**: Angular Reactive Forms and Template-driven Forms
- **HTTP**: Angular HttpClient (for API communication)
- **Build Tools**: Angular CLI, TypeScript 5.9.2

### Environment Configuration
- **Language**: Python 3.x (backend), TypeScript 5.9+ (frontend)
- **Package Managers**: pip (Python), npm 10.9.3 (Node)
- **Database**: MySQL (default)

---

## Project Structure

```
mini-projet/
├── backend/                          # Python FastAPI Backend
│   ├── main.py                       # Main API entry point with all endpoints
│   ├── models.py                     # SQLAlchemy ORM models
│   ├── schemas.py                    # Pydantic request/response schemas
│   ├── crud.py                       # CRUD operations for database
│   ├── database.py                   # Database configuration and connection
│   ├── security.py                   # Authentication and security utilities
│   ├── simple_chatbot.py             # AI chatbot integration with Ollama
│   ├── init_db.sql                   # Initial database schema creation script
│   ├── requirements.txt              # Python dependencies
│   └── test_db.py                    # Database tests
│
├── frontend/                         # Angular Frontend
│   ├── src/
│   │   ├── app/                      # Angular components, services, routing
│   │   ├── index.html                # HTML entry point
│   │   ├── main.ts                   # Bootstrap Angular application
│   │   └── styles.css                # Global CSS styling
│   ├── public/                       # Static assets
│   ├── package.json                  # Node dependencies and scripts
│   ├── angular.json                  # Angular CLI configuration
│   ├── tsconfig.json                 # TypeScript configuration
│   └── proxy.conf.json               # Development proxy configuration
│
├── reports/                          # Test reports and documentation
├── tools/                            # Utility scripts
├── README.md                         # Project setup guide
├── NEWHUB_FRONTEND_REPLICATION_BRIEF.md  # Detailed frontend specifications
└── .gitignore                        # Git ignore rules
```

---

## Backend Architecture

### Database Models (models.py)

#### **User Model**
```python
- id (Primary Key)
- full_name: String(100)
- email: String(100) [Unique, Indexed]
- password_hash: String(255) [Hashed password]
- profile_photo: LONGTEXT [Optional base64 image]
- role: String(20) [Default: "user"]
- is_premium: Boolean [Default: False]
- premium_plan: String(20) [Optional: "monthly" or "annual"]
- premium_since: DateTime [Optional premium activation date]
- created_at: DateTime [Server default: now()]
- Relationships: favorites, comments, interests, live_events, live_messages
```

#### **Interest Model**
```python
- id (Primary Key)
- name: String(50) [Unique, e.g., "Technology", "Business", "Politics", etc.]
- Relationships: users (Many-to-Many), news_articles
```

#### **UserInterest Model (Junction Table)**
```python
- user_id (Foreign Key -> users.id)
- interest_id (Foreign Key -> interests.id)
- Composite Primary Key: (user_id, interest_id)
```

#### **Source Model**
```python
- id (Primary Key)
- source_name: String(100)
- source_url: String(255)
- Unique Constraint: (source_name, source_url)
- Relationships: news_articles
```

#### **News Model**
```python
- id (Primary Key)
- external_id: String(255) [ID from external news API]
- title: String(255)
- content: Text [Full article body]
- image_url: String(255) [Featured image URL]
- article_url: String(500) [Unique link to original article]
- published_at: DateTime [Publication date]
- interest_id: Integer [Foreign Key -> interests.id]
- source_id: Integer [Foreign Key -> source.id]
- datatype: String(50) [e.g., "blog", "news", "press_release"]
- country: String(10) [2-letter country code]
- Relationships: interest, source, favorites, comments
```

#### **Favorite Model**
```python
- user_id (Primary Key, Foreign Key -> users.id)
- news_id (Primary Key, Foreign Key -> news.id)
- saved_at: DateTime [When article was saved]
- Relationships: user, news
```

#### **Comment Model**
```python
- comment_id (Primary Key)
- user_id (Foreign Key -> users.id)
- news_id (Foreign Key -> news.id)
- comment_content: Text [The comment body]
- createdAt: DateTime [Server default: now()]
- Relationships: user, news
```

#### **LiveEvent Model**
```python
- id (Primary Key)
- title: String(200)
- description: Text
- category: String(50)
- cover_image: String(500)
- stream_url: String(500)
- status: String(20) [Default: "upcoming", can be "live", "ended"]
- premium_only: Boolean [Default: True]
- editor_user_id: Integer [Foreign Key -> users.id]
- created_at: DateTime
- started_at: DateTime [Optional]
- ended_at: DateTime [Optional]
- Relationships: editor (User), messages (LiveMessage)
```

#### **LiveMessage Model**
```python
- id (Primary Key)
- live_event_id (Foreign Key -> live_events.id)
- user_id (Foreign Key -> users.id)
- message_type: String(20) [e.g., "chat", "reaction"]
- content: Text
- created_at: DateTime
- Relationships: live_event, user
```

### CRUD Operations (crud.py)

#### **parse_publication_date(value: Optional[str]) -> Optional[datetime]**
- **Purpose**: Parse ISO 8601 date strings from external APIs
- **Process**:
  1. Handles None and empty strings
  2. Replaces trailing 'Z' with '+00:00' for Python compatibility
  3. Uses `datetime.fromisoformat()` for parsing
  4. Removes timezone info (stores as naive datetime)
  5. Returns None on failure (graceful error handling)

#### **get_or_create_interest_id(db: Session, category: Optional[str]) -> Optional[int]**
- **Purpose**: Create or fetch interest category by name (case-insensitive)
- **Process**:
  1. Normalizes input category name
  2. Case-insensitive lookup in database
  3. If exists, returns existing ID
  4. If not exists, creates new Interest with proper capitalization
  5. Commits and returns new ID

#### **upsert_news_record(db: Session, article: schemas.FavoriteArticleData) -> int**
- **Purpose**: Insert or update a news article in the database
- **Process**:
  1. Validates article URL (required)
  2. Gets or creates Source record based on source_name and URL
  3. Gets or creates Interest category
  4. Parses publication date
  5. Combines content and description for article body
  6. Finds or creates News record
  7. Updates all News fields with article data
  8. Flushes to database
  9. Returns News ID

### Database Configuration (database.py)

#### **Connection Setup**
- Reads MySQL credentials from environment variables or uses defaults:
  - `MYSQL_HOST`: localhost
  - `MYSQL_PORT`: 3306
  - `MYSQL_USER`: root
  - `MYSQL_PASSWORD`: (empty)
  - `MYSQL_DATABASE`: newshub1
- Alternative: `DATABASE_URL` environment variable for full connection string

#### **_build_database_url() -> URL**
- Constructs SQLAlchemy connection URL
- Validates it points to MySQL
- Configures charset as utf8mb4

#### **_ensure_database_exists(database_url: URL)**
- Creates database if it doesn't exist
- Uses Unicode collation for proper multilingual support

#### **ensure_schema_extensions()**
- Creates all tables via SQLAlchemy
- Adds missing columns to users table (backward compatibility):
  - profile_photo
  - role
  - is_premium
  - premium_plan
  - premium_since
- Initializes default interests (Technology, Business, Politics, etc.)

#### **get_db() -> Generator[Session]**
- FastAPI dependency for database sessions
- Ensures proper cleanup

### Default Interests
```python
DEFAULT_INTERESTS = (
    "Technology",
    "Business",
    "Politics",
    "Science",
    "Entertainment",
    "Sports",
    "Health",
)
```

### Security (security.py)
- Password hashing with bcrypt
- JWT token generation and validation
- Credential verification

### API Endpoints (main.py)

#### **Authentication Endpoints**
- `POST /login` - User login with email/password
- `POST /complete-signup` - Complete user registration with interests
- `GET /check-email/:email` - Check email availability during signup
- `GET /interests` - Get list of available interest categories

#### **News Endpoints**
- `GET /articles` - Fetch articles by category/filters
- `GET /articles/:id` - Get single article details
- `POST /articles` - Save article to favorites
- `GET /articles/search` - Search articles

#### **User Endpoints**
- `GET /user/profile` - Get current user profile
- `PUT /user/profile` - Update user profile
- `GET /user/preferences` - Get user interests/preferences
- `PUT /user/preferences` - Update user interests

#### **Favorites Endpoints**
- `POST /favorites` - Save article to favorites
- `DELETE /favorites/:news_id` - Remove from favorites
- `GET /favorites-status` - Check if article is saved
- `GET /favorites/:userId` - Get user's saved articles

#### **Comments Endpoints**
- `GET /comments/:news_id` - Get article comments
- `POST /comments` - Post new comment
- `DELETE /comments/:comment_id` - Delete comment

#### **Premium Endpoints**
- `POST /premium/activate` - Simulate premium activation
- `GET /premium/status` - Check premium status

#### **Chatbot Endpoints**
- `GET /chatbot/status` - Check Ollama connection and model availability
- `POST /chatbot/brief` - Generate article brief
- `POST /chatbot/ask` - Send chat message to AI assistant

#### **Live Events Endpoints**
- `GET /live/events` - List live events
- `GET /live/events/:id` - Get live event details
- `WebSocket /ws/live/:event_id` - Real-time chat for live events

### AI Chatbot Integration (simple_chatbot.py)

#### **Ollama Configuration**
- **Host**: `OLLAMA_BASE_URL` environment variable (default: `http://localhost:11434`)
- **Model**: `CHATBOT_MODEL` environment variable (default: `qwen3:14b`)
- **Embedding Model**: Used for article retrieval (nomic-embed-text)

#### **get_chatbot_status() -> dict**
- **Purpose**: Health check for Ollama and model availability
- **Returns**:
  ```json
  {
    "host": "http://localhost:11434",
    "preferredGenerationModel": "qwen3:14b",
    "activeGenerationModel": "qwen3:14b or null",
    "embeddingModel": "nomic-embed-text",
    "connected": true/false,
    "generalReady": true/false,
    "articleBriefReady": true/false,
    "retrievalReady": true/false,
    "installedModels": ["qwen3:14b", "nomic-embed-text"],
    "issues": []
  }
  ```

#### **get_article_brief(article: schemas.FavoriteArticleData) -> dict**
- **Purpose**: Generate a lightweight summary without AI (uses article text directly)
- **Returns**:
  ```json
  {
    "title": "Article Title",
    "sourceName": "Source Name",
    "publishedAt": "2024-01-01T00:00:00",
    "summary": "First sentence or description",
    "longSummary": "First 4 sentences",
    "whyItMatters": "Explanation",
    "keyPoints": ["Point 1", "Point 2", "Point 3"],
    "people": [],
    "organizations": [],
    "places": [],
    "dates": [],
    "importantNumbers": [],
    "timeline": [],
    "suggestedQuestions": ["Summarize this article.", ...],
    "limitations": [],
    "blocked": false
  }
  ```

#### **ask_chatbot(article: FavoriteArticleData, message: str, history: list[ChatTurnData]) -> dict**
- **Purpose**: Send a message to the chatbot and get a response
- **Process**:
  1. Creates system message with article context
  2. Keeps last 4 chat turns in conversation history
  3. Appends current user message
  4. Sends to Ollama `/api/chat` endpoint
  5. Cleans response (removes `<think>` blocks)
  6. Detects limitations (short article warning)
  7. Returns structured response
- **Returns**:
  ```json
  {
    "mode": "grounded",
    "route": "simple_chat",
    "answer": "The assistant's response",
    "evidence": [],
    "confidence": 0.9,
    "limitations": [],
    "cached": false
  }
  ```

#### **Helper Functions**
- **_ollama(path, payload, timeout)**: Makes HTTP requests to Ollama API
- **_clean_answer(text)**: Removes hidden thinking blocks from LLM responses
- **_split_sentences(text)**: Breaks text into sentences for summaries
- **_article_text(article)**: Combines article title, description, and content

---

## Frontend Architecture

### Package Configuration (package.json)
```json
{
  "name": "f-news-1",
  "version": "0.0.0",
  "main-script": "npm start",
  "dependencies": {
    "@angular/common": "^21.1.0",
    "@angular/compiler": "^21.1.0",
    "@angular/core": "^21.1.0",
    "@angular/forms": "^21.1.0",
    "@angular/platform-browser": "^21.1.0",
    "@angular/router": "^21.1.0",
    "bootstrap": "^5.3.8",
    "rxjs": "~7.8.0",
    "tslib": "^2.3.0",
    "zone.js": "^0.16.1"
  }
}
```

### Angular Routing Structure
```
/ → Home page (news feed with filters)
/profile → User profile dashboard
/premium → Premium simulation page
/details/:id → Article details page with chatbot
/login → Login page (auth modal)
/register → Registration page (auth modal with interests selection)
/* → Wildcard redirect to home
```

### Core Components and Pages

#### **1. Home Page**
- **Purpose**: News feed with category filtering and personalization
- **Sections**:
  1. Header (sticky navigation)
  2. Hero banner (message changes by auth state)
  3. Intro section ("Latest News")
  4. Preferred interests banner (if logged in)
  5. Filter component (category, country, source, date)
  6. News feed grid (3-column on desktop, responsive)
  7. Footer
- **Functionality**:
  - Preloads articles by category
  - Caches in memory and localStorage
  - Filters by category, country, source, date type
  - Shows preferred categories first if user has interests
  - Displays up to 10 articles per preferred category, 5 per others

#### **2. Article Details Page (/details/:id)**
- **Structure**:
  - Hero metadata panel with title, category, source, date
  - Large article image
  - Article body with "Read original" button
  - Premium AI Assistant panel (conditional)
  - Comments section
- **Actions**:
  - Save/unsave article
  - Access AI assistant (premium only)
  - Post comments (if logged in)
  - View article comments

#### **3. Premium AI Assistant Panel**
- **Features**:
  - Status indicator showing Ollama connection state
  - Article brief with summary, key points, why it matters
  - Intelligence signals (people, organizations, dates, numbers)
  - Quick action buttons:
    - "Summarize this"
    - "Why does it matter?"
    - "Key facts"
    - "Explain simply"
    - "Who is involved?"
  - Conversation thread showing:
    - User messages (right-aligned, dark)
    - Assistant messages (left-aligned, white)
    - Mode indicator ("Article-grounded" or "General assistant")
    - Evidence chips showing sources
  - Input field with placeholder for questions
  - Keeps last 6 conversation turns in context

#### **4. Authentication Pages (/login and /register)**
- **Layout**: Split-screen with dark left panel and form right panel
- **Login Features**:
  - Email/password fields
  - Password visibility toggle
  - "Remember me" option
  - Link to signup
  - Error messages for invalid credentials
- **Signup Features** (2-step):
  - Step 1: Full name, email, password, confirm password
    - Real-time email availability check
    - Password strength indicator
  - Step 2: Interest selection
    - Select up to 3 favorite categories
    - Display selected count
  - Benefits shown:
    - Personalized news
    - Premium ready
    - Unified experience

#### **5. Profile Page (/profile)**
- **Hero Section**:
  - Dark gradient background
  - Marketing copy on left
  - Personal summary card on right (avatar, name, email, stats)
- **Main Content**:
  - Profile information form:
    - First name, last name, email
    - Security section: current password, new password, confirm password
  - Status badge (Loading, Saving, Ready)
  - Success/error messages
- **Side Cards**:
  - Membership card (Standard or Premium)
  - CTA to premium page
- **Saved Articles Section**:
  - Grid of saved article cards
  - Reuses NewsCard component
  - Count display
  - Empty state

#### **6. Premium Simulation Page (/premium)**
- **Purpose**: Fake checkout flow to unlock premium features
- **Layout**:
  - Hero section with simulation explanation
  - Membership status card (Guest, Standard, or Premium)
  - Plan selection (Monthly/Annual)
  - Checkout form with:
    - Cardholder name
    - Card number
    - Expiry
    - CVC
    - Terms checkbox
  - Summary card
  - Action buttons
- **Behavior**:
  - Marks user as premium locally
  - Generates fake receipt reference
  - Stores premium data in localStorage

#### **7. Shared Components**

**NewsCard Component**
- Displays article in card format
- Shows: image, category pill, title, description, metadata
- Metadata: source name, read time, publish date
- Clickable to navigate to `/details/:id`
- Passes article state in navigation for fast loading

**Hero Banner Component**
- Dark gradient background with radial gradient accents
- Message changes by user state:
  - Guest: Promote signup and future premium AI
  - Logged-in free: Encourage premium upgrade
  - Premium: Premium newsroom is ready
- Buttons change by user state
- Orange gradient CTA buttons

**Header Component**
- Sticky at top with translucent blur background
- Left: NewsHub logo with newspaper icon
- Right: 
  - Theme toggle (Light/Dark)
  - Auth state buttons (Login, Register, Premium)
  - OR Profile pill with dropdown (if logged in)
- Profile dropdown:
  - User name and email
  - Membership badge
  - Links to profile and premium
  - Logout button

**Footer Component**
- Simple design with top border
- Left: NewsHub brand
- Right: Copyright text

### Design System

#### **Color Scheme**
- **Light Mode**:
  - Background: #f7f7f8 (very light gray)
  - Cards: White
  - Text: #0f172a (deep slate)
  - Muted text: #64748b (slate gray)
  - Borders: #e5e7eb (light gray)
  - Accent: Orange gradients and sky blue

- **Dark Mode**:
  - Background: Deep blue/charcoal
  - Cards: Dark navy
  - Text: Light gray
  - Borders: Darker shades

#### **Typography**
- Font family: Inter, Arial, Helvetica, sans-serif
- Large bold headlines for impact
- Section titles: Very large and editorial
- Pill labels: Uppercase with strong letter spacing

#### **Border Radius**
- Large cards: ~18px
- Medium elements: ~14px
- Smooth transitions and curves throughout

#### **Spacing**
- Generous padding on cards
- Soft shadows (not dramatic)
- Maximum content width: 1240px

#### **Responsive Breakpoints**
- Desktop: Full layout
- Tablet (around 1100px): 2-column grids
- Mobile (around 700px): 1-column stacked layout
- Key breakpoints: 1180px, 1100px, 1024px, 900px, 760px, 700px

### State Management & Services

**Auth Service**
- Manages user session (stored in localStorage)
- Handles login/logout
- Provides premium membership data
- Token management
- Return URL handling for protected routes

**News Service**
- Fetches articles from backend API
- Manages article caching by category
- Handles filtering (category, country, source, date)
- Caches in memory and localStorage
- Deduplicates and sorts articles
- Fall back to cache if API fails

**Favorites Service**
- Save/unsave articles
- Get favorites for user
- Check if article is saved
- Manages favorite state in localStorage

**Comments Service**
- Post comments on articles
- Fetch comments for article
- Delete user's comments

**Premium Service**
- Handle premium activation (simulated)
- Check premium status
- Store premium data (plan, date, card last 4 digits)

**Chatbot Service**
- Check Ollama status
- Generate article brief
- Send chat messages
- Receive grounded and general responses
- Maintain conversation history

### Key Functional Rules

1. **Personalized Feed**
   - If user has interests: show preferred categories first
   - Preferred categories: up to 10 articles each
   - Other categories: 5 articles each

2. **Favorites System**
   - Article must have valid source URL
   - Saved state persists in database
   - Appears in profile page

3. **Comments**
   - Guests see login prompt
   - Empty comments blocked
   - Comments refresh after post

4. **Premium AI Access**
   - Premium users: See full assistant panel
   - Free users: See lock card with upsell
   - Guests: See login prompt

5. **Return URL Handling**
   - Used when login required from:
     - Save article
     - Post comment
     - Premium assistant
     - Profile access
   - After success, redirects to original page

---

## Data Flow

### Article Fetching Flow
1. Frontend requests articles for category
2. Backend fetches from NewsData API
3. Articles are cached in memory
4. Cache persisted to localStorage
5. Frontend reuses cache for fast filter switching
6. If API fails, fall back to localStorage cache

### Premium AI Flow
1. User views article as premium member
2. Frontend checks `/chatbot/status` endpoint
3. If Ollama ready, show assistant panel
4. Frontend calls `/chatbot/brief` to generate summary
5. User sends message to `/chatbot/ask`
6. Backend creates system prompt with article context
7. Message sent to Ollama via HTTP
8. Response returned and displayed with evidence

### User Registration Flow
1. Frontend collects name, email, password
2. Checks email availability with `/check-email/:email`
3. Proceeds to interest selection (Step 2)
4. User selects up to 3 interests
5. Frontend sends `/complete-signup` with all data
6. Backend validates and creates user record
7. User logged in automatically
8. Redirected to home or return URL

---

## Environment Variables

### Backend
```
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DATABASE=newshub1
DATABASE_URL=mysql+pymysql://root:@localhost:3306/newshub1?charset=utf8mb4
OLLAMA_BASE_URL=http://localhost:11434
CHATBOT_MODEL=qwen3:14b
OLLAMA_EMBED_MODEL=nomic-embed-text
```

### Frontend
- Proxy configuration in `proxy.conf.json` for development
- API base: `http://127.0.0.1:8000`

---

## Setup Instructions

### Backend Setup
```bash
cd backend

# Create MySQL database
mysql -u root < init_db.sql

# Install Python dependencies
pip install -r requirements.txt

# Start Ollama (separate terminal)
ollama serve
ollama pull qwen3:14b
ollama pull nomic-embed-text

# Run API
uvicorn main:app --reload
# API runs on http://127.0.0.1:8000/
```

### Frontend Setup
```bash
cd frontend

# Install Node dependencies
npm install

# Start Angular development server
npm start
# App runs on http://localhost:4200/
```

---

## Key Technologies & Libraries

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Backend API | FastAPI | High-performance Python web framework |
| Database | MySQL | Relational data storage |
| ORM | SQLAlchemy | Database abstraction layer |
| Auth | python-jose, bcrypt | Security and password management |
| AI/Chat | Ollama, qwen3:14b | Local AI generation model |
| Embeddings | nomic-embed-text | Article semantic search |
| Frontend | Angular 21 | SPA framework |
| Styling | Bootstrap 5, Custom CSS | UI design |
| State | RxJS | Reactive programming |
| Build | TypeScript, Webpack | Frontend compilation |
| Real-time | WebSockets | Live event messaging |

---

## Important Notes

- **Database**: Use MySQL 8.0+ for best compatibility
- **Ollama**: Must be running for premium AI features to work
- **qwen3:14b**: Preferred model; fallback variants auto-detected
- **Article URLs**: Must be valid for saving to favorites
- **Caching**: Articles cached locally to enable fast filtering
- **Password Hashing**: All passwords stored as bcrypt hashes (never plain text)
- **Premium**: Simulated locally; no real payment processing
- **Responsive Design**: App works on desktop, tablet, and mobile

This documentation provides a complete blueprint for recreating or improving the NewsHub project with another AI system.
