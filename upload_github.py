"""Sube el proyecto TAVOGYM a GitHub usando la API (sin git instalado)."""
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
IGNORE = {".env", "database.db", ".tools", "__pycache__", ".git"}

TEXT_EXTENSIONS = {
    ".py", ".txt", ".md", ".html", ".css", ".js", ".json", ".yaml", ".yml",
    ".bat", ".example", ".gitignore",
}


def collect_files():
    files = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        parts = rel.parts
        if any(p in IGNORE for p in parts):
            continue
        if path.name in IGNORE:
            continue
        files.append(path)
    return sorted(files)


def api_request(url, token, method="GET", data=None):
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "tavogym-uploader",
    }
    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def main():
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not token:
        print("ERROR: Falta GITHUB_TOKEN")
        print("Creá un token en: https://github.com/settings/tokens")
        print("Permiso necesario: repo")
        sys.exit(1)

    repo_name = os.environ.get("GITHUB_REPO", "tavogym")

    user = api_request("https://api.github.com/user", token)
    owner = user["login"]
    print(f"Usuario GitHub: {owner}")

    repo_url = f"https://api.github.com/repos/{owner}/{repo_name}"
    try:
        api_request(repo_url, token)
        print(f"Repo existente: {owner}/{repo_name}")
    except urllib.error.HTTPError as exc:
        if exc.code != 404:
            raise
        api_request(
            "https://api.github.com/user/repos",
            token,
            method="POST",
            data={"name": repo_name, "description": "TAVOGYM - App gym de barrio", "private": False},
        )
        print(f"Repo creado: {owner}/{repo_name}")

    files = collect_files()
    print(f"Subiendo {len(files)} archivos...")

    for index, path in enumerate(files, 1):
        rel = path.relative_to(ROOT).as_posix()
        content_bytes = path.read_bytes()
        if path.suffix.lower() in TEXT_EXTENSIONS or path.suffix == "":
            content_b64 = base64.b64encode(content_bytes).decode()
        else:
            content_b64 = base64.b64encode(content_bytes).decode()

        payload = {
            "message": f"Add {rel}" if index == 1 else f"Update {rel}",
            "content": content_b64,
        }

        file_url = f"{repo_url}/contents/{rel}"
        try:
            existing = api_request(file_url, token)
            payload["sha"] = existing["sha"]
            payload["message"] = f"Update {rel}"
        except urllib.error.HTTPError as exc:
            if exc.code != 404:
                raise

        api_request(file_url, token, method="PUT", data=payload)
        print(f"  [{index}/{len(files)}] {rel}")

    print()
    print("Listo!")
    print(f"https://github.com/{owner}/{repo_name}")


if __name__ == "__main__":
    main()
