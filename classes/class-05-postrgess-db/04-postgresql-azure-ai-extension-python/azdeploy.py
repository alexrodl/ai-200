# =============================================================================
# Change the values of these variables as needed.
# =============================================================================

rg = "ai-200-postgres-04"  # Resource Group name
location = "centralus"       # Azure region for the resource group and Foundry (models)

# =============================================================================
# DON'T CHANGE ANYTHING BELOW THIS LINE.
# =============================================================================

import hashlib
import json
import os
import secrets
import shutil
import string
import subprocess
import sys
import time
from pathlib import Path

DB_NAME = "postgres"
FIREWALL_RULE_NAME = "AllowAll"
REQUIRED_EXTENSIONS = ("azure_ai", "vector")

# Foundry model deployments: (deployment name, model name, version, capacity in K TPM)
EMBEDDING_MODEL = ("text-embedding-3-small", "text-embedding-3-small", "1", 120)
CHAT_MODEL = ("gpt-4.1-mini", "gpt-4.1-mini", "2025-04-14", 100)

os.environ.setdefault("AZURE_CORE_ONLY_SHOW_ERRORS", "true")

_EXE_CACHE: dict[str, str] = {}


def _throwaway_admin_password() -> str:
    # Password auth is disabled after creation, so this value is never used.
    # It only satisfies the CLI's create-time validation.
    safe_symbols = "_.@#"
    chars = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
        secrets.choice(safe_symbols),
        *[secrets.choice(string.ascii_letters + string.digits + safe_symbols) for _ in range(28)],
    ]
    secrets.SystemRandom().shuffle(chars)
    return "".join(chars)


def _resolve_exe(name: str) -> str:
    cached = _EXE_CACHE.get(name)
    if cached:
        return cached
    resolved = shutil.which(name)
    if not resolved:
        print(f"Error: '{name}' not found on PATH. Install it and retry.")
        sys.exit(1)
    _EXE_CACHE[name] = resolved
    return resolved


def run_quiet(description: str, argv: list[str], max_attempts: int = 1) -> bool:
    """Run a command, optionally retrying transient 'busy' responses."""
    argv = [_resolve_exe(argv[0]), *argv[1:]]
    for attempt in range(1, max_attempts + 1):
        result = subprocess.run(argv, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            return True
        combined = (result.stdout or "") + (result.stderr or "")
        if "ServerIsBusy" not in combined or attempt == max_attempts:
            print(f"Error: {description} failed (exit code {result.returncode}).")
            if combined.strip():
                print(combined.rstrip())
            return False
        delay = min(5 * (2 ** (attempt - 1)), 60)
        print(f"Server is busy. Retrying {description.lower()} in {delay} seconds...")
        time.sleep(delay)
    return False


def az_query(argv: list[str]) -> str:
    argv = [_resolve_exe(argv[0]), *argv[1:]]
    result = subprocess.run(argv, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return ""
    return (result.stdout or "").strip()


def clear_screen() -> None:
    if os.system("cls" if os.name == "nt" else "clear") != 0:
        sys.stdout.write("\x1b[2J\x1b[3J\x1b[H")
        sys.stdout.flush()


def pause() -> None:
    try:
        input("Press Enter to continue...")
    except EOFError:
        print()


def write_env_files(env_vars: dict[str, str], directory: str = ".") -> None:
    """Write .env (bash) and .env.ps1 (PowerShell) side by side."""
    target_dir = Path(directory)

    def bash_escape(value: str) -> str:
        return value.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$").replace("`", "\\`")

    def ps_escape(value: str) -> str:
        return value.replace("`", "``").replace('"', '`"').replace("$", "`$")

    with open(target_dir / ".env", "w", encoding="utf-8", newline="\n") as f:
        f.writelines(f'export {k}="{bash_escape(v)}"\n' for k, v in env_vars.items())
    with open(target_dir / ".env.ps1", "w", encoding="utf-8", newline="\n") as f:
        f.writelines(f'$env:{k} = "{ps_escape(v)}"\n' for k, v in env_vars.items())


def require_az_login() -> str:
    user_object_id = az_query(["az", "ad", "signed-in-user", "show", "--query", "id", "-o", "tsv"])
    if not user_object_id:
        print("Error: Not authenticated with Azure. Please run: az login")
        sys.exit(1)
    return user_object_id


def derived_names(user_object_id: str) -> tuple[str, str]:
    user_hash = hashlib.sha1(user_object_id.encode("utf-8")).hexdigest()[:8]
    return f"psql-azureai-{user_hash}", f"foundry-azureai-{user_hash}"


def create_resource_group() -> bool:
    print(f"Checking/creating resource group '{rg}'...")
    if az_query(["az", "group", "exists", "--name", rg]) == "false":
        if not run_quiet("Create resource group",
                         ["az", "group", "create", "--name", rg, "--location", location]):
            return False
        print(f"Resource group created: {rg}")
    else:
        print(f"Resource group already exists: {rg}")
    return True


# -----------------------------------------------------------------------------
# PostgreSQL Flexible Server
# -----------------------------------------------------------------------------

def server_state(server_name: str) -> str:
    """Return the server state ('' if it doesn't exist) using an ARM read."""
    return az_query([
        "az", "resource", "show", "--resource-group", rg, "--name", server_name,
        "--resource-type", "Microsoft.DBforPostgreSQL/flexibleServers",
        "--query", "properties.state", "-o", "tsv",
    ])


def wait_for_ready(server_name: str, timeout_seconds: int = 900, poll_seconds: int = 15) -> bool:
    deadline = time.monotonic() + timeout_seconds
    last_state = ""
    while time.monotonic() < deadline:
        state = server_state(server_name)
        if state == "Ready":
            return True
        if state in ("Failed", "Canceled"):
            print(f"Error: PostgreSQL server entered the {state} state.")
            return False
        if state and state != last_state:
            print(f"  Server state: {state} (waiting...)")
            last_state = state
        time.sleep(poll_seconds)
    print(f"Error: Timed out waiting for server '{server_name}' to become Ready.")
    return False


def create_postgres_server(server_name: str, user_object_id: str) -> bool:
    if not create_resource_group():
        return False
    print()

    if server_state(server_name):
        print(f"PostgreSQL server '{server_name}' already exists. Skipping creation.")
    else:
        print(f"Creating Azure Database for PostgreSQL Flexible Server '{server_name}'...")
        print("This may take several minutes...")
        if not run_quiet("Create PostgreSQL Flexible Server", [
            "az", "postgres", "flexible-server", "create",
            "--resource-group", rg, "--name", server_name, "--location", location,
            "--sku-name", "Standard_B1ms", "--tier", "Burstable",
            "--storage-size", "32", "--version", "16",
            "--public-access", "Enabled",
            "--microsoft-entra-auth", "Enabled", "--password-auth", "Enabled",
            "--admin-user", "pgadmin", "--admin-password", _throwaway_admin_password(),
            "--yes",
        ]):
            return False
    if not wait_for_ready(server_name):
        return False

    user_upn = az_query(["az", "ad", "signed-in-user", "show",
                         "--query", "userPrincipalName", "-o", "tsv"])
    if not user_upn:
        print("Error: Unable to retrieve signed-in user information.")
        return False

    print("Configuring Microsoft Entra administrator...")
    if not run_quiet("Configure Microsoft Entra administrator", [
        "az", "postgres", "flexible-server", "microsoft-entra-admin", "create",
        "--resource-group", rg, "--server-name", server_name,
        "--display-name", user_upn, "--object-id", user_object_id, "--type", "User",
    ], max_attempts=6) or not wait_for_ready(server_name):
        return False

    print("Disabling password authentication...")
    if not run_quiet("Disable password authentication", [
        "az", "postgres", "flexible-server", "update",
        "--resource-group", rg, "--name", server_name,
        "--microsoft-entra-auth", "Enabled", "--password-auth", "Disabled", "--yes",
    ], max_attempts=6) or not wait_for_ready(server_name):
        return False

    print("Creating firewall rule...")
    if not run_quiet("Create PostgreSQL firewall rule", [
        "az", "postgres", "flexible-server", "firewall-rule", "create",
        "--resource-group", rg, "--server-name", server_name, "--name", FIREWALL_RULE_NAME,
        "--start-ip-address", "0.0.0.0", "--end-ip-address", "255.255.255.255",
    ], max_attempts=6) or not wait_for_ready(server_name):
        return False

    print("PostgreSQL server created successfully.")
    return True


def configure_extensions(server_name: str) -> bool:
    """Add azure_ai and vector to the server's extension allow-list (azure.extensions)."""
    print("Configuring the extension allow-list (azure.extensions)...")
    state = server_state(server_name)
    if not state:
        print(f"Error: PostgreSQL server '{server_name}' not found. Run option 1 first.")
        return False
    if state != "Ready" and not wait_for_ready(server_name):
        return False

    current = az_query([
        "az", "postgres", "flexible-server", "parameter", "show",
        "--resource-group", rg, "--server-name", server_name,
        "--name", "azure.extensions", "--query", "value", "-o", "tsv",
    ])
    allowed = {item.strip().lower() for item in current.split(",") if item.strip()}
    if all(ext in allowed for ext in REQUIRED_EXTENSIONS):
        print("azure_ai and vector are already allow-listed. No changes needed.")
        return True

    allowed.update(REQUIRED_EXTENSIONS)
    value = ",".join(sorted(ext.upper() for ext in allowed))
    print(f"Setting azure.extensions = {value}")
    if not run_quiet("Allow-list extensions", [
        "az", "postgres", "flexible-server", "parameter", "set",
        "--resource-group", rg, "--server-name", server_name,
        "--name", "azure.extensions", "--value", value,
    ], max_attempts=6) or not wait_for_ready(server_name):
        return False
    print("Extensions allow-listed and server is ready.")
    return True


# -----------------------------------------------------------------------------
# Microsoft Foundry (AIServices) resource + model deployments
# -----------------------------------------------------------------------------

def foundry_exists(foundry_name: str) -> bool:
    return bool(az_query([
        "az", "cognitiveservices", "account", "show",
        "--resource-group", rg, "--name", foundry_name, "--query", "id", "-o", "tsv",
    ]))


def deploy_model(foundry_name: str, model: tuple[str, str, str, int]) -> bool:
    deployment, model_name, version, capacity = model
    existing = az_query([
        "az", "cognitiveservices", "account", "deployment", "list",
        "--resource-group", rg, "--name", foundry_name, "--query", "[].name", "-o", "tsv",
    ]).splitlines()
    if deployment in existing:
        print(f"  Deployment '{deployment}' already exists.")
        return True
    print(f"  Deploying model '{model_name}' ({version}) as '{deployment}'...")
    return run_quiet(f"Deploy {model_name}", [
        "az", "cognitiveservices", "account", "deployment", "create",
        "--resource-group", rg, "--name", foundry_name,
        "--deployment-name", deployment, "--model-name", model_name,
        "--model-version", version, "--model-format", "OpenAI",
        "--sku-name", "GlobalStandard", "--sku-capacity", str(capacity),
    ])


def create_foundry(foundry_name: str) -> bool:
    if not create_resource_group():
        return False
    print()
    if foundry_exists(foundry_name):
        print(f"Foundry resource '{foundry_name}' already exists.")
    else:
        print(f"Creating Microsoft Foundry resource '{foundry_name}' (kind AIServices)...")
        if not run_quiet("Create Foundry resource", [
            "az", "cognitiveservices", "account", "create",
            "--resource-group", rg, "--name", foundry_name, "--location", location,
            "--kind", "AIServices", "--sku", "S0",
            "--custom-domain", foundry_name, "--yes",
        ]):
            return False
        print("Foundry resource created.")

    print("Deploying models...")
    if not deploy_model(foundry_name, EMBEDDING_MODEL) or not deploy_model(foundry_name, CHAT_MODEL):
        return False
    print("Foundry resource and model deployments are ready.")
    return True


# -----------------------------------------------------------------------------
# Status and connection info
# -----------------------------------------------------------------------------

def check_deployment_status(server_name: str, foundry_name: str) -> bool:
    print(f"PostgreSQL Server ({server_name}):")
    state = server_state(server_name)
    print(f"  Status: {state or 'Not created'}")
    if state:
        allowed = az_query([
            "az", "postgres", "flexible-server", "parameter", "show",
            "--resource-group", rg, "--server-name", server_name,
            "--name", "azure.extensions", "--query", "value", "-o", "tsv",
        ])
        print(f"  azure.extensions: {allowed or '(empty)'}")

    print()
    print(f"Foundry resource ({foundry_name}):")
    if not foundry_exists(foundry_name):
        print("  Status: Not created")
        return True
    deployments = az_query([
        "az", "cognitiveservices", "account", "deployment", "list",
        "--resource-group", rg, "--name", foundry_name,
        "--query", "[].[name, properties.provisioningState]", "-o", "tsv",
    ])
    print("  Deployments:")
    for line in deployments.splitlines() or ["(none)"]:
        print(f"    {line}")
    return True


def retrieve_connection_info(server_name: str, foundry_name: str) -> bool:
    print("Retrieving connection information...")
    if server_state(server_name) != "Ready":
        print(f"Error: PostgreSQL server '{server_name}' is not Ready. Use option 4 to check.")
        return False
    if not foundry_exists(foundry_name):
        print(f"Error: Foundry resource '{foundry_name}' not found. Run option 2 first.")
        return False

    user_upn = az_query(["az", "ad", "signed-in-user", "show",
                         "--query", "userPrincipalName", "-o", "tsv"])
    access_token = az_query(["az", "account", "get-access-token", "--resource-type", "oss-rdbms",
                             "--query", "accessToken", "-o", "tsv"])
    ai_key = az_query(["az", "cognitiveservices", "account", "keys", "list",
                       "--resource-group", rg, "--name", foundry_name, "--query", "key1", "-o", "tsv"])
    if not user_upn or not access_token or not ai_key:
        print("Error: Unable to retrieve user, access token, or Foundry key.")
        return False

    env = {
        "DB_HOST": f"{server_name}.postgres.database.azure.com",
        "DB_NAME": DB_NAME,
        "DB_USER": user_upn,
        "PGPASSWORD": access_token,
        # The azure_ai extension calls these endpoints FROM the PostgreSQL server.
        "AZURE_OPENAI_ENDPOINT": f"https://{foundry_name}.openai.azure.com/",
        "AZURE_LANGUAGE_ENDPOINT": f"https://{foundry_name}.cognitiveservices.azure.com/",
        "AZURE_AI_KEY": ai_key,
        "EMBEDDING_DEPLOYMENT": EMBEDDING_MODEL[0],
        "CHAT_DEPLOYMENT": CHAT_MODEL[0],
    }
    write_env_files(env)
    print()
    print("Connection information")
    print("===========================================================")
    for key, value in env.items():
        shown = "(hidden)" if key in ("PGPASSWORD", "AZURE_AI_KEY") else value
        print(f"{key}: {shown}")
    print()
    print("Environment variables saved to .env and .env.ps1 (both are git-ignored).")
    return True


def show_menu(server_name: str, foundry_name: str) -> None:
    clear_screen()
    print("=====================================================================")
    print("    PostgreSQL + azure_ai extension Deployment Menu")
    print("=====================================================================")
    print(f"Resource Group: {rg}")
    print(f"PostgreSQL Server: {server_name}")
    print(f"Foundry resource: {foundry_name}")
    print(f"Location: Foundry={location}, PostgreSQL={location}")
    print("=====================================================================")
    print("1. Create PostgreSQL server with Entra authentication")
    print("2. Create Foundry resource and deploy models")
    print("3. Allow-list the azure_ai and vector extensions")
    print("4. Check deployment status")
    print("5. Retrieve connection info, access token, and Foundry key")
    print("6. Exit")
    print("=====================================================================")


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    if not (script_dir / "client").is_dir():
        print("Error: 'client/' folder is missing next to azdeploy.py.")
        sys.exit(1)
    os.chdir(script_dir)

    user_object_id = require_az_login()
    server_name, foundry_name = derived_names(user_object_id)

    actions = {
        "1": lambda: create_postgres_server(server_name, user_object_id),
        "2": lambda: create_foundry(foundry_name),
        "3": lambda: configure_extensions(server_name),
        "4": lambda: check_deployment_status(server_name, foundry_name),
        "5": lambda: retrieve_connection_info(server_name, foundry_name),
    }
    while True:
        show_menu(server_name, foundry_name)
        choice = input("Please select an option (1-6): ").strip()
        if choice == "6":
            clear_screen()
            sys.exit(0)
        clear_screen()
        print()
        if choice in actions:
            actions[choice]()
        else:
            print("Invalid option. Please select 1-6.")
        print()
        pause()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        sys.exit(130)
