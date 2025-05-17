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
    def styled_prompt(question, default=""):
        """Custom prompt function that keeps styling consistent"""
        console.print(f"[bold]QUESTION:[/bold] {question}", end="")
        response = input(" ") or default
        return response

    token = load_token()
    if not token:
        console.print("[bold red]No token found. Please authenticate first.[/bold red]")
        return

    try:
        token_data = get_token_data(token)
        user_id = token_data.user_id

        # Create a styled heading for the entry creation process
        console.print("\n[bold blue]━━━ CREATE NEW ENTRY ━━━[/bold blue]\n")

        # Stylized prompt for content using our custom function
        content = styled_prompt("What's on your mind?")
        console.print(f"[dim italic]You wrote: {content}[/dim italic]\n")

        # Stylized section for entry types
        console.print("[bold magenta]SELECT ENTRY TYPE[/bold magenta]")
        for i, entry_type in enumerate(EntryType):
            style = "bold cyan" if i == 0 else "cyan"  # Highlight default option
            console.print(f"  [{style}]{i + 1}[/{style}]. {entry_type.value}")

        entry_type_idx = styled_prompt("Select entry type (number)", "1")
        try:
            entry_type = list(EntryType)[int(entry_type_idx) - 1]
            console.print(f"[dim italic]Selected: {entry_type.value}[/dim italic]\n")
        except (ValueError, IndexError):
            entry_type = EntryType.HIGHLIGHT
            console.print(
                f"[yellow]Invalid selection, using default: {entry_type.value}[/yellow]\n"
            )

        # Stylized section for moods
        console.print("[bold magenta]SELECT MOOD[/bold magenta]")
        for i, mood in enumerate(Mood):
            style = "bold cyan" if i == 0 else "cyan"  # Highlight default option
            console.print(f"  [{style}]{i + 1}[/{style}]. {mood.value}")

        mood_idx = styled_prompt("Select mood (number)", "1")
        try:
            mood = list(Mood)[int(mood_idx) - 1]
            console.print(f"[dim italic]Selected: {mood.value}[/dim italic]\n")
        except (ValueError, IndexError):
            mood = Mood.NEUTRAL
            console.print(
                f"[yellow]Invalid selection, using default: {mood.value}[/yellow]\n"
            )

        # Stylized section for tags
        console.print("[bold magenta]ADD TAGS[/bold magenta]")
        tag_input = styled_prompt("Enter tags (comma-separated)", "")

        tag_names = [t.strip() for t in tag_input.split(",") if t.strip()]
        if tag_names:
            console.print(
                f"[dim italic]Tags entered: {', '.join(tag_names)}[/dim italic]\n"
            )
        else:
            console.print("[dim italic]No tags entered[/dim italic]\n")

        with console.status(
            "[bold green]Processing entry...[/bold green]", spinner="dots"
        ) as status:
            tag_ids = []

            for tag_name in tag_names:
                existing_tags = tag_db.find_by("name", tag_name)
                existing_tags = [t for t in existing_tags if str(t.user_id) == user_id]

                if existing_tags:
                    tag_ids.append(existing_tags[0].id)
                elif tag_name:
                    new_tag = tag_db.create(
                        Tag(name=tag_name, user_id=PyObjectId(user_id))
                    )
                    console.print(
                        f"[green]✓[/green] Created new tag: [bold cyan]{tag_name}[/bold cyan]"
                    )
                    tag_ids.append(new_tag.id)

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


        # Show a beautiful summary of the created entry
        console.print("\n[bold green]✅ ENTRY CREATED SUCCESSFULLY![/bold green]")

        # Format the entry nicely
        gitmojis_str = (
            " ".join([emoji.value for emoji in created_entry.gitmojis])
            if created_entry.gitmojis
            else ""
        )
        formatted_content = (
            f"{gitmojis_str} {created_entry.content}"
            if gitmojis_str
            else created_entry.content
        )

        tag_names = []
        for tag_id in created_entry.tags:
            tag = tag_db.get(tag_id)
            if tag:
                tag_names.append(tag.name)
        tags_str = ", ".join(tag_names) if tag_names else "no tags"

        # Determine sentiment color and label
        sentiment_score = created_entry.sentiment_score
        if sentiment_score > 0.5:
            sentiment_color = "bright_green"
            sentiment_label = "Very Positive"
        elif sentiment_score > 0.1:
            sentiment_color = "green"
            sentiment_label = "Positive"
        elif sentiment_score > -0.1:
            sentiment_color = "white"
            sentiment_label = "Neutral"
        elif sentiment_score > -0.5:
            sentiment_color = "red"
            sentiment_label = "Negative"
        else:
            sentiment_color = "bright_red"
            sentiment_label = "Very Negative"

        # Display the entry in a nicely formatted panel
        from rich.panel import Panel
        from rich.text import Text

        content_text = Text(formatted_content)
        panel_content = Text()
        panel_content.append(content_text)
        panel_content.append("\n\n")
        panel_content.append("Type: ", style="dim")
        panel_content.append(created_entry.entry_type.value, style="bold blue")
        panel_content.append(" | Mood: ", style="dim")
        panel_content.append(created_entry.mood.value, style="bold yellow")
        panel_content.append("\nTags: ", style="dim")
        panel_content.append(tags_str, style="bold cyan")
        panel_content.append("\nSentiment: ", style="dim")
        panel_content.append(
            f"{sentiment_label} ({sentiment_score:.2f})",
            style=f"bold {sentiment_color}",
        )
        panel_content.append("\nCreated: ", style="dim")
        panel_content.append(
            created_entry.created_at.strftime("%Y-%m-%d %H:%M:%S"), style="italic"
        )

        console.print(
            Panel(
                panel_content,
                title="[bold]New Entry Summary[/bold]",
                border_style="blue",
                padding=(1, 2),
            )
        )

    except Exception as e:
        console.print(f"\n[bold red]ERROR:[/bold red] {str(e)}")
        import traceback

        console.print("[dim]" + traceback.format_exc() + "[/dim]")

if __name__ == "__main__":
    app()