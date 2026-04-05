# Discord sample app (Python + Vercel Functions)

awwbot 是一個會把 `r/aww` 可愛內容回傳到 Discord 的範例機器人，使用 **Python** 與 **Vercel Functions** 部署。

## Resources used

- [Discord Interactions API](https://discord.com/developers/docs/interactions/receiving-and-responding)
- [Vercel Functions (Python)](https://vercel.com/docs/functions/functions-api-reference/vercel-sdk-python)
- [Reddit API](https://www.reddit.com/dev/api/)

---

## Project structure

```
├── .github/workflows/ci.yaml   -> GitHub Actions
├── api
│   └── interactions.py         -> Vercel Python Function 入口
├── src-python
│   ├── commands.py             -> Command definitions
│   ├── reddit.py               -> Reddit API 存取
│   ├── register.py             -> 產生 Discord 註冊 curl 指令
│   └── server.py               -> Discord interaction 核心邏輯
├── pyproject.toml              -> Python project config
├── package.json
└── README.md
```

## Configuring project

在開始前，你需要先建立一個 [Discord app](https://discord.com/developers/applications)，並準備：

- `DISCORD_TOKEN`
- `DISCORD_PUBLIC_KEY`
- `DISCORD_APPLICATION_ID`

可將這些變數放在 `.dev.vars`（由 `example.dev.vars` 複製）。

## Register commands

註冊指令改為由腳本輸出 `curl`，再由你自行執行：

```bash
python src-python/register.py
```

腳本會輸出一條 `curl` 指令，請在已設定 `DISCORD_TOKEN` 的環境下執行。

## Deploying app

- Vercel 會以 `api/interactions.py` 作為函式入口。
- 你可以自行補上 `vercel.json`（如需路由設定）。
- 請在 Vercel 專案環境變數中設定：
  - `DISCORD_PUBLIC_KEY`
  - `DISCORD_APPLICATION_ID`
  - `DISCORD_TOKEN`（通常執行註冊或其他 API 動作時才需要）
