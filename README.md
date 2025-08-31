# Yerak Discord Bot

Yerak Discord Bot is a feature-rich, modular, and extensible Discord bot designed for flexibility and easy customization. Built on top of the `discord.py` framework.

---

## Features

- **Modular Architecture:** Each major feature is implemented as a separate extension (Cog) for clean separation of concerns and scalability.
- **Dynamic Extension Management:** Hot-reload, load, and unload extensions at runtime with developer commands—no need to restart the bot to add or remove features.
- **Music Playback:** Includes a fully functional music module with voice support (using FFMPEG).
- **Custom Help System:** Enhanced help command for intuitive user onboarding and command discovery.
- **Developer Tools:** Safe, permission-checked developer commands for live bot management, including syncing application commands and controlled shutdowns.
- **Advanced Logging:** Centralized logging configuration for easier debugging and monitoring.

---

## Technical Highlights

### 1. Project Structure & Modularization

The codebase is organized around an "extension" model, where each feature set is an isolated module:
```
src/
  bot_yerak.py       # Main bot class and entrypoint logic
  main.py            # Launch script
  extensions/
    development/     # Developer/admin tools
    help/            # Custom help command
    miscellaneous/   # Misc utilities
    music/           # Music playback
    rave/            # Entertainment roles & effects
  settings/          # Configs and logging
```
Each extension is loaded as a "Cog" and can be managed at runtime.

### 2. Design Patterns & Best Practices

- **Command Pattern:** Each command is a method decorated within its Cog, allowing for easy mapping and grouping.
- **Builder Pattern:** Command attributes and parameters are dynamically built from configuration files, supporting scalability and DRY principles.
- **Dependency Injection:** Cogs receive the bot instance during initialization, enabling loose coupling and easier unit testing.
- **Signal Handling:** The bot gracefully handles termination signals for safe shutdowns.
- **Global Configuration Caching:** Command metadata is cached and invalidated at the appropriate lifecycle events to optimize performance and memory usage.

### 3. Extension Management

The bot provides developer-only commands to:
- Load/unload/reload extensions (hot-swap features on the fly)
- Sync application commands for up-to-date slash command support
- Controlled shutdown with confirmation prompts

### 4. Type Safety & Custom Contexts

- Custom context objects (`CustomContext`) extend the default Discord.py context to standardize command handling and error management.
- Type hints are used throughout for better readability and tooling support.

### 5. Logging

Uses Python's logging configuration (`logging.config.dictConfig`) to aggregate logs from all modules and extensions, supporting both debugging and production monitoring.

---

## Getting Started

### Prerequisites

- Python 3.10+
- Discord bot token
- FFMPEG (for music features)

### Installation

1. Clone the repository:
   ```sh
   git clone https://github.com/Davi-S/yerak-discord-bot.git
   cd yerak-discord-bot
   ```

2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

3. Configure your settings:
   - Copy and edit the settings and logging config files under `src/settings/`.

4. Run the bot:
   ```sh
   python src/main.py
   ```

---

## Extending and Customizing

Add new features by creating a new extension (Cog) in the `src/extensions/` directory. Register your extension in the bot's `initial_extensions` list and implement your commands with the provided patterns for consistency and maintainability.

---

## License

This project is licensed under the GNU General Public License v3.0. See [LICENSE](LICENSE) for details.
