# LPI Platform — React Frontend Client

**Author:** Jahanvi Gupta

This directory contains the React + Vite frontend client for the LPI Platform, integrated with backend services.

## Setup & Run Instructions

### Prerequisites

Make sure you have [Node.js](https://nodejs.org/) installed.

### 1. Install Dependencies

Navigate to this directory and install the package dependencies:

```bash
cd frontend-js
npm install
```

### 2. Run the Development Server

Start the local Vite development server:

```bash
npm run dev
```

Open the provided local address (typically `http://localhost:5173`) in your browser to view the application.

### 3. Build for Production

To generate a production-ready optimized build:

```bash
npm run build
```

---

## Backend Connection & Changes

The frontend connects to the FastAPI backend API running at `http://localhost:8000`. Ensure your backend server is running concurrently by running the following command in the root folder of the project:

```bash
make run
```

### Configuration (`.env` file)

Inside the `frontend-js` folder, create a `.env` file containing the following keys:

```env
VITE_SUPABASE_URL=http://127.0.0.1:54321
VITE_SUPABASE_ANON_KEY=your-key-here
VITE_GITHUB_CLIENT_ID=your-github-client-id
```

### Configuration (Root `.env` file)

In the root directory of the project, make sure you have a `.env` file set up with the following configuration:

```env
SUPABASE_URL=http://127.0.0.1:54321
SUPABASE_KEY=your-service-role-key-here
SUPABASE_JWT_SECRET=super-secret-jwt-token-with-at-least-32-characters-long
LLM_PROVIDER=groq
LLM_MODEL=llama-3.3-70b-versatile
GROQ_API_KEY=your-groq-api-key-here
DAILY_COST_CAP_USD=10.0
ADMIN_USER_IDS=your-admin-user-id
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
```

> [!NOTE]
> To configure multiple administrators, you can add their user UUIDs in `ADMIN_USER_IDS` separated by a comma (e.g., `ADMIN_USER_IDS=uuid1,uuid2,uuid3`).

### Key Features Added

* **Toast Notification System**: Integrated a premium, glassmorphic Toast notification system (`Toast.jsx` and `Toast.css`) to replace default browser alerts.
* **Account Disconnect Flow**: Added a "Disconnect Account" button in the GitHub integration section to clear user token records and remove tracking local storage keys.
* **Repository Disconnect Webhooks**: Enhanced tracking controls with a "Disconnect" action per repository that triggers the backend to unsubscribe GitHub webhooks.
* **User-Namespaced Storage**: Tracking repository state caches in Local Storage are namespaced per user (`tracked_repos_${userId}`) to avoid profile signal leaks.
* **Admin View Integration**: Updated the administrator timeline view in `SignalsView.jsx` to list all signals from all users.

## Folder Structure

```
frontend-js/
├── README.md                  # Setup and running instructions
├── index.html                 # HTML entry point for the React app
├── package.json               # Project dependencies and script runner (Vite)
├── vite.config.js             # Vite build tool configuration
├── eslint.config.js           # JavaScript formatting/linting rules
│
├── public/                    # Static assets (favicons, SVG assets)
│
└── src/                       # Main React source code
    ├── main.jsx               # React root injection point
    ├── App.jsx                # Main App layout, tab navigation, auth session listener
    ├── App.css                # Base application layout styles
    ├── api.js                 # Fetch connection layer to FastAPI endpoints
    ├── index.css              # Global theme styling tokens (dark mode, glassmorphism)
    ├── supabaseClient.js      # Supabase Authentication client initialization
    │
    ├── src/assets/            # Images and design assets
    │
    └── src/components/        # Modular React components and their CSS files
        ├── LoginPage.jsx / .css          # Portal landing / Login / Sign-up layout
        ├── UserProfile.jsx / .css        # Settings page, profile avatar, display name sync
        ├── GoalsList.jsx / .css          # Dashboard grid wrapper for GoalCards
        ├── GoalCard.jsx / .css           # Individual SMILE phase steppers and transitions
        ├── GoalCreateModal.jsx / .css    # Overlay popup wrapper for new goal creation
        ├── GoalCreateForm.jsx / .css     # Goal creation fields
        ├── RecommendationsView.jsx / .css # S.M.I.L.E. engine cards, AI reasoning logs, and feedback loops
        ├── GithubTracker.jsx / .css      # Dropdown repo selectors, toggles, and account integrations
        ├── SignalsView.jsx / .css        # Chronological timeline polling activity stream from GitHub
        └── Toast.jsx / .css              # Glassmorphic, non-blocking notification banners
```
