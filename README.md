# Unsaved

Unsaved turns saved links into usable notes.

Paste an Instagram or YouTube link. Get a Markdown note with the central idea, a real breakdown of the content, why it matters, and one next action inside 48 hours.

It is a Claude Code skill, not a SaaS yet.

## Why this exists

The save button is a graveyard.

Most tools save the link. The link was never the problem.

A carousel is images of text. A reel is speech. A video is an hour of context. A bookmark manager stores the container and leaves you to do the work later.

Unsaved reads the content and turns it into a note you can use.

## What works now

| Source | Status | Cost |
|---|---|---|
| Instagram carousel | Works through public embed | $0 |
| Instagram image post | Works through public embed | $0 |
| Instagram reel caption | Works through public embed | $0 |
| YouTube with captions | Works through yt-dlp | $0 |
| YouTube without captions | Works through local faster-whisper | $0 |

## What it does not do

- It does not sync your saved folder.
- It does not ask for Instagram cookies.
- It does not silently spend API credits.
- It does not invent missing speech from reels.
- It does not ship a web interface yet.

## Why it does not sync your saves

The magic version asks for your Instagram session, scrapes your saved folder, and breaks the next time Instagram changes something.

Unsaved starts smaller on purpose: paste one link, extract one piece of content, produce one useful note.

That path keeps the default product free, simpler, and safer.

## Install

Clone this repo into your Claude Code skills folder:

```bash
cd ~/.claude/skills
git clone https://github.com/evedark/unsaved.git unsaved
```

Or copy this folder into:

```text
~/.claude/skills/unsaved
```

Then restart Claude Code or reload skills.

## Optional setup

Copy the example config:

```bash
cp unsaved.config.example.md unsaved.config.md
```

Edit `unsaved.config.md` with your actual work, projects, goals, and problems.

Do not add secrets. Do not commit the config file.

## Usage

Give Claude Code a link:

```text
Use Unsaved on this: https://www.instagram.com/p/SHORTCODE/
```

or:

```text
Use Unsaved on this YouTube video and save the note.
```

The note follows this schema:

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
<connection to your actual context, or a neutral line if no config exists>

## Next action (48h)
<one concrete action due by YYYY-MM-DD, or `none` if `target_problem: none`>

## Limits
<any missing caption, inaccessible slide, untranscribed speech, or extraction caveat>
```

## Scripts

Instagram public embed:

```bash
python scripts/ig_embed.py "https://www.instagram.com/p/SHORTCODE/" ./scratch/ig
```

YouTube local transcription fallback:

```bash
python scripts/transcribe_url.py "https://www.youtube.com/watch?v=VIDEO_ID" --model medium
```

## Dependencies

Minimum:

```bash
python -m pip install requests pillow yt-dlp
```

Only needed for YouTube videos without captions:

```bash
python -m pip install faster-whisper
```

You also need `ffmpeg` for local transcription.

## Examples

See `examples/` for public, sanitized example notes.

They are not copied from a private vault. They show the output shape without exposing client work, private context, or credentials.

## License

MIT
