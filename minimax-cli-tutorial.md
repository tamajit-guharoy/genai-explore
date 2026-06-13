# MiniMax CLI (`mmx`) Tutorial

The MiniMax CLI (`mmx`) lets you generate **text, images, video, speech, and music**, perform **web search**, and understand **images** from the terminal — all powered by the MiniMax AI platform.

This tutorial walks through installation, authentication, every major command with working examples, and scripting/automation patterns.

---

## Table of Contents

1. [Installation & Setup](#1-installation--setup)
2. [Authentication](#2-authentication)
3. [Text Chat](#3-text-chat)
4. [Image Generation](#4-image-generation)
5. [Video Generation](#5-video-generation)
6. [Speech Synthesis (TTS)](#6-speech-synthesis-tts)
7. [Music Generation](#7-music-generation)
8. [Music Covers](#8-music-covers)
9. [Vision (Image Understanding)](#9-vision-image-understanding)
10. [Web Search](#10-web-search)
11. [Quota & Configuration](#11-quota--configuration)
12. [Scripting & Automation Patterns](#12-scripting--automation-patterns)
13. [Exit Codes Reference](#13-exit-codes-reference)

---

## 1. Installation & Setup

Install globally via npm:

```bash
npm install -g mmx-cli
```

Verify the installation:

```bash
mmx --version
```

Region is auto-detected. You can override it per call or persistently:

```bash
mmx text chat --message "Hello" --region global   # or --region cn
mmx config set --key region --value cn            # persist it
```

---

## 2. Authentication

You need a MiniMax API key (starts with `sk-`). There are three ways to provide it:

### Option A — Login once (recommended)

```bash
mmx auth login --api-key sk-xxxxx
```

This persists the key to `~/.mmx/config.json` (OAuth credentials go to `~/.mmx/credentials.json`).

### Option B — Environment variable

```bash
export MINIMAX_API_KEY=sk-xxxxx
```

### Option C — Per-call flag

```bash
mmx text chat --api-key sk-xxxxx --message "Hello"
```

Check which auth source is active:

```bash
mmx auth status
```

**Configuration precedence:** CLI flags → environment variables → `~/.mmx/config.json` → defaults.

---

## 3. Text Chat

Chat completions with MiniMax language models. Default model: `MiniMax-M2.7`.

### Basic usage

```bash
mmx text chat --message "What is MiniMax?"
```

### Roles and system prompts

Prefix messages with `role:` to control the conversation, or use `--system`:

```bash
# System prompt via flag
mmx text chat \
  --system "You are a coding assistant." \
  --message "user:Write fizzbuzz in Python"

# Roles inline (--message is repeatable for multi-turn)
mmx text chat \
  --message "system:You are a pirate." \
  --message "user:Tell me about the sea."
```

### Multi-turn conversations from a file

Save a conversation as JSON and pipe it in (`-` means stdin):

```json
// conversation.json
[
  { "role": "system", "content": "You are a helpful assistant." },
  { "role": "user", "content": "What is the capital of France?" },
  { "role": "assistant", "content": "Paris." },
  { "role": "user", "content": "And its population?" }
]
```

```bash
cat conversation.json | mmx text chat --messages-file - --output json
```

### Tuning generation

```bash
mmx text chat \
  --message "Write a haiku about autumn" \
  --model MiniMax-M2.7 \
  --max-tokens 200 \
  --temperature 0.9 \
  --top-p 0.95
```

### Machine-readable output

```bash
mmx text chat --message "Hi" --output json --quiet | jq '.content'
```

### Tool use

Pass tool definitions as JSON strings or file paths (repeatable):

```bash
mmx text chat \
  --message "What's the weather in Tokyo?" \
  --tool ./tools/get_weather.json \
  --output json
```

---

## 4. Image Generation

Generate images with the `image-01` model.

### Basic usage

```bash
mmx image generate --prompt "A cat in a spacesuit floating above Earth"
```

By default this prints image URLs. Add `--quiet` to get one URL per line (great for scripting).

### Download images to disk

```bash
mmx image generate \
  --prompt "Minimalist logo for a coffee shop" \
  --n 3 \
  --out-dir ./gen/ \
  --out-prefix logo \
  --quiet
# stdout: ./gen/logo-1.png  ./gen/logo-2.png  ./gen/logo-3.png (one per line)
```

### Control size and aspect ratio

```bash
# Aspect ratio (ignored if --width AND --height are set)
mmx image generate --prompt "Mountain panorama" --aspect-ratio 16:9

# Exact pixels (512–2048, multiples of 8; both flags required together)
mmx image generate --prompt "Avatar portrait" --width 1024 --height 1024
```

### Reproducible results & prompt optimization

```bash
# Same seed + same prompt = same image
mmx image generate --prompt "A red bicycle" --seed 42

# Let MiniMax improve your prompt first
mmx image generate --prompt "dog park" --prompt-optimizer
```

### Subject reference (consistent characters)

Keep the same character across generations using a reference image:

```bash
mmx image generate \
  --prompt "The character riding a horse through a desert" \
  --subject-ref "type=character,image=./my_character.png"
```

### Base64 output (skip CDN)

```bash
mmx image generate --prompt "Icon of a rocket" --response-format base64 --output json
```

---

## 5. Video Generation

Generate videos with `MiniMax-Hailuo-2.3` (default) or `MiniMax-Hailuo-2.3-Fast`. Video generation is an **async task** — by default the CLI polls until completion.

### Blocking: wait and download

```bash
mmx video generate \
  --prompt "Ocean waves crashing on a rocky shore at sunset" \
  --download ocean.mp4 \
  --quiet
# stdout: ocean.mp4
```

### Non-blocking: fire and check later

```bash
# 1. Submit the task — returns immediately
mmx video generate --prompt "A robot dancing in the rain" --async --quiet
# stdout: {"taskId":"23901234567"}

# 2. Check status whenever you like
mmx video task get --task-id 23901234567 --output json

# 3. Download when finished
mmx video download --file-id <file-id> --out robot.mp4
```

### Animate a still image (image-to-video)

```bash
mmx video generate \
  --prompt "Camera slowly zooms in as leaves rustle" \
  --first-frame ./photo.jpg \
  --download animated.mp4
```

### Faster model and webhook callback

```bash
mmx video generate \
  --prompt "Time-lapse of a city at night" \
  --model MiniMax-Hailuo-2.3-Fast \
  --callback-url https://example.com/webhook \
  --async
```

### Tune polling

```bash
mmx video generate --prompt "Snowfall in a forest" --poll-interval 10 --download snow.mp4
```

---

## 6. Speech Synthesis (TTS)

Text-to-speech with `speech-2.8-hd` (default). Max input: 10,000 characters.

### Basic usage

```bash
mmx speech synthesize --text "Hello world" --out hello.mp3 --quiet
# stdout: hello.mp3
```

### From a file or stdin

```bash
mmx speech synthesize --text-file article.txt --out article.mp3

echo "Breaking news: the build is green." | \
  mmx speech synthesize --text-file - --out news.mp3
```

### Voice, speed, pitch, and volume

```bash
mmx speech synthesize \
  --text "Welcome to the show!" \
  --voice English_expressive_narrator \
  --speed 1.1 \
  --pitch 2 \
  --volume 8 \
  --out intro.mp3
```

### Subtitles (SRT)

```bash
mmx speech synthesize --text "This video has captions." --subtitles --out clip.mp3
# Saves clip.mp3 AND clip.srt
```

### Audio quality settings

```bash
mmx speech synthesize \
  --text "High quality narration." \
  --format mp3 \
  --sample-rate 32000 \
  --bitrate 128000 \
  --channels 1 \
  --out narration.mp3
```

### Custom pronunciation and language boost

```bash
mmx speech synthesize \
  --text "The CEO of Xilinx spoke today." \
  --pronunciation "Xilinx/ZY-links" \
  --language en \
  --out news.mp3
```

### Stream raw audio to another program

```bash
mmx speech synthesize --text "Hello" --stream | ffplay -nodisp -autoexit -
```

---

## 7. Music Generation

Generate songs with `music-2.6-free` (unlimited for API key users, rate limit: 3 requests/min). At least one of `--prompt` or `--lyrics` is required.

### Three modes

```bash
# 1. Your own lyrics
mmx music generate \
  --prompt "Upbeat pop, bright synths" \
  --lyrics "[Verse] Walking down the sunny street..." \
  --out song.mp3 --quiet

# 2. Auto-generated lyrics from the prompt
mmx music generate \
  --prompt "Upbeat pop song about summer road trips" \
  --lyrics-optimizer \
  --out summer.mp3 --quiet

# 3. Instrumental (no vocals)
mmx music generate \
  --prompt "Cinematic orchestral, building tension, epic drums" \
  --instrumental \
  --out bgm.mp3 --quiet
```

> Note: `--lyrics`, `--lyrics-optimizer`, and `--instrumental` are mutually exclusive.

### Rich, structured prompts

The music model responds well to detailed descriptions. Dedicated flags help you structure them:

```bash
mmx music generate \
  --prompt "Warm morning folk song about fresh starts" \
  --vocals "male and female duet, harmonies in chorus" \
  --genre "folk" \
  --mood "warm, hopeful" \
  --instruments "acoustic guitar, piano, light percussion" \
  --bpm 95 \
  --key "C major" \
  --structure "verse-chorus-verse-bridge-chorus" \
  --avoid "electronic drums, autotune" \
  --use-case "podcast intro" \
  --references "similar to early Mumford & Sons" \
  --lyrics-file song.txt \
  --out duet.mp3
```

### Lyrics from stdin

```bash
cat lyrics.txt | mmx music generate --prompt "Acoustic ballad" --lyrics-file - --out ballad.mp3
```

---

## 8. Music Covers

Re-style an existing song using `music-cover-free` (unlimited for API key users, rate limit: 3 requests/min). Reference audio: 6 seconds to 6 minutes, max 50 MB (mp3, wav, flac, etc.).

### Cover from a URL

```bash
mmx music cover \
  --prompt "Indie folk, acoustic guitar, warm male vocal" \
  --audio https://filecdn.minimax.chat/public/d20eda57-2e36-45bf-9e12-82d9f2e69a86.mp3 \
  --out cover.mp3 --quiet
```

### Cover from a local file with your own lyrics

If `--lyrics` is omitted, lyrics are extracted from the reference audio automatically (ASR).

```bash
mmx music cover \
  --prompt "Jazz, piano, slow and smoky" \
  --audio-file original.mp3 \
  --lyrics-file lyrics.txt \
  --out jazz_cover.mp3 --quiet
```

### Reproducible covers

```bash
mmx music cover \
  --prompt "Pop, upbeat" \
  --audio-file original.mp3 \
  --seed 42 \
  --format wav --channel 2 \
  --out cover.wav
```

---

## 9. Vision (Image Understanding)

Ask questions about images with a vision-language model. Provide **either** `--image` **or** `--file-id`, not both.

```bash
# Local file (auto base64-encoded)
mmx vision describe --image photo.jpg --prompt "What breed is this dog?"

# Remote URL
mmx vision describe --image https://example.com/chart.png --prompt "Summarize this chart"

# Default prompt is "Describe the image."
mmx vision describe --image screenshot.png

# Pre-uploaded file (skips base64 encoding)
mmx vision describe --file-id 12345 --prompt "Extract all text" --output json
```

---

## 10. Web Search

```bash
mmx search query --q "MiniMax AI latest models"

# JSON for scripts
mmx search query --q "MiniMax AI" --output json --quiet | jq '.results[0]'
```

---

## 11. Quota & Configuration

### Check your usage

```bash
mmx quota show
mmx quota show --output json
```

### Persistent configuration

```bash
mmx config set --key region --value cn
mmx config show
```

### Default models per modality

Stop typing `--model` every time:

```bash
mmx config set --key default-text-model   --value MiniMax-M2.7-highspeed
mmx config set --key default-speech-model --value speech-2.8-hd
mmx config set --key default-video-model  --value MiniMax-Hailuo-2.3
mmx config set --key default-music-model  --value music-2.6

# Now these use your defaults:
mmx text chat --message "Hello"
mmx speech synthesize --text "Hello" --out hello.mp3

# --model still wins per call:
mmx text chat --model MiniMax-M2.7 --message "Hello"
```

**Model resolution priority:** `--model` flag → config default → hardcoded fallback.

### Export commands as agent tool schemas

Register `mmx` commands as tools in an Anthropic/OpenAI-compatible agent framework:

```bash
mmx config export-schema                              # all tool-worthy commands
mmx config export-schema --command "video generate"   # just one
```

---

## 12. Scripting & Automation Patterns

### Flags every script should know

| Flag | Purpose |
|---|---|
| `--non-interactive` | Fail fast on missing args instead of prompting |
| `--quiet` | Suppress spinners/progress; stdout is pure data |
| `--output json` | Machine-readable JSON output |
| `--async` | Return a task ID immediately (video) |
| `--dry-run` | Preview the API request without executing |
| `--yes` | Skip confirmation prompts |

`stdout` is always clean data; progress and spinners go to `stderr`. That makes piping safe:

```bash
mmx text chat --message "Hi" --output json | jq '.content'
mmx video generate --prompt "Waves" 2>/dev/null
```

### Chain commands: generate an image, then describe it

```bash
URL=$(mmx image generate --prompt "A sunset over mountains" --quiet)
mmx vision describe --image "$URL" --prompt "Write alt text for this image" --quiet
```

### Full async video pipeline

```bash
TASK=$(mmx video generate --prompt "A robot walking" --async --quiet | jq -r '.taskId')

# ... do other work ...

mmx video task get --task-id "$TASK" --output json
mmx video download --task-id "$TASK" --out robot.mp4
```

### Generate a narrated slideshow asset set

```bash
#!/usr/bin/env bash
set -euo pipefail

# 1. Script the narration
SCRIPT=$(mmx text chat --quiet --output json \
  --message "Write a 3-sentence narration about coral reefs" | jq -r '.content')

# 2. Narrate it with subtitles
mmx speech synthesize --text "$SCRIPT" --subtitles --out narration.mp3 --quiet

# 3. Matching background image
mmx image generate --prompt "Vibrant coral reef, underwater photography" \
  --aspect-ratio 16:9 --out-dir ./assets/ --quiet

# 4. Background music
mmx music generate --prompt "Calm ambient underwater soundscape" \
  --instrumental --out ./assets/bgm.mp3 --quiet
```

### Preview a request before spending quota

```bash
mmx video generate --prompt "Expensive 4K shot" --dry-run
```

### Handle errors by exit code

```bash
mmx text chat --message "Hello" --non-interactive --quiet
case $? in
  0)  echo "ok" ;;
  3)  echo "auth error — run: mmx auth login --api-key sk-..." ;;
  4)  echo "quota exceeded — check: mmx quota show" ;;
  10) echo "content filter triggered — rephrase the prompt" ;;
  *)  echo "failed" ;;
esac
```

---

## 13. Exit Codes Reference

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | General error |
| 2 | Usage error (bad flags, missing args) |
| 3 | Authentication error |
| 4 | Quota exceeded |
| 5 | Timeout |
| 10 | Content filter triggered |

---

## Quick Reference Card

```bash
mmx auth login --api-key sk-xxxxx                                  # authenticate
mmx text chat --message "Hello"                                    # chat
mmx image generate --prompt "A cat" --out-dir ./gen/               # image
mmx video generate --prompt "Waves" --download waves.mp4           # video (blocking)
mmx video generate --prompt "Waves" --async                        # video (task ID)
mmx speech synthesize --text "Hi" --out hi.mp3                     # TTS
mmx music generate --prompt "Pop" --lyrics-optimizer --out s.mp3   # music
mmx music cover --prompt "Jazz" --audio-file in.mp3 --out c.mp3    # cover
mmx vision describe --image photo.jpg --prompt "What is this?"     # vision
mmx search query --q "MiniMax AI"                                  # search
mmx quota show                                                     # usage
```
