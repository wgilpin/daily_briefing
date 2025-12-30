"""CLI interface for Zotero API Digest."""

import argparse
import sys

from src.utils.config import Configuration, load_configuration
from src.zotero import AuthenticationError, ZoteroConnectionError
from src.zotero.client import create_zotero_client, fetch_recent_items
from src.zotero.filters import filter_by_keywords, sort_and_limit_items
from src.zotero.formatter import generate_digest, write_digest


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Generate a markdown digest of recent Zotero library additions.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Generate digest with defaults (last 24h, digest.md)
  %(prog)s --days 7                 # Generate digest for last 7 days
  %(prog)s --output custom.md        # Save to custom.md
  %(prog)s --include "AI" "ML"      # Include only items with "AI" or "ML"
  %(prog)s --exclude "review"        # Exclude items containing "review"
  
Get your Zotero API credentials from: https://www.zotero.org/settings/keys
        """,
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default="digest.md",
        help="Output file path for the markdown digest (default: digest.md)",
    )
    
    parser.add_argument(
        "--days",
        type=int,
        default=1,
        help="Number of days to look back for recent additions (default: 1)",
    )
    
    parser.add_argument(
        "--include",
        nargs="+",
        default=[],
        help="Keywords to include (items must contain at least one keyword in title, abstract, or tags)",
    )
    
    parser.add_argument(
        "--exclude",
        nargs="+",
        default=[],
        help="Keywords to exclude (items containing these keywords will be omitted)",
    )
    
    return parser.parse_args()


def merge_cli_args_with_config(config: Configuration, args: argparse.Namespace) -> Configuration:
    """
    Merge CLI arguments with configuration from environment.
    
    Args:
        config: Configuration loaded from environment
        args: Parsed CLI arguments
        
    Returns:
        Updated Configuration with CLI args merged
    """
    # Create new configuration with CLI args overriding defaults
    return Configuration(
        library_id=config.library_id,
        api_key=config.api_key,
        output_path=args.output,
        days=args.days,
        include_keywords=args.include if args.include else [],
        exclude_keywords=args.exclude if args.exclude else [],
    )


def main() -> int:
    """
    Main entry point for the CLI application.
    
    Orchestrates the workflow: fetch → filter → sort → format → write
    
    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        # Parse CLI arguments
        args = parse_arguments()
        
        # Load configuration from environment
        config = load_configuration()
        
        # Merge CLI args with config
        config = merge_cli_args_with_config(config, args)
        
        # Create Zotero client
        client = create_zotero_client(config.library_id, config.api_key)
        
        # Fetch recent items
        print(f"Fetching items added in the last {config.days} day(s)...")
        items = fetch_recent_items(client, config.days)
        print(f"Found {len(items)} item(s)")
        
        if not items:
            print(f"No items found in the last {config.days} day(s).")
            return 0
        
        # Apply keyword filtering if specified (before sorting)
        if config.include_keywords or config.exclude_keywords:
            items = filter_by_keywords(
                items,
                include=config.include_keywords,
                exclude=config.exclude_keywords,
            )
            print(f"After keyword filtering: {len(items)} item(s)")
        
        # Sort and limit to 10 most recently published
        items = sort_and_limit_items(items, limit=10)
        print(f"Processing {len(items)} item(s) for digest")
        
        # Generate markdown digest
        digest_content = generate_digest(items, config.days)
        
        # Write to file
        write_digest(digest_content, config.output_path)
        print(f"Digest written to: {config.output_path}")
        
        return 0
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return 130
    except (AuthenticationError, ZoteroConnectionError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

