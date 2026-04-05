# Discord sample app (Python + Vercel Functions)

awwbot is a sample Discord bot that returns cute content from `r/aww`, built with **Python** and deployed on **Vercel Functions**.

## Resources used

- [Discord Interactions API](https://discord.com/developers/docs/interactions/receiving-and-responding)
- [Vercel Functions (Python)](https://vercel.com/docs/functions/functions-api-reference/vercel-sdk-python)
- [Reddit API](https://www.reddit.com/dev/api/)

---

## Project structure

```
├── .github/workflows/ci.yaml   -> GitHub Actions
├── api
│   └── interactions.py         -> Vercel Python Function entrypoint
├── src-python
│   ├── commands.py             -> Command definitions
│   ├── reddit.py               -> Reddit API access
│   ├── register.py             -> Prints curl command for Discord command registration
│   └── server.py               -> Discord interaction core logic
├── pyproject.toml              -> Python project config
├── package.json
└── README.md
```

## Configuring project

Before starting, create a [Discord app](https://discord.com/developers/applications) and prepare:

- `DISCORD_TOKEN`
- `DISCORD_PUBLIC_KEY`
- `DISCORD_APPLICATION_ID`

You can store these in `.dev.vars` (copy from `example.dev.vars`).

## Register commands

Command registration is now manual by design:

```bash
python src-python/register.py
```

The script prints a `curl` command. Run that command in an environment where `DISCORD_TOKEN` is set.

## Deploying app

- Vercel uses `api/interactions.py` as the function entrypoint.
- You can add `vercel.json` yourself if you need custom routing.
- Set these project environment variables in Vercel:
  - `DISCORD_PUBLIC_KEY`
  - `DISCORD_APPLICATION_ID`
  - `DISCORD_TOKEN` (typically needed when registering commands or calling Discord APIs directly)
