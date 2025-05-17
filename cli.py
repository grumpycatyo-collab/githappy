import typer
from core.auth import get_token_data
from core.logger import logger
from core.db import user_db, changelog_db, tag_db
from core.utils import save_token, load_token
from core.sentiment import enrich_entry
from models import PyObjectId, ChangelogEntry, EntryType, Mood, Tag
from bson import ObjectId
from rich.text import Text
from rich.console import Console
from rich.align import Align
from rich.padding import Padding
from rich import print
from typing import Optional
from datetime import datetime

app = typer.Typer()
console = Console()


@app.command()
def auth(bearer: str = None) -> None:
    """
    Authenticate a user with a bearer token.

    Parameters
    ----------
    bearer : str, optional
        Bearer token for authentication (default is None)

    Returns
    -------
    None
    """
    if bearer:
        try:
            token_data = get_token_data(bearer)

            message = Text()
            message.append("✅ Authentication successful\n", style="bold green")
            message.append("User: ", style="dim")
            message.append(token_data.username, style="bold")
            message.append(" | Role: ", style="dim")
            message.append(token_data.role, style="blue")
            console.print(message)
            save_token(bearer)
        except Exception as e:
            error_message = Text()
            error_message.append("❌ Authentication failed\n", style="bold red")
            error_message.append(str(e))

            console.print(error_message)
    else:
        error_message = Text()
        error_message.append("⚠️ No token provided\n", style="bold yellow")
        error_message.append("Please provide a bearer token to authenticate")
        console.print(error_message)

@app.command()
def log(
    json: bool = False,
    tags: Optional[list[str]] = typer.Option(
        None, "--tag", "-t", help="Filter by tag names"
    ),
    limit: int = typer.Option(
        10, "--limit", "-l", help="Limit number of entries to show"
    ),
) -> None:
    """
    Get the changelog entries for the current user. Works like "git log".

    Parameters
    ----------
    json : bool, optional
        Whether to output in JSON format (default is False)
    tags : list[str], optional
        Filter by tag names
    limit : int, optional
        Limit number of entries to show (default is 10)
    Returns
    -------
    None
    """
    token = load_token()
    if not token:
        console.print("[bold red]No token found. Please authenticate first.[/bold red]")
        return

    try:
        token_data = get_token_data(token)
        user_id = ObjectId(token_data.user_id)

        user_entries = changelog_db.find_by("user_id", user_id)
        user_entries = sorted(user_entries, key=lambda x: x.created_at, reverse=True)

        if not user_entries:
            console.print("[yellow]No changelog entries found.[/yellow]")
            return


        if tags:
            tag_ids = []
            for tag_name in tags:
                tag_entries = list(tag_db.find_by("name", tag_name))
                if tag_entries:
                    tag_ids.append(tag_entries[0].id)

            if tag_ids:
                user_entries = [
                    entry
                    for entry in user_entries
                    if any(tag_id in entry.tags for tag_id in tag_ids)
                ]

        if limit:
            user_entries = user_entries[:limit]

        if json:
            print(user_entries)
        else:
            # First calculate the maximum width for each column
            max_content_width = 0
            max_tags_width = 0
            date_width = 19  # Fixed width for date format "YYYY-MM-DD HH:MM"

            for entry in user_entries:
                gitmojis_str = (
                    " ".join([emoji.value for emoji in entry.gitmojis])
                    if entry.gitmojis
                    else ""
                )
                content_with_emoji = (
                    f"{gitmojis_str} {entry.content}" if gitmojis_str else entry.content
                )

                tag_names = [
                    tag_db.get(tag_id).name
                    for tag_id in entry.tags
                    if tag_db.get(tag_id)
                ]
                tags_str = ", ".join(tag_names) if tag_names else "no tags"

                max_content_width = max(max_content_width, len(content_with_emoji))
                max_tags_width = max(max_tags_width, len(tags_str))

            # Calculate total width for the separator line
            total_width = (
                max_content_width + max_tags_width + date_width + 6
            )  # Adding padding between columns

            # Get username for the header
            user = user_db.get(user_id)
            username = user.username if user else "User"

            # Add header with username and count of entries
            console.print("=" * total_width)
            header = Text()
            header.append("CHANGELOG FOR ", style="white")
            header.append(username, style="bold magenta")
            header.append(f" ({len(user_entries)} entries)", style="dim")
            console.print(header)
            console.print("=" * total_width)

            # Add column headers
            column_header = Text()
            column_header.append(f"{'DATE':<{date_width}} | ", style="bold")
            column_header.append(f"{'TAGS':<{max_tags_width}} | ", style="bold")
            column_header.append("MESSAGE", style="bold")
            console.print(column_header)
            console.print("─" * total_width)

            # Display entries in a formatted table-like structure
            for entry in user_entries:
                date_str = entry.created_at.strftime("%Y-%m-%d %H:%M")

                tag_names = []
                for tag_id in entry.tags:
                    tag = tag_db.get(tag_id)
                    if tag:
                        tag_names.append(tag.name)

                tags_str = ", ".join(tag_names) if tag_names else "no tags"

                gitmojis_str = (
                    " ".join([emoji.value for emoji in entry.gitmojis])
                    if entry.gitmojis
                    else ""
                )
                content = entry.content

                # Create a row with columns
                row = Text()

                # Date column
                row.append(f"{date_str:<{date_width}} | ", style="dim")

                # Tags column with highlighting
                tags_styled = Text()
                tags_styled.append(tags_str, style="bold cyan")
                row.append(tags_styled)
                row.append(" " * (max_tags_width - len(tags_str)) + " | ")

                # Content column with sentiment-based styling
                content_part = Text()
                if gitmojis_str:
                    content_part.append(f"{gitmojis_str} ")

                if entry.sentiment_score > 0.3:
                    content_part.append(content, style="green")
                elif entry.sentiment_score < -0.3:
                    content_part.append(content, style="red")
                else:
                    content_part.append(content)

                row.append(content_part)

                console.print(row)
                console.print("─" * total_width)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")


@app.command()
def write() -> None:
    """
    Write a new changelog entry.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    token = load_token()
    if not token:
        console.print("[bold red]No token found. Please authenticate first.[/bold red]")
        return

    try:
        token_data = get_token_data(token)
        user_id = token_data.user_id

        content = typer.prompt("What's on your mind?")

        console.print("\nEntry types:")
        for i, entry_type in enumerate(EntryType):
            console.print(f"  {i + 1}. {entry_type.value}")

        entry_type_idx = typer.prompt("Select entry type (number)", default="1")
        try:
            entry_type = list(EntryType)[int(entry_type_idx) - 1]
        except (ValueError, IndexError):
            entry_type = EntryType.HIGHLIGHT
            console.print(
                f"[yellow]Invalid selection, using default: {entry_type.value}[/yellow]"
            )

        # Display mood options
        console.print("\nMoods:")
        for i, mood in enumerate(Mood):
            console.print(f"  {i + 1}. {mood.value}")

        # Get mood selection
        mood_idx = typer.prompt("Select mood (number)", default="1")
        try:
            mood = list(Mood)[int(mood_idx) - 1]
        except (ValueError, IndexError):
            mood = Mood.NEUTRAL
            console.print(
                f"[yellow]Invalid selection, using default: {mood.value}[/yellow]"
            )

        tag_input = typer.prompt("Enter tags (comma-separated)", default="")

        tag_names = [t.strip() for t in tag_input.split(",") if t.strip()]
        tag_ids = []

        for tag_name in tag_names:
            existing_tags = tag_db.find_by("name", tag_name)
            existing_tags = [t for t in existing_tags if str(t.user_id) == user_id]

            if existing_tags:
                tag_ids.append(existing_tags[0].id)
            elif tag_name:
                new_tag = tag_db.create(Tag(name=tag_name, user_id=PyObjectId(user_id)))
                tag_ids.append(new_tag.id)
                console.print(f"[green]Created new tag:[/green] {tag_name}")

        entry = ChangelogEntry(
            user_id=PyObjectId(user_id),
            content=content,
            entry_type=entry_type,
            mood=mood,
            tags=tag_ids,
            week_number=datetime.now().isocalendar()[1],
        )

        entry = enrich_entry(entry)

        created_entry = changelog_db.create(entry)

        console.print("\n[bold green]✅ Entry created successfully![/bold green]")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")


if __name__ == "__main__":
    app()