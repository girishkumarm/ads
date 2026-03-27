#!/usr/bin/env python3
"""
Telegram Notification Helper for Trading Alerts
Replaces ntfy.sh — same interface, works on server (no Zscaler)

Usage:
  python3 notify.py send "Your message here"
  python3 notify.py send "Message" --title "Alert Title" --priority high
  python3 notify.py ask "Need OTP for Upstox" --timeout 120
  python3 notify.py poll --since 5m
"""

import sys
import json
import time
import os
import urllib.request
import urllib.parse
import urllib.error
import ssl

# SSL context — disable verification only behind Zscaler proxy (local dev)
SSL_CTX = ssl.create_default_context()
if os.environ.get("SKIP_SSL_VERIFY") or os.path.exists(os.path.expanduser("~/Library")):
    SSL_CTX.check_hostname = False
    SSL_CTX.verify_mode = ssl.CERT_NONE

# Config path — works on both MacBook and server
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "telegram-config.json")

PRIORITY_EMOJI = {
    "urgent": "🚨",
    "high":   "⚠️",
    "default": "",
    "low":    "ℹ️",
}

def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)

def send_message(text, title=None, priority="default", tags=None, audience="all"):
    """Send a message to user via Telegram bot.
    audience: 'all' = both Girish + Pooja (trading alerts)
              'girish' = only Girish (resort/ads/SEO stuff)
    """
    config = load_config()

    # Format message with title and priority emoji
    emoji = PRIORITY_EMOJI.get(priority, "")
    parts = []
    if title:
        header = f"{emoji} *{title}*" if emoji else f"*{title}*"
        parts.append(header)
    elif emoji:
        text = f"{emoji} {text}"
    parts.append(text)

    full_text = "\n".join(parts)

    url = f"https://api.telegram.org/bot{config['bot_token']}/sendMessage"

    # Determine recipients based on audience
    if audience == "girish":
        chat_ids = [config.get("chat_id_girish", config["chat_id"])]
    else:
        chat_ids = config.get("chat_ids", [config["chat_id"]])

    # Split long messages (Telegram 4096 char limit)
    MAX_LEN = 4000  # Leave margin for safety
    chunks = []
    if len(full_text) <= MAX_LEN:
        chunks = [full_text]
    else:
        lines = full_text.split("\n")
        chunk = ""
        for line in lines:
            if len(chunk) + len(line) + 1 > MAX_LEN:
                if chunk:
                    chunks.append(chunk)
                chunk = line
            else:
                chunk = f"{chunk}\n{line}" if chunk else line
        if chunk:
            chunks.append(chunk)

    success = False
    for cid in chat_ids:
        for chunk in chunks:
            # Try Markdown first, fall back to plain text on parse error
            for parse_mode in ["Markdown", None]:
                payload = {"chat_id": cid, "text": chunk}
                if parse_mode:
                    payload["parse_mode"] = parse_mode
                data = urllib.parse.urlencode(payload).encode()
                try:
                    req = urllib.request.Request(url, data=data)
                    resp = urllib.request.urlopen(req, context=SSL_CTX, timeout=10)
                    result = json.loads(resp.read().decode())
                    if result.get("ok"):
                        msg_id = result["result"]["message_id"]
                        print(f"Sent: {msg_id}")
                        success = True
                        break  # Sent successfully, don't retry plain text
                    else:
                        # If Markdown parse failed, retry as plain text
                        if parse_mode and "parse" in str(result).lower():
                            continue
                        print(f"Telegram error for {cid}: {result}")
                        break
                except urllib.error.HTTPError as e:
                    err_body = e.read().decode() if e.fp else ""
                    if parse_mode and e.code == 400 and "parse" in err_body.lower():
                        continue  # Retry without Markdown
                    print(f"Failed to send to {cid}: HTTP {e.code}")
                    break
                except Exception as e:
                    print(f"Failed to send to {cid}: {e}")
                    break
    return success

def get_updates(offset=None, timeout_sec=5):
    """Fetch updates from Telegram getUpdates API."""
    config = load_config()
    params = {"timeout": timeout_sec, "allowed_updates": ["message"]}
    if offset is not None:
        params["offset"] = offset

    url = f"https://api.telegram.org/bot{config['bot_token']}/getUpdates?" + urllib.parse.urlencode(params)
    try:
        req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req, context=SSL_CTX, timeout=timeout_sec + 5)
        result = json.loads(resp.read().decode())
        if result.get("ok"):
            return result.get("result", [])
        return []
    except Exception as e:
        print(f"Failed to get updates: {e}", file=sys.stderr)
        return []

def get_latest_offset():
    """Get the update_id of the most recent message (to ignore old ones)."""
    updates = get_updates()
    if updates:
        return updates[-1]["update_id"] + 1
    return None

def _get_offset_file():
    """Path to persisted Telegram offset file."""
    return os.path.join(SCRIPT_DIR, ".telegram-offset")

def _load_offset():
    """Load persisted offset to avoid re-processing messages."""
    path = _get_offset_file()
    try:
        if os.path.exists(path):
            with open(path) as f:
                return int(f.read().strip())
    except (ValueError, IOError):
        pass
    return None

def _save_offset(offset):
    """Persist offset so future poll calls skip already-seen messages."""
    path = _get_offset_file()
    try:
        with open(path, "w") as f:
            f.write(str(offset))
    except IOError:
        pass

def poll_replies(since="2m"):
    """Get recent messages from user, filtered by time window.
    since: e.g. '2m' for last 2 minutes, '5m' for last 5 minutes, '1h' for 1 hour."""
    import re
    # Parse since into seconds (supports s, m, h)
    match = re.match(r'(\d+)([smh]?)', since)
    if match:
        val = int(match.group(1))
        unit = match.group(2) or 'm'
        multipliers = {'s': 1, 'm': 60, 'h': 3600}
        since_secs = val * multipliers.get(unit, 60)
    else:
        since_secs = 120

    config = load_config()
    # Use persisted offset to avoid re-processing old messages
    offset = _load_offset()
    updates = get_updates(offset=offset)
    chat_ids = [str(c) for c in config.get("chat_ids", [config["chat_id"]])]
    now = int(time.time())
    messages = []
    max_update_id = None
    for update in updates:
        update_id = update.get("update_id", 0)
        if max_update_id is None or update_id > max_update_id:
            max_update_id = update_id
        msg = update.get("message", {})
        msg_time = msg.get("date", 0)
        # Only include messages within the time window
        if now - msg_time > since_secs:
            continue
        if str(msg.get("chat", {}).get("id")) in chat_ids:
            text = msg.get("text", "").strip()
            caption = msg.get("caption", "").strip()

            # Handle media messages (photo, video, voice, document)
            media_type = None
            file_id = None
            if msg.get("photo"):
                media_type = "photo"
                file_id = msg["photo"][-1]["file_id"]  # Largest resolution
            elif msg.get("video"):
                media_type = "video"
                file_id = msg["video"]["file_id"]
            elif msg.get("voice"):
                media_type = "voice"
                file_id = msg["voice"]["file_id"]
            elif msg.get("document"):
                media_type = "document"
                file_id = msg["document"]["file_id"]
            elif msg.get("video_note"):
                media_type = "video_note"
                file_id = msg["video_note"]["file_id"]

            if file_id:
                # Download the media file
                local_path = _download_telegram_file(config, file_id, media_type)
                if local_path:
                    # Voice messages → transcribe to text command
                    if media_type in ("voice", "video_note"):
                        transcribed = _transcribe_voice(local_path)
                        if transcribed:
                            messages.append(transcribed)
                            continue
                    # Photos/videos → media tag for ad creation
                    media_text = f"[MEDIA:{media_type}:{local_path}]"
                    if caption:
                        media_text += f" {caption}"
                    messages.append(media_text)
                    continue

            if text:
                messages.append(text)
    # Advance offset so these messages are never re-processed
    if max_update_id is not None:
        _save_offset(max_update_id + 1)
    if messages:
        for msg_text in messages:
            print(msg_text)
        return messages
    print("No messages")
    return []


def _transcribe_voice(audio_path):
    """Convert voice/audio to text using OpenAI Whisper."""
    try:
        os.environ["PATH"] = "/home/girish/.local/bin:" + os.environ.get("PATH", "")
        import whisper
        model = whisper.load_model("base")  # Small, fast model
        result = model.transcribe(audio_path, language="en")
        text = result.get("text", "").strip()
        if text:
            print(f"Transcribed voice: {text}", file=sys.stderr)
            return text
    except Exception as e:
        print(f"Whisper transcription failed: {e}", file=sys.stderr)
    return None


def _download_telegram_file(config, file_id, media_type="photo"):
    """Download a file from Telegram and save locally."""
    media_dir = os.path.join(SCRIPT_DIR, "media-inbox")
    os.makedirs(media_dir, exist_ok=True)

    try:
        # Get file path from Telegram
        url = f"https://api.telegram.org/bot{config['bot_token']}/getFile?" + urllib.parse.urlencode({"file_id": file_id})
        req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req, context=SSL_CTX, timeout=15)
        result = json.loads(resp.read().decode())
        if not result.get("ok"):
            return None

        file_path = result["result"]["file_path"]
        ext = os.path.splitext(file_path)[1] or {
            "photo": ".jpg", "video": ".mp4", "voice": ".ogg",
            "document": "", "video_note": ".mp4"
        }.get(media_type, "")

        # Download the file
        download_url = f"https://api.telegram.org/file/bot{config['bot_token']}/{file_path}"
        local_name = f"{media_type}_{int(time.time())}{ext}"
        local_path = os.path.join(media_dir, local_name)

        req2 = urllib.request.Request(download_url)
        resp2 = urllib.request.urlopen(req2, context=SSL_CTX, timeout=60)
        with open(local_path, "wb") as f:
            f.write(resp2.read())

        file_size = os.path.getsize(local_path)
        print(f"Downloaded {media_type}: {local_path} ({file_size} bytes)", file=sys.stderr)
        return local_path
    except Exception as e:
        print(f"Failed to download {media_type}: {e}", file=sys.stderr)
        return None

def send_photo(photo_path, caption=None, title=None, priority="default", audience="all"):
    """Send a photo to user via Telegram bot."""
    config = load_config()

    emoji = PRIORITY_EMOJI.get(priority, "")
    if caption and title:
        header = f"{emoji} *{title}*" if emoji else f"*{title}*"
        caption = f"{header}\n{caption}"
    elif title:
        caption = f"{emoji} *{title}*" if emoji else f"*{title}*"

    url = f"https://api.telegram.org/bot{config['bot_token']}/sendPhoto"
    if audience == "girish":
        chat_ids = [config.get("chat_id_girish", config["chat_id"])]
    else:
        chat_ids = config.get("chat_ids", [config["chat_id"]])

    success = False
    for cid in chat_ids:
        try:
            # Build multipart form data manually
            boundary = "----PythonBoundary"
            body = []
            body.append(f"--{boundary}")
            body.append(f'Content-Disposition: form-data; name="chat_id"\r\n')
            body.append(str(cid))
            if caption:
                body.append(f"--{boundary}")
                body.append(f'Content-Disposition: form-data; name="caption"\r\n')
                body.append(caption)
                body.append(f"--{boundary}")
                body.append(f'Content-Disposition: form-data; name="parse_mode"\r\n')
                body.append("Markdown")
            body.append(f"--{boundary}")
            body.append(f'Content-Disposition: form-data; name="photo"; filename="{os.path.basename(photo_path)}"')
            body.append(f"Content-Type: image/jpeg\r\n")

            # Read photo data
            with open(photo_path, "rb") as f:
                photo_data = f.read()

            # Assemble
            pre = ("\r\n".join(body) + "\r\n").encode()
            post = f"\r\n--{boundary}--\r\n".encode()
            payload = pre + photo_data + post

            req = urllib.request.Request(url, data=payload)
            req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
            resp = urllib.request.urlopen(req, context=SSL_CTX, timeout=30)
            result = json.loads(resp.read().decode())
            if result.get("ok"):
                msg_id = result["result"]["message_id"]
                print(f"Photo sent: {msg_id}")
                success = True
            else:
                print(f"Photo error for {cid}: {result}")
        except Exception as e:
            print(f"Failed to send photo to {cid}: {e}")
    return success

def ask_and_wait(question, timeout=7200, title=None, priority="urgent", tags="question"):
    """Send a question and wait for the user's reply. Returns reply text."""
    config = load_config()

    # Get current offset BEFORE sending question (to ignore all old messages)
    offset = get_latest_offset()

    # Send the question
    send_message(question, title=title, priority=priority, tags=tags)

    start = time.time()
    print(f"Waiting for reply (timeout: {timeout}s)...", file=sys.stderr)

    while time.time() - start < timeout:
        time.sleep(3)
        try:
            updates = get_updates(offset=offset)
            chat_ids = [str(c) for c in config.get("chat_ids", [config["chat_id"]])]
            for update in updates:
                msg = update.get("message", {})
                if str(msg.get("chat", {}).get("id")) in chat_ids:
                    text = msg.get("text", "").strip()
                    if text:
                        # Advance offset so we don't re-read this message
                        offset = update["update_id"] + 1
                        print(text)
                        return text
                # Always advance offset even for non-matching updates
                offset = update["update_id"] + 1
        except Exception as e:
            print(f"Poll error: {e}", file=sys.stderr)

    print("NO_REPLY")
    return None

# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 notify.py [send|ask|poll] [message] [--title T] [--priority P] [--timeout N]")
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]
    message = args[0] if args and not args[0].startswith("--") else ""

    def get_flag(flag, default=None):
        if flag in args:
            idx = args.index(flag)
            if idx + 1 < len(args):
                return args[idx + 1]
        return default

    if command == "send":
        send_message(
            message or "Test notification",
            title=get_flag("--title"),
            priority=get_flag("--priority", "default"),
            tags=get_flag("--tags"),
            audience=get_flag("--audience", "all")
        )

    elif command == "ask":
        ask_and_wait(
            message or "Please reply",
            timeout=int(get_flag("--timeout", "120")),
            title=get_flag("--title", "Action Required"),
            priority=get_flag("--priority", "urgent")
        )

    elif command == "photo":
        photo_path = message
        send_photo(
            photo_path,
            caption=get_flag("--caption"),
            title=get_flag("--title"),
            priority=get_flag("--priority", "default")
        )

    elif command == "poll":
        poll_replies(get_flag("--since", "5m"))

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
