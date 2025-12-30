# pylint: disable=import-error,logging-fstring-interpolation
"""Zotero Deduplication Script"""

import logging
import os
import re
from collections import defaultdict

from dotenv import load_dotenv  # type: ignore
from pyzotero import zotero  # type: ignore
from tqdm import tqdm  # type: ignore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Suppress verbose HTTP logging from httpx (used by pyzotero)
logging.getLogger("httpx").setLevel(logging.WARNING)


def create_signature(item):
    """Create a signature for matching papers"""
    try:
        data = item["data"]

        # Always use title + year for matching (more reliable than DOI which may be missing)
        # This ensures items with and without DOI can still be matched
        title = data.get("title", "").lower().strip()
        if not title:
            # Fallback to key if no title (shouldn't happen for regular items)
            title = item.get("key", "unknown")

        # Normalize title: remove extra whitespace, normalize punctuation
        title = re.sub(r"\s+", " ", title)  # Collapse multiple spaces
        # Normalize punctuation: em dash, en dash, double hyphen to single hyphen
        title = title.replace("—", "-").replace("–", "-").replace("--", "-")
        # Remove trailing punctuation and whitespace
        title = title.strip()

        # Remove common suffixes that cause false mismatches
        # e.g., "for dimension reduction" vs just the base title
        title = re.sub(r"\s+for\s+[a-z\s]+$", "", title, flags=re.IGNORECASE)
        title = re.sub(r":\s*a\s+[a-z\s]+$", "", title, flags=re.IGNORECASE)
        title = title.strip()

        year = data.get("date", "")[:4] if data.get("date") else ""

        logger.debug(f"Using title+year signature: {title[:30]}... ({year})")
        return ("title_year", f"{title}_{year}")
    except Exception as e:
        logger.error(
            f"Error creating signature for item {item.get('key', 'unknown')}: {e}"
        )
        raise


def main():
    """Main function to find and delete duplicate items in Zotero library"""
    # Load environment variables from .env file
    logger.info("Loading environment variables from .env file...")
    load_dotenv()

    # Get API credentials from environment variables
    library_id = os.getenv("ZOTERO_LIBRARY_ID")
    api_key = os.getenv("ZOTERO_API_KEY")

    # Validate that credentials are loaded
    if not library_id or not api_key:
        logger.error("Missing required environment variables!")
        raise ValueError(
            "Missing required environment variables. Please create a .env file with:\n"
            "ZOTERO_LIBRARY_ID=your_library_id\n"
            "ZOTERO_API_KEY=your_api_key\n\n"
            "Get your library ID from: https://www.zotero.org/settings/keys\n"
            "Get your API key from: https://www.zotero.org/settings/keys/new"
        )

    logger.info(f"Credentials loaded successfully. Library ID: {library_id}")

    logger.info("Connecting to Zotero API...")
    zot = zotero.Zotero(library_id, "user", api_key)

    # Get total item count
    logger.info("Getting total item count...")
    total_items = zot.num_items()
    logger.info("Total items in library: %d", total_items)

    # Fetch items in batches with progress bar
    logger.info("Fetching all items from Zotero library...")
    items = []
    limit = 100  # Maximum allowed by Zotero API

    with tqdm(total=total_items, desc="Loading items", unit="items") as pbar:
        for start in range(0, total_items, limit):
            batch = zot.items(limit=limit, start=start)
            items.extend(batch)
            pbar.update(len(batch))

    logger.info("Retrieved %d items from library", len(items))

    # Group potential duplicates
    logger.info("Analyzing items for potential duplicates...")
    duplicates = defaultdict(list)

    for item in tqdm(items, desc="Analyzing items", unit="items"):
        sig = create_signature(item)
        duplicates[sig].append(item)

    logger.info("Created %d unique signatures", len(duplicates))

    # Second pass: Match items with same title but different/missing years
    # Create title-only groups for items that weren't matched
    title_only_groups = defaultdict(list)
    for sig, group in duplicates.items():
        if len(group) == 1:  # Only unmatched items
            item = group[0]
            title = item.get("data", {}).get("title", "").lower().strip()
            if title:
                # Normalize title same way as signature
                title = re.sub(r"\s+", " ", title)
                # Normalize punctuation: em dash, en dash, double hyphen to single hyphen
                title = title.replace("—", "-").replace("–", "-").replace("--", "-")
                title = re.sub(r"\s+for\s+[a-z\s]+$", "", title, flags=re.IGNORECASE)
                title = re.sub(r":\s*a\s+[a-z\s]+$", "", title, flags=re.IGNORECASE)
                title = title.strip()
                if title:
                    title_only_groups[title].append(item)

    # Merge title-only groups that have multiple items (same title, different years)
    additional_dups = 0
    for title, group in title_only_groups.items():
        if len(group) > 1:
            additional_dups += 1
            # Add to duplicates dict with a title-only signature
            title_sig = ("title_only", title)
            duplicates[title_sig] = group
            logger.debug(
                "Found %d items with same title but different years: %s",
                len(group),
                title[:50],
            )

    if additional_dups > 0:
        logger.info(
            "Found %d additional duplicate groups by matching titles without years",
            additional_dups,
        )

    # Stage 1: Find duplicate groups and prepare deletion list
    logger.info("\n=== STAGE 1: Identifying Duplicates ===")
    duplicate_groups = []
    items_to_delete = []

    for sig, group in duplicates.items():
        if len(group) > 1:
            # Keep the most complete record
            best = max(group, key=lambda x: len(str(x["data"])))

            # Mark others for deletion
            to_delete_in_group = []
            for item in group:
                if item["key"] != best["key"]:
                    to_delete_in_group.append(item)
                    items_to_delete.append(item)

            duplicate_groups.append(
                {
                    "signature": sig,
                    "total": len(group),
                    "keep": best,
                    "delete": to_delete_in_group,
                }
            )

            logger.info("Found %d duplicates for: %s", len(group), sig)

    # Display summary and ask for confirmation
    separator = "=" * 60
    print(f"\n{separator}")
    print("DUPLICATE ANALYSIS COMPLETE")
    print(f"{separator}")
    print(f"Total items scanned: {len(items)}")
    print(f"Duplicate groups found: {len(duplicate_groups)}")
    print(f"Items to be deleted: {len(items_to_delete)} of {len(items)}")
    print(f"{separator}\n")

    if len(items_to_delete) == 0:
        logger.info("No duplicates found. Nothing to delete.")
        return

    # Show first 5 items to be deleted
    print("First 5 items that will be DELETED:\n")
    for idx, item in enumerate(items_to_delete[:5], 1):
        title = item["data"].get("title", "N/A")
        item_type = item["data"].get("itemType", "unknown")
        print(f"{idx}. [{item_type}] {title[:70]}")
        print(f"   Key: {item['key']}")
        if item["data"].get("DOI"):
            print(f"   DOI: {item['data']['DOI']}")
        print()

    if len(items_to_delete) > 5:
        print(f"... and {len(items_to_delete) - 5} more items\n")

    # Ask for confirmation
    print(f"{separator}")
    response = (
        input(f"Delete {len(items_to_delete)} duplicate items? (yes/no): ")
        .strip()
        .lower()
    )

    if response not in ["yes", "y"]:
        logger.info("Deletion cancelled by user.")
        print("No items were deleted.")
        return

    # Stage 2: Perform deletions
    logger.info("\n=== STAGE 2: Deleting Duplicates ===")
    total_deleted = 0

    for item in tqdm(items_to_delete, desc="Deleting duplicates", unit="items"):
        try:
            # Refresh item to get latest version before deletion (fixes version conflicts)
            try:
                fresh_item = zot.item(item["key"])
                if fresh_item:
                    item = fresh_item
            except Exception:
                # Item might already be deleted, skip
                logger.warning("Item %s not found, may already be deleted", item["key"])
                continue

            zot.delete_item(item)
            total_deleted += 1
            logger.debug(
                "Deleted: %s - %s", item["key"], item["data"].get("title", "N/A")[:50]
            )
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to delete item %s: %s", item["key"], e)

    # Final summary
    print(f"\n{separator}")
    print("DELETION COMPLETE")
    print(f"{separator}")
    print(f"Total items deleted: {total_deleted}")
    print(f"Duplicate groups resolved: {len(duplicate_groups)}")
    print(f"{separator}")


if __name__ == "__main__":
    main()
