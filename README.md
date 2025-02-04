# Waveger Backend API - Billboard Charts Integration

## Overview

This backend service provides access to Billboard chart data using the **Billboard Charts API**. It supports fetching top charts and retrieving specific chart details while minimizing API calls by caching data in a PostgreSQL database.

## Endpoints

### 1. **Get Top Charts**

**Endpoint:**  
`GET /api/top-charts`

**Description:**  
Returns a list of top Billboard charts.

**Example Response:**

```json
{
  "source": "api",
  "data": {
    "charts": [
      {
        "id": "hot-100",
        "title": "Billboard Hot 100™"
      },
      {
        "id": "billboard-200",
        "title": "Billboard 200™"
      }
    ]
  }
}
```

**Note:** The `source` field indicates whether data is retrieved from the **database** or directly from the **API**.

---

### 2. **Get Specific Chart Details**

**Endpoint:**  
`GET /api/chart?id={chart_id}&week={YYYY-MM-DD}`

**Description:**  
Fetches details for a specific Billboard chart.

- If **no `id` is specified**, it defaults to `"hot-100"`.
- If **no `week` is specified**, it defaults to today's date.
- If the requested data exists in the **database**, it is retrieved from there instead of calling the API.

**Example Request:**  
`GET /api/chart?id=hot-100&week=2025-02-08`

**Example Response:**

```json
{
  "source": "database",
  "data": {
    "title": "Billboard Hot 100™",
    "week": "Week of February 8, 2025",
    "songs": [
      {
        "position": 1,
        "name": "4X4",
        "artist": "Travis Scott",
        "image": "https://charts-static.billboard.com/img/2025/02/travis-scott-a4t-4x4-eal-180x180.jpg",
        "url": "https://www.youtube.com/results?search_query=4X4+Travis+Scott",
        "last_week_position": 0,
        "peak_position": 1,
        "weeks_on_chart": 1
      }
    ]
  }
}
```

**Note:**

- `"source": "database"` indicates that the response was **retrieved from the database**.
- `"source": "api"` would mean that data was fetched **directly from the API** and stored in the database for future requests.

---

## Billboard Chart IDs

Below are the supported chart IDs that can be used with `/api/chart`:

| Chart ID                        | Chart Title                    |
| ------------------------------- | ------------------------------ |
| `hot-100`                       | Billboard Hot 100™            |
| `billboard-200`                 | Billboard 200™                |
| `artist-100`                    | Billboard Artist 100           |
| `emerging-artists`              | Emerging Artists               |
| `streaming-songs`               | Streaming Songs                |
| `radio-songs`                   | Radio Songs                    |
| `digital-song-sales`            | Digital Song Sales             |
| `summer-songs`                  | Songs of the Summer            |
| `top-album-sales`               | Top Album Sales                |
| `tiktok-billboard-top-50`       | TikTok Billboard Top 50        |
| `top-streaming-albums`          | Top Streaming Albums           |
| `independent-albums`            | Independent Albums             |
| `vinyl-albums`                  | Vinyl Albums                   |
| `indie-store-album-sales`       | Indie Store Album Sales        |
| `billboard-u-s-afrobeats-songs` | Billboard U.S. Afrobeats Songs |

---

## Database Caching

To reduce API usage, this service stores fetched chart data in a **PostgreSQL database**. If a chart's **title and week** exist in the database, it retrieves the data from there instead of making an API call.

### **Database Schema (Simplified)**

| Column Name | Type   | Description                            |
| ----------- | ------ | -------------------------------------- |
| `id`        | SERIAL | Auto-incrementing unique ID            |
| `title`     | TEXT   | Chart title (e.g., Billboard Hot 100)  |
| `week`      | TEXT   | Chart week (e.g., Week of Feb 8, 2025) |
| `data`      | JSONB  | Chart data stored as JSON              |

---

## Environment Variables

Ensure the following environment variables are set:

- `RAPIDAPI_KEY` → Your RapidAPI key for Billboard Charts API.
- `DATABASE_URL` → PostgreSQL connection string.

---

## Deployment Notes

- This service is deployed on **Render**.
- Uses **Flask** as the backend framework.
- **Flask-CORS** is enabled for handling cross-origin requests.

---

### 🚀 API is now live!

Make API calls at:  
🔗 `https://wavegerpython.onrender.com/api/chart`  
🔗 `https://wavegerpython.onrender.com/api/top-charts`
