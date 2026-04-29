# EncHybrid Bot 🎬

Hybrid Telegram encoding bot combining features from **Nubuki-all/Enc** and **Zylern/TGVid-Comp**.
Encodes video to **AV1 / HEVC x265 / HEVC x264** (10-bit, dual audio) via FFmpeg.

---

## Features

### Encoding
- AV1 (libsvtav1), HEVC x265, HEVC x264 — all 10-bit
- Configurable CRF, preset, bit depth (8/10) per user
- Dual audio: keep 2 audio tracks (e.g. JPN + ENG), AAC 192k
- Subtitle passthrough
- Custom ffmpeg override via FFMPEG env vars
- Encoding queue with configurable max size

### File Management
- Auto-prefix / auto-suffix on output filenames
- Regex autorename rule (pattern|replacement)
- Custom releaser tag (e.g. [GroupName])
- Codec tag appended automatically
- Safe filename sanitization

### Thumbnail
- Custom per-user thumbnail (set by replying to photo)
- Auto-extract from video if no custom thumb set
- View / delete thumbnail

### Caption
- Decorator emoji/prefix (CAP_DECO)
- Caption includes codec, audio mode, file size
- Custom rename rules applied to captions too

### Sample & Screenshots
- `/sample` — cut N-second sample clip (configurable start/duration)
- `/screenshots` — capture N evenly-spaced screenshots as media group

### Upload
- Upload as video (with streaming) or document
- Spoiler mode toggle
- Dump to separate channel/group (DUMP_CHANNEL)
- Forward channel support (FCHANNEL)

### Download
- Telegram file download with progress bar
- Speed, ETA, percentage shown in live-updating message

### Admin
- `/lock` / `/unlock` — freeze encoding
- `/clearqueue` — flush all queued jobs
- `/broadcast` — message all users
- `/stats` — CPU / RAM / disk / queue

### Misc
- Per-user settings stored in MongoDB
- `/mysettings` — view all active settings
- `/reset` — reset settings to defaults
- Auto-deploy latest on startup (ALWAYS_DEPLOY_LATEST)
- LOGS_IN_CHANNEL — auto-dump errors to log channel

---

## Setup

1. Clone repo and copy `.env.sample` → `.env`
2. Fill in APP_ID, API_HASH, BOT_TOKEN, OWNER, DATABASE_URL
3. Build & run:

```bash
docker build -t enchybrid .
docker run --env-file .env enchybrid
```

---

## Deploy on Heroku (NO CLI required)

### Step 1 — Fork this repo
Go to your copy on GitHub: `https://github.com/YOUR_USERNAME/EncHybridBot`

### Step 2 — Create Heroku app
1. Go to https://dashboard.heroku.com/new-app
2. Enter app name → **Create app**

### Step 3 — Connect GitHub
1. In your Heroku app → **Deploy** tab
2. Deployment method → **GitHub**
3. Search for your fork → **Connect**

### Step 4 — Set stack to container
1. Go to **Settings** tab → **Stack** section
2. Change stack to **container**
   *(Heroku Dashboard → Settings → scroll to "Stack" → click "Change Stack" → select `container`)*

   Alternatively, set `heroku.yml` in root (already included in this repo).

### Step 5 — Set Config Vars (env variables)
1. Heroku app → **Settings** → **Config Vars** → **Reveal Config Vars**
2. Add each variable from `.env.sample`:

| Key | Value |
|-----|-------|
| APP_ID | your telegram app id |
| API_HASH | your telegram api hash |
| BOT_TOKEN | your bot token from @BotFather |
| OWNER | your telegram user id |
| DATABASE_URL | mongodb+srv://... |
| DEFAULT_CODEC | hevc265 |
| DUAL_AUDIO | True |
| ... | (see .env.sample for full list) |

### Step 6 — Deploy
1. **Deploy** tab → **Manual deploy** → select `main` branch → **Deploy Branch**
2. Watch build logs. When done, go to **Resources** tab.

### Step 7 — Enable worker dyno
1. **Resources** tab → find `worker` dyno → toggle it **ON**
2. Bot is now running 🎉

### Step 8 — MongoDB (free)
Use [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register):
1. Create free M0 cluster
2. Add database user + allow all IPs (0.0.0.0/0)
3. Get connection string → paste as `DATABASE_URL` in Heroku config vars

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| APP_ID | ✅ | — | Telegram API ID |
| API_HASH | ✅ | — | Telegram API Hash |
| BOT_TOKEN | ✅ | — | Bot token |
| OWNER | ✅ | — | Owner user ID |
| DATABASE_URL | ✅ | — | MongoDB URI |
| DEFAULT_CODEC | | hevc265 | av1/hevc265/hevc264 |
| DEFAULT_CRF | | 24 | CRF value |
| DEFAULT_PRESET | | slow | Encode preset |
| DUAL_AUDIO | | True | Keep 2 audio tracks |
| AUDIO_LANG_1 | | jpn | Primary audio lang |
| AUDIO_LANG_2 | | eng | Secondary audio lang |
| UPLOAD_AS_VIDEO | | True | Upload as video vs doc |
| AUTO_PREFIX | | — | Global filename prefix |
| AUTO_SUFFIX | | — | Global filename suffix |
| CAP_DECO | | — | Caption emoji/prefix |
| RELEASER | | — | Release group tag |
| LOG_CHANNEL | | — | Log channel ID |
| DUMP_CHANNEL | | — | Dump encoded files here |
| SAMPLE_DURATION | | 60 | Sample clip length (s) |
| SCREENSHOT_COUNT | | 10 | Number of screenshots |
| MAX_QUEUE | | 10 | Max queued jobs |
| WORKERS | | 4 | Pyrogram workers |
| LOCK_ON_STARTUP | | False | Lock encoding at start |
| ALWAYS_DEPLOY_LATEST | | False | git pull on startup |

---

## Commands

| Command | Description |
|---------|-------------|
| /start | Start bot |
| /help | Full help |
| /encode | Encode replied video |
| /sample | Generate sample clip |
| /screenshots | Generate screenshots |
| /setcodec | Choose codec (inline buttons) |
| /setcrf [n] | Set CRF |
| /setpreset | Choose preset (inline buttons) |
| /setbitdepth [8\|10] | Set bit depth |
| /dualaudio [on\|off] | Toggle dual audio |
| /setprefix [text] | Set filename prefix |
| /setsuffix [text] | Set filename suffix |
| /setrename [pat\|rep] | Set regex rename rule |
| /clearrename | Clear rename rule |
| /setthumb | Set custom thumbnail |
| /delthumb | Delete custom thumbnail |
| /viewthumb | Preview thumbnail |
| /mysettings | View all settings |
| /reset | Reset settings |
| /queue | Queue status |
| /lock | Lock encoding (owner) |
| /unlock | Unlock encoding (owner) |
| /clearqueue | Clear queue (owner) |
| /stats | Bot stats |
| /broadcast [msg] | Broadcast (owner) |
