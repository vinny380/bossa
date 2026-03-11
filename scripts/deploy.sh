#!/bin/bash
# Build and upload bossa-memory to PyPI.
# On first run, prompts for your PyPI API token and saves it to .pypi-token (gitignored).

set -e
cd "$(dirname "$0")/.."

TOKEN_FILE=".pypi-token"

if [[ ! -f "$TOKEN_FILE" ]]; then
  echo "PyPI API token not found. Create one at https://pypi.org/manage/account/token/"
  echo -n "Enter your API token: "
  read -r token
  echo "$token" > "$TOKEN_FILE"
  chmod 600 "$TOKEN_FILE"
  echo "Token saved to $TOKEN_FILE"
fi

echo "=== Building package ==="
rm -rf dist/
python -m pip install build twine -q
python -m build

echo "=== Uploading to PyPI ==="
# First non-empty line, trim newlines (token must be pypi-...)
TOKEN=$(grep -v '^[[:space:]]*$' "$TOKEN_FILE" | head -1 | tr -d '\n\r')
if [[ -z "$TOKEN" ]]; then
  echo "ERROR: Token file is empty or invalid. Delete it and run again:"
  echo "  rm $TOKEN_FILE"
  echo "  ./scripts/deploy.sh"
  exit 1
fi
TWINE_USERNAME=__token__ TWINE_PASSWORD="$TOKEN" python -m twine upload dist/*

echo "Done."
