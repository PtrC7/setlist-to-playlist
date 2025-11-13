import os, secrets, json
from flask import Blueprint, current_app, session, redirect, request, url_for, make_response
import spotipy
from spotipy.oauth2 import SpotifyOAuth

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

def _oauth():
    return SpotifyOAuth(
        client_id=current_app.config["SPOTIFY_CLIENT_ID"],
        client_secret=current_app.config["SPOTIFY_CLIENT_SECRET"],
        redirect_uri=current_app.config["SPOTIFY_REDIRECT_URI"],
        scope="playlist-modify-public playlist-modify-private user-read-email",
        cache_path=None,
        show_dialog=True,   
        open_browser=False 
    )

@auth_bp.route("/login")
def login():
    state = secrets.token_urlsafe(16)
    session["spotify_oauth_state"] = state
    auth_url = _oauth().get_authorize_url(state=state)
    return redirect(auth_url)

@auth_bp.route("/callback")
def callback():
    code = request.args.get("code")
    state = request.args.get("state")

    if not code or not state or state != session.get("spotify_oauth_state"):
        return _close_popup(success=False, message="Invalid OAuth state.")

    oauth = _oauth()
    token_info = oauth.get_access_token(code=code, as_dict=True)

    session["spotify_token"] = {
        "access_token": token_info["access_token"],
        "refresh_token": token_info.get("refresh_token"),
        "expires_at": token_info["expires_at"],
        "scope": token_info.get("scope"),
        "token_type": token_info.get("token_type"),
    }

    sp = spotipy.Spotify(auth=token_info["access_token"])
    me = sp.me()
    session["spotify_user"] = {"id": me["id"], "name": me.get("display_name") or me["id"]}

    print("Authenticated Spotify user (callback):", me["id"], me.get("display_name"))

    return _close_popup(success=True, payload={"user": session["spotify_user"]})


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.pop("spotify_token", None)
    session.pop("spotify_user", None)
    session.pop("spotify_oauth_state", None)
    return {"success": True}


@auth_bp.route("/me")
def me():
    """Frontend can poll this to know if a user is logged in."""
    if "spotify_token" not in session or "spotify_user" not in session:
        return {"authenticated": False}
    return {
        "authenticated": True,
        "user": session.get("spotify_user"),
    }


def _close_popup(success=True, payload=None, message=None):
    data = {"success": success}
    if payload: data.update(payload)
    if message: data["message"] = message
    html = f"""
    <html><body>
    <script>
      (function() {{
        if (window.opener) {{
          window.opener.postMessage({json.dumps(data)}, "*");
        }}
        window.close();
      }})();
    </script>
    Success. You can close this window.
    </body></html>
    """
    resp = make_response(html)
    resp.headers["Content-Type"] = "text/html"
    return resp