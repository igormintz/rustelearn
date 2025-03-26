# Rust Learning Bot 🦀

A Telegram bot designed to help users learn Rust programming language through interactive lessons, practice exercises, and real-time feedback.

## Features

- 📚 Interactive Rust programming lessons
- 🎯 Practice exercises with difficulty progression
- 💻 Direct integration with Rust Playground
- 📊 Progress tracking and analytics
- 🤖 AI-powered explanations and assistance
- ✨ Personalized learning experience

## Prerequisites

- Python 3.8 or higher
- Poetry (Python package manager)
- Telegram Bot Token
- OpenAI API Key

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/rust-learning-bot.git
cd rust-learning-bot
```

2. Install dependencies using Poetry:
```bash
poetry install
```

3. Create a `.env` file in the project root:
```bash
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openai_api_key
```

## Project Structure

```
rust-learning-bot/
├── src/
│   ├── config/
│   │   └── settings.py
│   ├── database/
│   │   ├── connection.py
│   │   └── models.py
│   ├── handlers/
│   │   ├── callback_handlers.py
│   │   └── command_handlers.py
│   └── utils/
│       └── openai_tools.py
├── .env
├── .gitignore
├── main.py
├── pyproject.toml
└── README.md
```

## Usage

1. Start the bot:
```bash
poetry run python main.py
```

2. In Telegram, start a conversation with the bot:
   - Use `/start` to begin
   - Use `/mini` for quick lessons
   - Use `/progress` to check your learning progress

## Bot Commands

- `/start` - Initialize the bot and see available options
- `/progress` - Check your learning progress
- `/mini` - Get a mini lesson
- Interactive buttons for:
  - Lesson navigation
  - Practice exercises
  - Rust Playground integration
  - Progress tracking

## Development

1. Format code:
```bash
poetry run black .
```

2. Run linter:
```bash
poetry run flake8
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Rust Programming Language Team
- python-telegram-bot developers
- OpenAI for content generation
- YouTube for educational content

## Support

If you encounter any issues or have questions, please open an issue on GitHub or contact the maintainers.
