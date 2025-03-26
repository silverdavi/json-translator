# Examples

This directory contains example JSON files for demonstrating and testing the JSON Translator.

## Directory Structure

```
examples/
├── en/                 # Source English JSON files
│   ├── homepage.json   # Simple homepage translations
│   └── dashboard.json  # More complex nested translations
└── output/             # Generated output translations
    ├── es/             # Spanish translations
    ├── fr/             # French translations
    └── ...             # Other language directories
```

## File Descriptions

### Homepage (Simple)

`homepage.json` is a simple flat JSON file with basic UI strings:

```json
{
  "welcome": "Welcome to our application",
  "login": "Log in",
  "signup": "Sign up",
  "logout": "Log out",
  "settings": "Settings",
  "profile": "Profile",
  "help": "Help",
  "about": "About"
}
```

### Dashboard (Nested)

`dashboard.json` demonstrates more complex nested JSON structure:

```json
{
  "app": {
    "name": "Sample Application",
    "version": "1.0.0"
  },
  "navigation": {
    "home": "Home",
    "dashboard": "Dashboard",
    "settings": "Settings",
    "profile": {
      "view": "View Profile",
      "edit": "Edit Profile",
      "picture": "Change Picture"
    }
  },
  "messages": {
    "success": {
      "login": "Successfully logged in",
      "signup": "Account created successfully",
      "update": "Your information has been updated"
    },
    "errors": {
      "login": "Invalid username or password",
      "server": "Server connection error",
      "validation": "Please check your input and try again"
    }
  },
  "buttons": {
    "save": "Save",
    "cancel": "Cancel",
    "delete": "Delete",
    "confirm": "Confirm"
  }
}
```

## Running the Examples

To translate these example files, run:

```bash
python json_translator_main.py --source examples/en --languages Spanish,French,German --output examples/output
```

The translated files will be generated in the `output` directory, organized by language code.

## Notes for Translators

- Preserve any placeholders like `{username}` or `{count}` in the translated text
- Maintain the JSON structure - only translate the string values, not the keys
- For arrays, translate each string element while preserving the array structure 