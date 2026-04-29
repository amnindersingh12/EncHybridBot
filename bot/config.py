import os
from dotenv import load_dotenv

load_dotenv()

# ── Core ──────────────────────────────────────────────────────────────────────
APP_ID           = int(os.environ.get("APP_ID", 0))
API_HASH         = os.environ.get("API_HASH", "")
BOT_TOKEN        = os.environ.get("BOT_TOKEN", "")
OWNER            = int(os.environ.get("OWNER", 0))

# ── Database ──────────────────────────────────────────────────────────────────
DATABASE_URL     = os.environ.get("DATABASE_URL", "")
DBNAME           = os.environ.get("DBNAME", "encbot")

# ── Encoding ──────────────────────────────────────────────────────────────────
# Preset ffmpeg command; if unset, bot uses codec selected at runtime
FFMPEG           = os.environ.get("FFMPEG", "")
FFMPEG2          = os.environ.get("FFMPEG2", "")
FFMPEG3          = os.environ.get("FFMPEG3", "")
FFMPEG4          = os.environ.get("FFMPEG4", "")
MUX_ARGS         = os.environ.get("MUX_ARGS", "")

# ── Codec shortcuts (used when FFMPEG is empty) ───────────────────────────────
# av1 / hevc265 / hevc264
DEFAULT_CODEC    = os.environ.get("DEFAULT_CODEC", "hevc265")  # av1|hevc265|hevc264
DEFAULT_PRESET   = os.environ.get("DEFAULT_PRESET", "slow")
DEFAULT_CRF      = int(os.environ.get("DEFAULT_CRF", 24))
DUAL_AUDIO       = os.environ.get("DUAL_AUDIO", "True").lower() == "true"
AUDIO_LANG_1     = os.environ.get("AUDIO_LANG_1", "jpn")   # first audio track lang
AUDIO_LANG_2     = os.environ.get("AUDIO_LANG_2", "eng")   # second audio track lang

# ── Upload behaviour ──────────────────────────────────────────────────────────
UPLOAD_AS_VIDEO          = os.environ.get("UPLOAD_AS_VIDEO", "True").lower() == "true"
UPLOAD_VIDEO_AS_SPOILER  = os.environ.get("UPLOAD_VIDEO_AS_SPOILER", "False").lower() == "true"
FILENAME_AS_CAPTION      = os.environ.get("FILENAME_AS_CAPTION", "True").lower() == "true"

# ── Rename / Caption ──────────────────────────────────────────────────────────
CUSTOM_RENAME    = os.environ.get("CUSTOM_RENAME", "")   # regex replace rule "pattern|replacement"
AUTO_PREFIX      = os.environ.get("AUTO_PREFIX", "")     # prepend to every output filename
AUTO_SUFFIX      = os.environ.get("AUTO_SUFFIX", "")     # append  to every output filename
CAP_DECO         = os.environ.get("CAP_DECO", "")        # emoji/prefix for captions
RELEASER         = os.environ.get("RELEASER", "")        # release group tag e.g. [GRP]

# ── Thumbnail ─────────────────────────────────────────────────────────────────
THUMBNAIL        = os.environ.get("THUMBNAIL", "")       # path or Telegram file_id

# ── Users / Auth ──────────────────────────────────────────────────────────────
TEMP_USERS       = [int(u) for u in os.environ.get("TEMP_USERS", "").split() if u]
ENCODER          = os.environ.get("ENCODER", "")         # user_id allowed to encode
WORKERS          = int(os.environ.get("WORKERS", 4))

# ── Channels ──────────────────────────────────────────────────────────────────
LOG_CHANNEL      = int(os.environ.get("LOG_CHANNEL", 0) or 0)
LOGS_IN_CHANNEL  = os.environ.get("LOGS_IN_CHANNEL", "False").lower() == "true"
DUMP_LEECH       = os.environ.get("DUMP_LEECH", "True").lower() == "true"
DUMP_CHANNEL     = int(os.environ.get("DUMP_CHANNEL", 0) or 0)

# Forward channel
FCHANNEL         = int(os.environ.get("FCHANNEL", 0) or 0)
FCHANNEL_STAT    = int(os.environ.get("FCHANNEL_STAT", 0) or 0)
FCODEC           = os.environ.get("FCODEC", "")
FBANNER          = os.environ.get("FBANNER", "False").lower() == "true"
NO_BANNER        = os.environ.get("NO_BANNER", "False").lower() == "true"
C_LINK           = os.environ.get("C_LINK", "")

# ── Download managers ─────────────────────────────────────────────────────────
ARIA2_PORT       = int(os.environ.get("ARIA2_PORT", 6800))
QBIT_PORT        = int(os.environ.get("QBIT_PORT", 8090))
ARIA2_DL_TIMEOUT = int(os.environ.get("ARIA2_DL_TIMEOUT", 3600))
QBIT_DL_TIMEOUT  = int(os.environ.get("QBIT_DL_TIMEOUT", 3600))
CACHE_DL         = os.environ.get("CACHE_DL", "False").lower() == "true"

# ── RSS ───────────────────────────────────────────────────────────────────────
RSS_CHAT         = int(os.environ.get("RSS_CHAT", 0) or 0)
RSS_DELAY        = int(os.environ.get("RSS_DELAY", 600))
RSS_DIRECT       = os.environ.get("RSS_DIRECT", "False").lower() == "true"
USE_ANILIST      = os.environ.get("USE_ANILIST", "True").lower() == "true"

# ── Telegraph ─────────────────────────────────────────────────────────────────
TELEGRAPH_API    = os.environ.get("TELEGRAPH_API", "")
TELEGRAPH_AUTHOR = os.environ.get("TELEGRAPH_AUTHOR", "EncBot")

# ── Misc ──────────────────────────────────────────────────────────────────────
CMD_SUFFIX             = os.environ.get("CMD_SUFFIX", "")
FLOOD_SLEEP_THRESHOLD  = int(os.environ.get("FLOOD_SLEEP_THRESHOLD", 60))
LOCK_ON_STARTUP        = os.environ.get("LOCK_ON_STARTUP", "False").lower() == "true"
ALLOW_ACTION           = os.environ.get("ALLOW_ACTION", "True").lower() == "true"
REPORT_FAILED          = os.environ.get("REPORT_FAILED", "True").lower() == "true"
ALWAYS_DEPLOY_LATEST   = os.environ.get("ALWAYS_DEPLOY_LATEST", "False").lower() == "true"
USE_CAPTION            = os.environ.get("USE_CAPTION", "True").lower() == "true"
PODI                   = os.environ.get("PODI", "False").lower() == "true"

# ── Sample video ──────────────────────────────────────────────────────────────
SAMPLE_DURATION  = int(os.environ.get("SAMPLE_DURATION", 60))   # seconds
SAMPLE_START     = int(os.environ.get("SAMPLE_START", 0))       # offset seconds

# ── Screenshot ────────────────────────────────────────────────────────────────
SCREENSHOT_COUNT = int(os.environ.get("SCREENSHOT_COUNT", 10))

# ── Queue ─────────────────────────────────────────────────────────────────────
MAX_QUEUE        = int(os.environ.get("MAX_QUEUE", 10))
