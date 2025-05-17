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
            print(f"Authenticated user: {token_data.username} with role: {token_data.role}")
            save_token(bearer)
        except Exception as e:
            print("Bad:", e)
    else:
        print("No token provided.")



@app.command()
def log(json: bool = False) -> None:
    """
    Get the changelog entries for the current user. Works like "git log".

    Parameters
    ----------
    json : bool, optional
        Whether to output in JSON format (default is False)

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

        if json:
            import json
            from datetime import datetime

            class CustomEncoder(json.JSONEncoder):
                def default(self, obj):
                    if isinstance(obj, ObjectId):
                        return str(obj)
                    if isinstance(obj, datetime):
                        return obj.isoformat()
                    if hasattr(obj, "__dict__"):
                        return obj.__dict__
                    return super().default(obj)

            print(json.dumps(user_entries, cls=CustomEncoder, indent=2))
        else:
            content_width = 70

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

                message.append(f"{tags_str}\n", style="dim")

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

                message.append(f"\n{date_str}", style="dim")

                console.print(message)

                console.print("─" * 100)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")


if __name__ == "__main__":
    app()