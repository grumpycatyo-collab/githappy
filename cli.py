import typer
from core.auth import get_token_data
from core.logger import logger
from core.db import user_db, changelog_db, tag_db
from core.utils import save_token, load_token
from models import PyObjectId
from bson import ObjectId
from rich.text import Text
from rich.console import Console
from rich.align import Align
from rich.padding import Padding
from rich import print
from typing import Optional

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
            max_message_width = 0
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

                date_str = entry.created_at.strftime("%Y-%m-%d %H:%M")

                max_message_width = max(
                    max_message_width,
                    len(content_with_emoji),
                    len(tags_str),
                    len(date_str),
                )

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

                message = Text()

                message.append(f"{tags_str:<{max_message_width}}\n", style="dim")

                content_part = Text()
                if gitmojis_str:
                    content_part.append(f"{gitmojis_str} ")

                if entry.sentiment_score > 0.3:
                    content_part.append(entry.content, style="green")
                elif entry.sentiment_score < -0.3:
                    content_part.append(entry.content, style="red")
                else:
                    content_part.append(entry.content)

                message.append(content_part)

                message.append(f"\n{date_str:<{max_message_width}}", style="dim")

                console.print(message)

                console.print("─" * max_message_width)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")


if __name__ == "__main__":
    app()