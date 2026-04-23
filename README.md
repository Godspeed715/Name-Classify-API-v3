# Name-Classify-API-v3

## Overview
Name-Classify-API-v3 is a demographic intelligence API that enables intelligent profile querying and filtering. It allows clients to search, filter, and analyze demographic data using advanced filtering, sorting, pagination, and natural language queries.

## Features

### 1. Advanced Filtering
Filter profiles by multiple criteria:
- **gender**: Filter by 'male' or 'female'
- **age_group**: Filter by 'child', 'teen', 'adult', 'senior', or 'young'
- **country_id**: Filter by ISO country code (e.g., 'NG', 'US')
- **min_age/max_age**: Filter by age range
- **min_gender_probability/min_country_probability**: Filter by confidence scores

### 2. Sorting & Pagination
- **sort_by**: Sort results by 'age', 'created_at', or 'gender_probability'
- **order**: Specify 'asc' (ascending) or 'desc' (descending) order
- **page**: Navigate through paginated results (default: 1)
- **limit**: Set results per page (default: 10, max: 50)

### 3. Natural Language Queries
Search using plain English queries that are automatically parsed into filters:
- Example: "young males from nigeria" → gender=male, min_age=16, max_age=24, country_id=NG
- Example: "females above 30" → gender=female, min_age=30

### 4. Error Handling
All errors follow a consistent format with appropriate HTTP status codes:
- 400 Bad Request: Missing or empty parameters
- 422 Unprocessable Entity: Invalid parameter types
- 404 Not Found: Profile not found
- 500 Server Error: Database or server failures

## API Endpoints

### GET /api/profiles
Retrieve profiles with optional filters and sorting.

**Example:**
```
GET /api/profiles?gender=male&country_id=NG&min_age=25&limit=20
```

### GET /api/profiles/search
Search using natural language queries.

**Example:**
```
GET /api/profiles/search?q=young+males+from+nigeria
```

## Response Format
```json
{
  "status": "success",
  "page": 1,
  "limit": 10,
  "total": 2026,
  "data": [...]
}
```

## Error Response Format
```json
{
  "status": "error",
  "message": "Error description"
}
```

## Technical Details
- **Database**: PostgreSQL with 2026+ demographic profiles
- **Framework**: Flask with CORS support
- **Language Processing**: Spacy for natural language parsing
- **CORS**: Enabled for cross-origin requests