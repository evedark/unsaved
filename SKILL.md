---
name: unsaved
description: Turn saved Instagram and YouTube links into applied Markdown notes. Use when the user gives an Instagram or YouTube URL and wants the content extracted, summarized, saved, or converted into reusable knowledge.
argument-hint: <Instagram or YouTube URL>
---

# Unsaved

Unsaved turns a saved link into a usable note.

It is not a bookmark manager. It reads the media, extracts the idea, connects it to the user's current work, and ends with one dated action inside 48 hours.

## Supported sources

| Source | Default path | Cost | Notes |
|---|---|---|---|
| Instagram carousel or image | Public embed endpoint | $0 | No login, browser, cookies, or API key |
| Instagram reel without speech | Public embed endpoint | $0 | Caption and visual content only |
| Instagram reel with speech | Optional paid provider, bring your own key | Paid | Off by default. Never invent speech |
| YouTube with captions | yt-dlp subtitles | $0 | Manual captions first, auto captions second |
| YouTube without captions | `<skill-dir>/scripts/transcribe_url.py` with faster-whisper | $0 | Local transcription, slower |

## Skill folder

The helper scripts live inside this skill, not in the user's project. `<skill-dir>` below means the folder that contains this `SKILL.md`, usually `~/.claude/skills/unsaved`. Resolve it to an absolute path before running a script. Output folders like `./scratch/` stay relative to the user's current project.

## Workflow

1. Get the URL.
2. Identify the platform:
   - Instagram: `/p/`, `/reel/`, `/tv/`, or any `instagram.com` URL.
   - YouTube: `youtube.com/watch`, `youtu.be`, or `youtube.com/shorts`.
3. Extract the content.
4. Produce a Markdown note using the schema below.
5. If the user has an `unsaved.config.md`, use it for the personal context section. If not, stay neutral.
6. Save the note to the configured destination. Default: `./unsaved-notes/`.

## Instagram extraction

For carousels and images, use the public embed script:

```bash
python "<skill-dir>/scripts/ig_embed.py" "<instagram-url-or-shortcode>" "./scratch/ig"
```

The script prints the caption, downloads `slide01.jpg`, `slide02.jpg`, and so on, and creates `contact.jpg` for visual review.

Read the caption and the slide images. If a slide is too small in `contact.jpg`, inspect the individual slide image.

If the embed returns no content, degrade honestly:

- Ask the user to paste the caption or screenshots.
- Do not guess what the post said.
- If speech from an Instagram reel matters and no paid provider is configured, say the speech was not transcribed.

## YouTube extraction

First get metadata:

```bash
python -m yt_dlp --skip-download --no-warnings   --print "%(title)s
%(uploader)s
%(duration_string)s
%(upload_date)s
%(webpage_url)s"   "<youtube-url>"
```

Then download the best available captions:

```bash
mkdir -p ./scratch/yt
python -m yt_dlp --skip-download --no-warnings   --write-subs --write-auto-subs   --sub-langs "pt-BR,pt,en,en-orig"   --sub-format vtt   -o "./scratch/yt/%(id)s.%(ext)s"   "<youtube-url>"
```

Use fixed subtitle languages. Do not use wildcard subtitle patterns because they can download many translations and trigger rate limits.

If no caption file exists, transcribe locally:

```bash
python "<skill-dir>/scripts/transcribe_url.py" "<youtube-url>" --model medium
```

Use the transcript to synthesize. Do not paste a raw transcript into the note unless the user asks for it.

## User context

If `unsaved.config.md` exists, read it before writing the sections `Why this matters` and `Next action (48h)`.

If it does not exist:

- Write a neutral `Why this matters` section.
- Do not pretend to know the user's business, goals, clients, or projects.

## Note schema

```markdown
---
type: unsaved-note
source: "<original URL>"
platform: instagram | youtube
format: carousel | image | reel | video | short
saved_at: <YYYY-MM-DD>
target_problem: "<current problem this helps solve>" | none
tags: [ ... ]
status: complete | partial
---

# <content title>

**Central idea:** <1-2 sentences>

## Breakdown
- <the real content, not a generic summary>

## Why this matters
<connection to the user's actual context, or a neutral line if no context file exists>

## Next action (48h)
<one concrete action due by YYYY-MM-DD, or `none` if `target_problem: none`>

## Limits
<any missing caption, inaccessible slide, untranscribed speech, or extraction caveat>
```

## Rules

- One note, one link.
- One concrete next action, not a checklist.
- If there is no real target problem, set `target_problem: none` and add the tag `shelf-help`.
- Never sync a user's saved folder.
- Never ask for Instagram cookies.
- Never store API keys, tokens, cookies, or private context in the repo.
- Never invent missing content.
- Prefer smaller honest extraction over a fragile magic workflow.

## Troubleshooting

### `python -m yt_dlp` instead of `yt-dlp`

Some systems block the `yt-dlp` launcher. `python -m yt_dlp` is more reliable.

### Instagram speech is not free by default

`yt-dlp` often fails on Instagram reels with:

```text
Instagram sent an empty media response ... use --cookies-from-browser
```

Unsaved does not use browser cookies. If speech from a reel is required, use an optional provider with the user's own key, or mark the note as partial.

### Public embed stops working

If Instagram changes or blocks the embed endpoint, ask for the caption/screenshots and continue from the user-provided source. Do not break the whole workflow.
