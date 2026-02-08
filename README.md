# Perplexity Export (JSON + XLSX)

Convert Perplexity conversation provided after GDPR requests, into organized files. It currently only supports the Markdown format.

## Disclaimer
This project has been currently created making heavy use of LLMs, please be advise, and report any error, or fix them if you know how.

## Features

- Converts Perplexity JSON exports to individual markdown files
- Organizes conversations by collection into separate directories (customizable)
- Configurable filename length and date formatting
- Flexible asset path configuration (needs testing)
- Optional wikilinks format for assets (i.e. for Obsidian) (needs testing)
- Preserves conversation metadata (date, title, mode)
- Error logging for failed exports
- Automatic filename collision resolution
- Empty citations removal from answers
- Automatic heading demotion
- Conservative character sanitization for filenames and metadata

## Requirements

- Python 3.11 or higher
- uv package manager

## Installation

### Install uv

If you don't have uv installed, visit the official documentation:
**[https://docs.astral.sh/uv/getting-started/installation](https://docs.astral.sh/uv/getting-started/installation)**

### Setup Project

Clone or download this project, then sync dependencies:

```bash
git clone <repository>
cd perplexity-export-convert
uv sync
```

This will:
- Create a virtual environment
- Install the projectl dependencies

## Usage

### Basic Usage

copy the `.json`, `.xlsx`, and `assets` directories into the cloned repository, from here run it with `uv run perplexity-export-convert.py <convertations>.json`

## Configuration

Create a copy of `config.toml.example`, and name it `config.toml`, then modify it to fit your needs.

### Collection Mappings

Map collection UUIDs to the ones you use on Perplexity. You'll probably need a first export to find these out... then you can insert the UUIDs and the names in the configuration file, delete the first export, and export again. Your files will now be named as you defined them.


## Markdown Format

Each exported file contains:

```markdown
---
Date: 2026-01-31
Title: Is this DDR2 or DDR3 memory_
Export date: 2026-02-03
---
# Query
Is this DDR2 or DDR3 memory?

# Answer (copilot - 20260131T142558)
Based on the label visible in your image, this is **DDR2 memory**...
```

### Answer Heading Format

- Includes mode in lowercase: `(copilot)`, `(pro)`, etc.
- Includes creation timestamp in configured format: `- 20260131T142558`
- Includes status if not `COMPLETED`: `# Answer (copilot - 20260131T142558) FAILED`

## Error Logging

If any conversations fail to export, an `ERRORS.log` file is created in the output directory with:
- Timestamp of the error
- Conversation title that failed
- Detailed error message

## Filename Collision Handling

If multiple conversations have the same title:
1. The first one uses the base filename
2. Subsequent ones get a timestamp suffix

### Viewing Help

```bash
uv run perplexity-export-convert.py --help
```

## Support

if this script has helped you, and you want to support me, you can find all the options at https://furayoshi.com/support
