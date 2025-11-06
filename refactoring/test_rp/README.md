# Test RP Directory

This is a minimal RP directory for testing the refactored RP Client.

## Structure

```
test_rp/
├── config/
│   ├── config.json       # Main configuration
│   └── .env              # API keys (optional)
├── state/
│   └── session.json      # Session state
├── characters/           # Character files
└── worlds/               # World files
```

## Testing Mode

Since this is a test directory with no API keys configured, you can use **Testing Mode**:

1. Launch the application:
   ```bash
   python launch.py test_rp
   ```

2. Press **F2** to open settings

3. Toggle **Testing Mode** to ON

4. Send a test message - you'll get mock responses without needing API keys!

## Adding API Keys

If you want to test with real LLM providers:

1. Edit `config/.env` and add your API keys:
   ```
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   OPENAI_API_KEY=sk-your-key-here
   ```

2. Edit `config/config.json` and enable the provider:
   ```json
   "claude_client": {
     "enabled": true,
     ...
   }
   ```

3. Restart the application

4. Use **F2** → Provider Selector to switch providers

## Next Steps

- Create character files in `characters/`
- Add world files in `worlds/`
- Configure triggers and templates
- Explore the WIP testing system!
