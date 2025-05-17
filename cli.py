import typer
from core.auth import get_token_data
from core.logger import logger
from core.db import user_db, changelog_db
from core.utils import save_token, load_token
from models import PyObjectId

app = typer.Typer()


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
def log():
    """
    Get the changelog entries for the current user. Works like "git log".

    Returns
    -------
    None
    """

    token = load_token()
    if not token:
        print("No token found. Please authenticate first.")
        return
    try:
        token_data = get_token_data(token)
        print(token_data)
        user_entries = changelog_db.find_by("user_id", PyObjectId(token_data.user_id))
        print(user_entries)


    except Exception as e:
        print("Bad:",e)




if __name__ == "__main__":
    app()