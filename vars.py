# ══════════════════════════════════════════════════════════════════════════════
# vars.py  –  Hardcoded configuration
# Fill values here OR set equivalent environment variables.
# Environment variables always take priority over values set here.
# ══════════════════════════════════════════════════════════════════════════════

# ── REQUIRED ──────────────────────────────────────────────────────────────────
# Get APP_ID and API_HASH from https://my.telegram.org
APP_ID      = 0          # e.g. 1234567
API_HASH    = ""         # e.g. "abc123def456..."
BOT_TOKEN   = ""         # from @BotFather e.g. "123456:ABC-DEF..."
OWNER       = 0          # your Telegram user ID (get from @userinfobot)

# ── DATABASE ──────────────────────────────────────────────────────────────────
# Free MongoDB: https://www.mongodb.com/cloud/atlas
DATABASE_URL = ""        # e.g. "mongodb+srv://user:pass@cluster.mongodb.net"
DBNAME       = "encbot"

# ── ENCODING DEFAULTS ─────────────────────────────────────────────────────────
DEFAULT_CODEC  = "hevc265"   # av1 | hevc265 | hevc264
DEFAULT_CRF    = 24
DEFAULT_PRESET = "slow"
DUAL_AUDIO     = True
AUDIO_LANG_1   = "jpn"       # primary audio track language
AUDIO_LANG_2   = "eng"       # secondary audio track language

# ── RENAME / CAPTION ──────────────────────────────────────────────────────────
AUTO_PREFIX = ""         # prepend to every output filename e.g. "@MyChannel - "
AUTO_SUFFIX = ""         # append  to every output filename e.g. " [Encoded]"
CAP_DECO    = "🎬"       # emoji/prefix added before captions
RELEASER    = ""         # release group tag e.g. "SubsPlease"

# ── UPLOAD ────────────────────────────────────────────────────────────────────
UPLOAD_AS_VIDEO         = True
UPLOAD_VIDEO_AS_SPOILER = False
FILENAME_AS_CAPTION     = True

# ── CHANNELS ──────────────────────────────────────────────────────────────────
LOG_CHANNEL     = 0      # channel ID to receive logs/errors
LOGS_IN_CHANNEL = False  # auto-dump errors to LOG_CHANNEL
DUMP_LEECH      = True   # also upload encoded file to DUMP_CHANNEL
DUMP_CHANNEL    = 0      # channel/group ID to dump encoded files

# Forward channel
FCHANNEL        = 0
FCODEC          = ""
FBANNER         = False
NO_BANNER       = False
C_LINK          = ""

# ── FEATURES ──────────────────────────────────────────────────────────────────
SAMPLE_DURATION  = 60    # sample clip length in seconds
SAMPLE_START     = 0     # sample clip start offset in seconds
SCREENSHOT_COUNT = 10    # number of screenshots to capture
MAX_QUEUE        = 10    # max simultaneous queued jobs

# ── MISC ──────────────────────────────────────────────────────────────────────
WORKERS              = 4
LOCK_ON_STARTUP      = False
ALWAYS_DEPLOY_LATEST = False
ALLOW_ACTION         = True
CACHE_DL             = False
ARIA2_PORT           = 6800
QBIT_PORT            = 8090
ARIA2_DL_TIMEOUT     = 3600
QBIT_DL_TIMEOUT      = 3600
RSS_CHAT             = 0
RSS_DELAY            = 600
RSS_DIRECT           = False
USE_ANILIST          = True
USE_CAPTION          = True
PODI                 = False
TELEGRAPH_API        = ""
TELEGRAPH_AUTHOR     = "EncBot"
CMD_SUFFIX           = ""
FLOOD_SLEEP_THRESHOLD = 60
