# Translation Examples

This directory contains sample JSON files that demonstrate different complexity levels for the JSON translation pipeline. These examples are intended to help you understand how to structure your own translation files.

## Directory Structure

- **simple/**: Basic flat JSON structure with simple key-value pairs
- **nested/**: Nested JSON structure with multiple levels of hierarchy
- **complex/**: Complex JSON structure with arrays, mixed types, and placeholders

## Simple Example

The simple example demonstrates a flat JSON structure with basic key-value pairs. This is suitable for simple applications with few translation strings.

```json
{
  "welcome": "Welcome to our application",
  "login": "Log in",
  "signup": "Sign up"
}
```

## Nested Example

The nested example demonstrates a hierarchical JSON structure with multiple levels of nesting. This is suitable for organizing translations by feature or section.

```json
{
  "navigation": {
    "home": "Home",
    "profile": {
      "view": "View Profile",
      "edit": "Edit Profile"
    }
  },
  "messages": {
    "success": {
      "login": "Successfully logged in"
    }
  }
}
```

## Complex Example

The complex example demonstrates advanced JSON features including:

1. **Arrays**: Lists of items that need translation
2. **Mixed types**: Combining strings, numbers, booleans, and objects
3. **Placeholders**: Variables embedded in strings like `{username}` that should be preserved during translation

```json
{
  "dashboard": {
    "welcome": "Welcome back, {username}!",
    "statistics": {
      "items": [
        {
          "label": "Projects",
          "description": "You have {count} active projects"
        }
      ]
    }
  }
}
```

## Using These Examples

You can use these examples to test the translation pipeline:

```bash
python json_translator_main.py --input-dir "examples/simple/" --output-dir "output/" --languages "Spanish,French,German"
```

When creating your own translation files, choose a structure that best matches your application's complexity and organization needs.

## Notes for Translators

- Preserve any placeholders like `{username}` or `{count}` in the translated text
- Maintain the JSON structure - only translate the string values, not the keys
- For arrays, translate each string element while preserving the array structure 