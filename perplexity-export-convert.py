#!/usr/bin/env python3
"""
Perplexity Export to Markdown Converter

Converts Perplexity conversation exports (JSON + XLSX) into organized markdown files.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
import tomllib
import re


class PerplexityExporter:
    """Handles conversion of Perplexity exports to markdown files."""

    def __init__(self, config_path: Path = Path("config.toml")):
        """Initialize exporter with configuration."""
        self.config = self._load_config(config_path)
        self.export_date = datetime.now().strftime("%Y-%m-%d")
        self.errors = []

    def _load_config(self, config_path: Path) -> dict:
        """Load configuration from TOML file."""
        if not config_path.exists():
            print(f"Config file not found: {config_path}")
            print("Using default configuration...")
            return self._default_config()

        try:
            with open(config_path, "rb") as f:
                config = tomllib.load(f)
                print(f"✓ Loaded configuration from: {config_path}")
                # Debug: show what was loaded
                if config.get("collections"):
                    print(f"  Collections mapped: {len(config['collections'])} collection(s)")
                return config
        except Exception as e:
            print(f"Error loading config: {e}")
            print("Using default configuration...")
            return self._default_config()

    def _default_config(self) -> dict:
        """Return default configuration."""
        return {
            "filename": {
                "max_length": 128,
                "append_date": False,
                "date_format": "%Y%m%dT%H%M%S",
            },
            "assets": {
                "location": "assets",
                "relative_to_markdown": False,
            },
            "output": {
                "base_dir": "output",
                "wikilinks": False,
            },
            "collections": {},
        }

    def sanitize_text(self, text: str, for_metadata: bool = False) -> str:
        """Sanitize text for use in metadata or filenames."""
        # Remove or replace problematic characters
        # Remove newlines and carriage returns
        text = text.replace("\n", " ").replace("\r", " ")
        # Remove backticks
        text = text.replace("`", "")
        
        if for_metadata:
            # For metadata, be conservative - replace problematic symbols with underscore
            # Keep only: letters, numbers, spaces, periods, commas, hyphens, underscores, parentheses, quotes, @
            text = re.sub(r'[^a-zA-Z0-9\s.,\-_()\"@]+', '_', text)
        
        # Collapse multiple spaces
        text = re.sub(r'\s+', ' ', text)
        # Collapse multiple underscores
        text = re.sub(r'_+', '_', text)
        # Strip leading/trailing whitespace and underscores
        text = text.strip().strip('_')
        return text

    def sanitize_filename(self, title: str, reserve_for_date: int = 0) -> str:
        """Create a safe filename from title."""
        # First sanitize general problematic characters (same as metadata)
        # Remove newlines and carriage returns
        safe_title = title.replace("\n", " ").replace("\r", " ")
        # Remove backticks
        safe_title = safe_title.replace("`", "")
        
        # Replace problematic symbols with underscore
        # Keep only: letters, numbers, spaces, periods, commas, hyphens, underscores, parentheses, quotes, @
        safe_title = re.sub(r'[^a-zA-Z0-9\s.,\-_()\"@]+', '_', safe_title)
        
        # Remove filesystem invalid characters (these must be fully removed, not replaced)
        safe_title = re.sub(r'[<>:"/\\|?*]', '', safe_title)
        
        # Collapse multiple spaces and underscores
        safe_title = re.sub(r'\s+', ' ', safe_title)
        safe_title = re.sub(r'_+', '_', safe_title)
        
        # Strip leading/trailing whitespace and underscores
        safe_title = safe_title.strip().strip('_')

        # Calculate available length
        max_length = self.config.get("filename", {}).get("max_length", 128)
        available_length = max_length - reserve_for_date

        if len(safe_title) > available_length:
            safe_title = safe_title[:available_length].strip().strip('_')

        # Ensure filename is not empty
        if not safe_title:
            safe_title = "untitled"

        return safe_title

    def generate_unique_filename(self, title: str, created_at: str, output_dir: Path) -> str:
        """Generate unique filename, adding timestamp if collision occurs."""
        # Check if we should always append date
        filename_config = self.config.get("filename", {})
        append_date = filename_config.get("append_date", False)
        date_format = filename_config.get("date_format", "%Y%m%dT%H%M%S")

        # Parse timestamp
        if created_at:
            dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            date_suffix = dt.strftime(date_format)
        else:
            date_suffix = datetime.now().strftime(date_format)

        if append_date:
            # Always append date
            base_filename = self.sanitize_filename(title, reserve_for_date=len(date_suffix) + 1)
            filename = f"{base_filename}-{date_suffix}.md"
        else:
            # Only append if collision
            base_filename = self.sanitize_filename(title)
            filename = f"{base_filename}.md"
            filepath = output_dir / filename

            # Check for collision
            if filepath.exists():
                # Truncate by 15 chars and add timestamp
                truncate_amount = len(date_suffix) + 1 + 15
                base_filename = self.sanitize_filename(title, reserve_for_date=truncate_amount)
                filename = f"{base_filename}-{date_suffix}.md"

        return filename

    def get_collection_name(self, collection_uuid: Optional[str]) -> str:
        """Get collection name from config or use UUID."""
        if collection_uuid is None:
            return "uncategorized"

        # Look up in collections mapping
        collections = self.config.get("collections", {})
        mapped_name = collections.get(collection_uuid, collection_uuid)
        
        # Debug output
        if mapped_name != collection_uuid:
            print(f"  Mapped collection: {collection_uuid[:8]}... → {mapped_name}")
        
        return mapped_name

    def format_asset_link(self, asset_path: str) -> str:
        """Format asset link according to configuration."""
        assets_config = self.config.get("assets", {})
        assets_dir = assets_config.get("location", "assets")
        relative_to_markdown = assets_config.get("relative_to_markdown", False)

        if relative_to_markdown:
            # Asset path relative to markdown file
            link_path = f"{assets_dir}/{asset_path}"
        else:
            # Asset path at same level as markdown directories
            link_path = f"../{assets_dir}/{asset_path}"

        # Check wikilinks setting in output section
        output_config = self.config.get("output", {})
        use_wikilinks = output_config.get("wikilinks", False)

        if use_wikilinks:
            return f"![[{link_path}]]"
        else:
            return f"![Asset]({link_path})"

    def format_date(self, iso_datetime: str) -> str:
        """Format ISO datetime string to config-specified format."""
        if not iso_datetime:
            return ""
        
        try:
            dt = datetime.fromisoformat(iso_datetime.replace("Z", "+00:00"))
            date_format = self.config.get("filename", {}).get("date_format", "%Y%m%dT%H%M%S")
            return dt.strftime(date_format)
        except Exception:
            return iso_datetime

    def remove_citation_numbers(self, text: str) -> str:
        """Remove citation numbers like [1], [2][3], etc. from text."""
        # Remove citation patterns: [1], [2], [1][2][3], etc.
        # This pattern matches one or more citation numbers in brackets
        text = re.sub(r'(\[\d+\])+', '', text)
        return text

    def demote_headings(self, content: str) -> str:
        """Demote all markdown headings by one level (add one # to each)."""
        lines = content.split('\n')
        result = []
        
        for line in lines:
            # Check if line starts with heading markdown
            if line.strip().startswith('#'):
                # Count leading #'s
                match = re.match(r'^(#+)\s', line)
                if match:
                    # Remove citation numbers from heading
                    line_without_citations = self.remove_citation_numbers(line)
                    # Add one more # to demote the heading
                    result.append('#' + line_without_citations)
                else:
                    result.append(line)
            else:
                result.append(line)
        
        return '\n'.join(result)

    def create_markdown(self, conversation: dict) -> str:
        """Create markdown content from conversation data."""
        title = conversation.get("context_title", "Untitled")
        created_at = conversation.get("created_at", "")
        mode = conversation.get("mode", "UNKNOWN")

        # Sanitize title for metadata (conservative character set)
        clean_title = self.sanitize_text(title, for_metadata=True)

        # Parse date for metadata
        if created_at:
            dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            date_str = dt.strftime("%Y-%m-%d")
        else:
            date_str = "Unknown"

        # Build markdown content
        lines = [
            "---",
            f"Date: {date_str}",
            f"title: {clean_title}",
            f"export date: {self.export_date}",
            "---",
        ]

        # Add each query-answer pair
        entries = conversation.get("entries", [])
        for entry in entries:
            query = entry.get("query", "")
            answer = entry.get("answer", "")
            entry_mode = entry.get("mode", mode)  # Use conversation mode as fallback
            entry_created_at = entry.get("created_at", "")
            query_status = entry.get("query_status", "COMPLETED")

            # Add query
            lines.append("\n# Query")
            lines.append(query)

            # Check if answer contains level 1 headings
            if answer and re.search(r'^\s*#\s', answer, re.MULTILINE):
                # Demote all headings in the answer (also removes citations from headings)
                answer = self.demote_headings(answer)
            else:
                # Just remove citations from non-heading text
                answer = self.remove_citation_numbers(answer)

            # Format the answer heading
            answer_heading_parts = [f"# Answer ({entry_mode.lower()}"]
            
            # Add date if available
            if entry_created_at:
                formatted_date = self.format_date(entry_created_at)
                answer_heading_parts.append(f" - {formatted_date}")
            
            # Add status if not COMPLETED
            if query_status != "COMPLETED":
                answer_heading_parts.append(f") {query_status}")
            else:
                answer_heading_parts.append(")")
            
            answer_heading = "".join(answer_heading_parts)
            
            lines.append(f"\n{answer_heading}")
            lines.append(answer)

        return "\n".join(lines)

    def log_error(self, conversation_title: str, error: str):
        """Log an error for a failed export."""
        self.errors.append({
            "title": conversation_title,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })

    def write_error_log(self, output_base: Path):
        """Write error log file if there were any errors."""
        if not self.errors:
            return

        error_log_path = output_base / "ERRORS.log"
        with open(error_log_path, "w", encoding="utf-8") as f:
            f.write("Perplexity Export Errors\n")
            f.write("=" * 80 + "\n\n")

            for error_entry in self.errors:
                f.write(f"Timestamp: {error_entry['timestamp']}\n")
                f.write(f"Conversation: {error_entry['title']}\n")
                f.write(f"Error: {error_entry['error']}\n")
                f.write("-" * 80 + "\n\n")

        print(f"\n⚠️  Errors logged to: {error_log_path}")

    def process_json_export(self, json_path: Path, output_base: Path):
        """Process JSON export file and create markdown files."""
        print(f"Loading JSON from: {json_path}")

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error loading JSON: {e}")
            sys.exit(1)

        conversations = data.get("conversations", [])
        print(f"Found {len(conversations)} conversations\n")

        successful = 0
        failed = 0

        # Process each conversation
        for conv in conversations:
            title = conv.get("context_title", "Untitled")
            try:
                # Determine collection directory
                collection_uuid = conv.get("collection_uuid")
                collection_name = self.get_collection_name(collection_uuid)
                collection_dir = output_base / collection_name
                collection_dir.mkdir(parents=True, exist_ok=True)

                # Create unique filename
                created_at = conv.get("created_at", "")
                filename = self.generate_unique_filename(title, created_at, collection_dir)

                # Generate markdown
                markdown_content = self.create_markdown(conv)

                # Write file
                output_path = collection_dir / filename
                output_path.write_text(markdown_content, encoding="utf-8")

                print(f"✓ Created: {output_path}")
                successful += 1

            except Exception as e:
                error_msg = f"{type(e).__name__}: {str(e)}"
                print(f"✗ Failed: {title} - {error_msg}")
                self.log_error(title, error_msg)
                failed += 1
                continue

        # Summary
        print(f"\n{'=' * 80}")
        print(f"Export Summary:")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        print(f"{'=' * 80}")

        # Write error log if there were failures
        if failed > 0:
            self.write_error_log(output_base)

    def run(self, json_path: Path):
        """Run the export process."""
        # Validate input
        if not json_path.exists():
            print(f"JSON file not found: {json_path}")
            sys.exit(1)

        # Create output directory
        output_config = self.config.get("output", {})
        output_base = Path(output_config.get("base_dir", "output"))
        output_base.mkdir(parents=True, exist_ok=True)

        # Process export
        self.process_json_export(json_path, output_base)

        print(f"\nOutput directory: {output_base.absolute()}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Convert Perplexity exports to markdown files"
    )
    parser.add_argument(
        "json_file", type=Path, help="Path to conversations JSON file"
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=Path("config.toml"),
        help="Path to config file (default: config.toml)",
    )

    args = parser.parse_args()

    exporter = PerplexityExporter(config_path=args.config)
    exporter.run(args.json_file)


if __name__ == "__main__":
    main()
