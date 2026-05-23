#!/usr/bin/env bash
# Tokenmin friends-and-family installer.
#
#   curl -fsSL https://watsonrm.github.io/rmwcommerce/tokenmin/install.sh | bash
#   # or
#   curl -fsSL https://raw.githubusercontent.com/watsonrm/rmwcommerce/main/tokenmin/install.sh | bash
#
# The F&F repo (watsonrm/tokenmin) is PRIVATE. You need to be added before
# this works — ping Rick.
#
# What this does, in order:
#   1. Confirm gh + python3 are installed and gh is authenticated.
#   2. Confirm you have access to watsonrm/tokenmin (otherwise stop early).
#   3. Clone to $TOKENMIN_HOME (default ~/.tokenmin) or fast-forward update.
#   4. Symlink $TOKENMIN_BIN_DIR/tokenmin (default ~/.local/bin/tokenmin).
#   5. Print PATH guidance + smoke-test instructions.
#
# Override anything with env vars before running:
#   TOKENMIN_HOME=/opt/tokenmin TOKENMIN_BIN_DIR=/usr/local/bin curl ... | bash

set -euo pipefail

REPO="watsonrm/tokenmin"
DEST="${TOKENMIN_HOME:-$HOME/.tokenmin}"
BIN_DIR="${TOKENMIN_BIN_DIR:-$HOME/.local/bin}"

say()  { printf "tokenmin-install: %s\n" "$*" >&2; }
ok()   { printf "tokenmin-install: \033[32m\xE2\x9C\x93\033[0m %s\n" "$*" >&2; }
die()  { printf "tokenmin-install: \033[31merror\033[0m %s\n" "$*" >&2; exit 1; }

command -v gh >/dev/null 2>&1 \
  || die "the GitHub CLI ('gh') is required. install: https://cli.github.com/"
command -v python3 >/dev/null 2>&1 \
  || die "python3 is required (3.10+)."
gh auth status >/dev/null 2>&1 \
  || die "you are not signed in to gh. run: gh auth login"

# Access check before doing anything else — friendly message instead of a clone failure.
if ! gh api "repos/${REPO}" >/dev/null 2>&1; then
  die "you don't have access to ${REPO} yet. ask Rick to add you to the F&F preview."
fi
ok "access to ${REPO} confirmed"

if [ -d "${DEST}/.git" ]; then
  say "updating existing install at ${DEST}"
  git -C "${DEST}" fetch --quiet origin
  git -C "${DEST}" pull --ff-only --quiet
else
  say "cloning ${REPO} into ${DEST}"
  gh repo clone "${REPO}" "${DEST}" -- --quiet
fi
ok "tokenmin is at ${DEST}"

chmod +x "${DEST}/tokenmin"
mkdir -p "${BIN_DIR}"
ln -sf "${DEST}/tokenmin" "${BIN_DIR}/tokenmin"
ok "symlinked ${BIN_DIR}/tokenmin -> ${DEST}/tokenmin"

case ":${PATH}:" in
  *":${BIN_DIR}:"*)
    ok "${BIN_DIR} is already on PATH"
    ;;
  *)
    say ""
    say "${BIN_DIR} is NOT on PATH. add this to your shell rc:"
    say "    export PATH=\"${BIN_DIR}:\$PATH\""
    say ""
    say "or run tokenmin directly: ${DEST}/tokenmin --help"
    ;;
esac

say ""
ok "installed. try it:"
say "    tokenmin --days 7 --out report.md"
say ""
say "see ${DEST}/README.md for what gets collected, how it's anonymized,"
say "and the F&F bargain (free for anonymized data)."
