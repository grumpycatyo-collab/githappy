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
curl -X POST "http://localhost:8000/api/changelog/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "I had a bad day today, however I learnt a lot, so I am gonna continue and be better tomorrow",
    "entry_type": "REFLECTION",
    "mood": "NEUTRAL",
    "tags": ["f47ac10b-58cc-4372-a567-0e02b2c3d479"]
  }'
```

### Response
```json
{
  "id": "6c84fb90-12c4-11e1-840d-7b25c5ee775a",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "content": "I had a bad day today, however I learnt a lot, so I am gonna continue and be better tomorrow",
  "entry_type": "REFLECTION",
  "mood": "NEUTRAL",
  "week_number": 32,
  "gitmojis": ["📝", "💡", "⚡"],
  "sentiment_score": 0.25,
  "tags": ["f47ac10b-58cc-4372-a567-0e02b2c3d479"],
  "created_at": "2023-08-10T14:30:45.123Z",
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