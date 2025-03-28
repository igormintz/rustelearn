# Rust Learning Bot 🤖

A Telegram bot that helps users learn Rust programming through personalized lessons, interactive exercises, and progress tracking.

## Features 🚀

- **Personalized Learning Path**
  - AI-powered lesson generation based on user progress
  - Adaptive difficulty levels (Beginner, Intermediate, Advanced)
  - Spaced repetition learning system

- **Interactive Learning Experience**
  - Daily lessons and exercises
  - Code examples with explanations
  - Practice exercises with immediate feedback
  - Integration with Rust Playground

- **Progress Tracking**
  - Detailed progress statistics
  - Topic mastery tracking
  - Learning streak counting
  - Achievement system

- **Customizable Settings**
  - Message frequency preferences (1-3 times per day)
  - Learning progress reset option
  - Personalized notification schedule (8:00-21:00)

## Commands 📝

- `/start` - Initialize your profile and start learning
- `/progress` - View your learning progress and statistics
- `/mini` - Get a quick, personalized mini-lesson

## Database Structure 💾

The bot uses SQLite for persistent storage with the following main tables:
- `users` - User profiles and preferences
- `topics` - Learning content and materials
- `user_progress` - Individual learning progress
- `learning_sessions` - Session tracking and metrics

## Setup 🛠️

1. Clone the repository:
```bash
git clone https://github.com/yourusername/rust-learning-bot.git
cd rust-learning-bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
export TELEGRAM_BOT_TOKEN='your_bot_token'
export OPENAI_API_KEY='your_openai_api_key'
export DATABASE_URL='sqlite:///rust_learning_bot.db'  # Optional, defaults to this value
```

4. Run the bot:
```bash
python main.py
```

## Project Structure 📁

```
rust-learning-bot/
├── main.py                 # Main bot entry point
├── requirements.txt        # Python dependencies
├── src/
│   ├── config/            # Configuration settings
│   ├── database/          # Database models and connection
│   ├── handlers/          # Command and callback handlers
│   └── utils/             # Utility functions and tools
└── README.md              # This file
```

## Contributing 🤝

Contributions are welcome! Please feel free to submit a Pull Request.

## License 📄

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments 🙏

- OpenAI for providing the GPT API
- Telegram Bot API team
- Rust community for excellent documentation and resources
