import platform

import click

from globus_search_cli.config import (
    SEARCH_AT_EXPIRES_OPTNAME,
    SEARCH_AT_OPTNAME,
    SEARCH_RT_OPTNAME,
    internal_auth_client,
    lookup_option,
    write_option,
)
from globus_search_cli.printing import safeprint

SEARCH_ALL_SCOPE = "urn:globus:auth:scope:search.api.globus.org:all"


_SHARED_EPILOG = """\

Logout of the Globus Search CLI with
  globus-search logout
"""

_LOGIN_EPILOG = (
    (
        u"""\

You have successfully logged in to the Globus Search CLI
"""
    )
    + _SHARED_EPILOG
)

_LOGGED_IN_RESPONSE = (
    (
        """\
You are already logged in!

You may force a new login with
  globus-search login --force
"""
    )
    + _SHARED_EPILOG
)


def _check_logged_in():
    search_rt = lookup_option(SEARCH_RT_OPTNAME)
    if search_rt is None:
        return False
    native_client = internal_auth_client()
    res = native_client.oauth2_validate_token(search_rt)
    return res["active"]


def _revoke_current_tokens(native_client):
    for token_opt in (SEARCH_RT_OPTNAME, SEARCH_AT_OPTNAME):
        token = lookup_option(token_opt)
        if token:
            native_client.aotuh2_revoke_token(token)


def _store_config(token_response):
    tkn = token_response.by_resource_server

    search_at = tkn["search.api.globus.org"]["access_token"]
    search_rt = tkn["search.api.globus.org"]["refresh_token"]
    search_at_expires = tkn["search.api.globus.org"]["expires_at_seconds"]

    write_option(SEARCH_RT_OPTNAME, search_rt)
    write_option(SEARCH_AT_OPTNAME, search_at)
    write_option(SEARCH_AT_EXPIRES_OPTNAME, search_at_expires)

    safeprint(_LOGIN_EPILOG)


def _do_login_flow():
    # get the NativeApp client object
    native_client = internal_auth_client()

    label = platform.node() or None
    native_client.oauth2_start_flow(
        requested_scopes=SEARCH_ALL_SCOPE,
        refresh_tokens=True,
        prefill_named_grant=label,
    )
    linkprompt = "Please log into Globus here"
    safeprint(
        "{0}:\n{1}\n{2}\n{1}\n".format(
            linkprompt, "-" * len(linkprompt), native_client.oauth2_get_authorize_url()
        )
    )
    auth_code = click.prompt("Enter the resulting Authorization Code here").strip()
    tkn = native_client.oauth2_exchange_code_for_tokens(auth_code)
    _revoke_current_tokens(native_client)
    _store_config(tkn)


@click.command(
    "login",
    short_help=("Log into Globus to get credentials for " "the Globus Search CLI"),
    help=(
        "Get credentials for the Globus Search CLI. "
        "Necessary before any 'globus-search' commands which "
        "require authentication will work"
    ),
)
@click.option(
    "--force", is_flag=True, help="Do a fresh login, ignoring any existing credentials"
)
def login_command(force):
    # if not forcing, stop if user already logged in
    if not force and _check_logged_in():
        safeprint(_LOGGED_IN_RESPONSE)
        return

    _do_login_flow()
