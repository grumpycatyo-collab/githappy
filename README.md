# GitHappy

Personal Changelog API to track your life like a GitHub project


## What is GitHappy?

GitHappy lets you track your life like a software project, with personal changelog entries that include:
- 🔍 Entry types (HIGHLIGHT, BUG, REFLECTION)
- 😊 Mood tracking
- 🏷️ Custom tags
- ✨ Gitmojis automatically assigned based on content
- 📊 Sentiment analysis

## Features

- **Personal Changelog**: Track life events, reflections, and issues
- **Sentiment Analysis**: Automatically analyze the sentiment of your entries
- **Gitmoji Support**: Visualize entry types with appropriate emojis
- **Week-based Organization**: Group entries by week for better life retrospectives
- **Tag System**: Categorize entries with custom tags
- **REST API**: Access your data programmatically
- **Authentication**: Secure your personal data with JWT

## Examples

### Creating a Changelog Entry

When you want to record your day:

```bash
curl -X 'POST' \
  'http://0.0.0.0:8000/api/changelog/' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer YOUR BEARER' \
  -H 'Content-Type: application/json' \
  -d '{
  "content": "I had a bad day today, however I learnt a lot, so I am gonna continue and be better tomorrow",
  "entry_type": "HIGHLIGHT",
  "mood": "HAPPY",
  "tags": [
    "6827b84a5d986a02e321c33c"
  ]
}'
```

### Response
```json
{
  "_id": "6827b8ca5d986a02e321c33d",
  "user_id": "6827b7d15d986a02e321c33a",
  "content": "I had a bad day today, however I learnt a lot, so I am gonna continue and be better tomorrow",
  "entry_type": "HIGHLIGHT",
  "mood": "HAPPY",
  "week_number": 20,
  "gitmojis": [
    "✨",
    "🚀",
    "🧠"
  ],
  "sentiment_score": -1,
  "tags": [
    "6827b84a5d986a02e321c33c"
  ],
  "created_at": "2025-05-17T01:14:34.482986",
  "updated_at": null
}
```

GitHappy automatically:

* Adds relevant gitmojis based on content analysis
* Calculates sentiment score (positive in this case despite challenges)
* Organizes by week for easy retrospectives


## Getting Formatted Entry

See how your entry looks with gitmojis:

```bash
curl -X GET "http://localhost:8000/api/changelog/6c84fb90-12c4-11e1-840d-7b25c5ee775a/formatted" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Requirements

* Python 3.11
* MongoDB
* Docker and Docker Compose (optional)

## API Documentation
Once running, visit http://localhost:8000/docs for the Swagger UI documentation.