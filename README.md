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


### Getting Formatted Entry

See how your entry looks with gitmojis:

```bash
curl -X GET "http://localhost:8000/api/changelog/6c84fb90-12c4-11e1-840d-7b25c5ee775a/formatted" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## CLI (WIP) via Typer
Yes, there is a CLI! You can use it to manage your changelog entries directly from the command line. 

```bash
python3 cli.py --help

Usage: cli.py [OPTIONS] COMMAND [ARGS]...                                                                                       
                                                                                                                                 
╭─ Options ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --install-completion          Install completion for the current shell.                                                       │
│ --show-completion             Show completion for the current shell, to copy it or customize the installation.                │
│ --help                        Show this message and exit.                                                                     │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ auth   Authenticate a user with a bearer token.                                                                               │
│ log    Get the changelog entries for the current user. Works like "git log".                                                  │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

Use the `auth` command to paste your bearer token and authenticate with the API.
```bash
python3 cli.py auth --bearer YOUR_TOKEN
✅ Authentication successful
User: grumpycatyo_collab | Role: WRITER
```

Then you can start playing with the `log` command to get your changelog entries:
```
python3 cli.py log --help
                                                                                                                                 
Usage: cli.py log [OPTIONS]                                                                                                     
                                                                                                                                 
 Get the changelog entries for the current user. Works like "git log".                                                           
 Parameters ---------- json : bool, optional     Whether to output in JSON format (default is False) tags : list[str], optional  
 Filter by tag names limit : int, optional     Limit number of entries to show (default is 10) Returns ------- None              
                                                                                                                                 
╭─ Options ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --json       --no-json             [default: no-json]                                                                         │
│ --tag    -t               TEXT     Filter by tag names [default: None]                                                        │
│ --limit  -l               INTEGER  Limit number of entries to show [default: 10]                                              │
│ --help                             Show this message and exit.                                                                │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

So if we do:
```
python3 cli.py log --tag life --limit 2 

========================================================================================
CHANGELOG FOR string (2 entries)
========================================================================================
DATE                | TAGS | MESSAGE
────────────────────────────────────────────────────────────────────────────────────────
2025-05-17 18:34    | uni | 📝 ❤️ I've met a cute girl today, I hope I don't feel in love
────────────────────────────────────────────────────────────────────────────────────────
2025-05-17 18:33    | uni | ✨ Sometimes life doesn't feel that good
────────────────────────────────────────────────────────────────────────────────────────
```

Als you can create new entries by using the `write` command:

```
python3 cli.py write
━━━ CREATE NEW ENTRY ━━━

QUESTION: What's on your mind? I love my mom
You wrote: I love my mom

SELECT ENTRY TYPE
  1. HIGHLIGHT
  2. BUG
  3. REFLECTION
  4. INSIGHT
  5. CHALLENGE
  6. PROGRESS
  7. QUESTION
QUESTION: Select entry type (number) 1
Selected: HIGHLIGHT

SELECT MOOD
  1. HAPPY
  2. NEUTRAL
  3. SAD
  4. EXCITED
  5. STRESSED
  6. TIRED
QUESTION: Select mood (number) 1
Selected: HAPPY

ADD TAGS
QUESTION: Enter tags (comma-separated) mom
Tags entered: mom

✓ Created new tag: mom

✅ ENTRY CREATED SUCCESSFULLY!
╭────────────────────────────────────────────────────── New Entry Summary ──────────────────────────────────────────────────────╮
│                                                                                                                               │
│  ❤️ 🌱 I love my mom                                                                                                           │
│                                                                                                                               │
│  Type: HIGHLIGHT | Mood: HAPPY                                                                                                │
│  Tags: mom                                                                                                                    │
│  Sentiment: Very Positive (0.64)                                                                                              │
│  Created: 2025-05-18 00:54:52                                                                                                 │
│                                                                                                                               │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

```
## Requirements

* Python 3.11
* MongoDB
* Docker and Docker Compose (optional)

## API Documentation
Once running, visit http://localhost:8000/docs for the Swagger UI documentation.