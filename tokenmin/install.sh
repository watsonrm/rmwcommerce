#!/usr/bin/env bash
# Tokenmin installer.
#
# Most users — public audit copy of the scanner:
#   curl --proto '=https' --tlsv1.2 -fsSL https://tokenmin.ai/install.sh | bash
#
# F&F preview (no gh, no brew, no setup) — your sponsor sends you a unique URL:
#   curl --proto '=https' --tlsv1.2 -fsSL https://tokenmin.ai/ff/<your-code>/install.sh | bash
#
# Audit-first install — verify the script before executing:
#   curl --proto '=https' --tlsv1.2 -fsSL -o install.sh https://tokenmin.ai/install.sh
#   curl --proto '=https' --tlsv1.2 -fsSL -o install.sh.sha256 https://tokenmin.ai/install.sh.sha256
#   shasum -a 256 -c install.sh.sha256
#   less install.sh
#   bash install.sh
#
# Configuration env vars:
#   TOKENMIN_TOKEN          fine-grained PAT for watsonrm/tokenmin (F&F)
#   TOKENMIN_FF             1=force F&F install path; 0=force public-scanner-only
#   TOKENMIN_HOME           install dir          (default $HOME/.tokenmin)
#   TOKENMIN_BIN_DIR        PATH symlink dir     (default $HOME/.local/bin)
#   TOKENMIN_NO_PATH_PATCH=1  skip the shell-rc autopatch prompt
#   TOKENMIN_QUIET=1        suppress non-error output

set -euo pipefail

TOKEN="${TOKENMIN_TOKEN:-}"
FF_REQUESTED="${TOKENMIN_FF:-}"
DEST="${TOKENMIN_HOME:-$HOME/.tokenmin}"
BIN_DIR="${TOKENMIN_BIN_DIR:-$HOME/.local/bin}"
NO_PATCH="${TOKENMIN_NO_PATH_PATCH:-0}"
QUIET="${TOKENMIN_QUIET:-0}"

PUBLIC_REPO="watsonrm/tokenmin-scanner"
FF_REPO="watsonrm/tokenmin"

# ---- output helpers --------------------------------------------------------
say()  { [ "${QUIET}" = "1" ] || printf "tokenmin: %s\n" "$*" >&2; }
ok()   { [ "${QUIET}" = "1" ] || printf "tokenmin: \033[32m\xE2\x9C\x93\033[0m %s\n" "$*" >&2; }
warn() { printf "tokenmin: \033[33m!\033[0m %s\n" "$*" >&2; }
die()  { printf "tokenmin: \033[31merror\033[0m %s\n" "$*" >&2; exit 1; }

# ---- input validation ------------------------------------------------------
# Refuse weird install paths (defense against malicious shell rc setting
# TOKENMIN_HOME=/etc/cron.d).
case "${DEST}" in
  "$HOME"/*|/usr/local/*|/opt/*) ;;
  *) die "refusing install path ${DEST} (must be under \$HOME, /usr/local, or /opt)";;
esac
case "${BIN_DIR}" in
  "$HOME"/*|/usr/local/*|/opt/*) ;;
  *) die "refusing symlink dir ${BIN_DIR} (must be under \$HOME, /usr/local, or /opt)";;
esac

# ---- prerequisites ---------------------------------------------------------
command -v python3 >/dev/null 2>&1 || die "python3 is required (3.10+).
  macOS:  brew install python   (or download from python.org)
  Linux:  sudo apt install python3   (or 'sudo dnf install python3')"
command -v git >/dev/null 2>&1 || die "git is required.
  macOS:  xcode-select --install   (or 'brew install git')
  Linux:  sudo apt install git"

PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
case "${PY_VERSION}" in
  3.1[0-9]|3.[2-9][0-9]) ;;
  *) die "python3 ${PY_VERSION} is too old; need 3.10+";;
esac

# ---- decide which repo -----------------------------------------------------
if [ -n "${TOKEN}" ] || [ "${FF_REQUESTED}" = "1" ]; then
  REPO="${FF_REPO}"
  KIND="F&F bundle (private)"
  if [ -z "${TOKEN}" ]; then
    # F&F requested but no token — fall back to gh CLI
    if ! command -v gh >/dev/null 2>&1; then
      die "F&F install requires either TOKENMIN_TOKEN env var (recommended) or gh CLI.
  ask your sponsor for a tokenmin.ai/ff/... invite URL (it embeds the token),
  or install gh: https://cli.github.com/ then 'gh auth login'"
    fi
    gh auth status >/dev/null 2>&1 || die "you are not signed in to gh. run: gh auth login"
    if ! gh api "repos/${REPO}" >/dev/null 2>&1; then
      die "you don't have F&F access to ${REPO} yet. ask your sponsor for an invite URL,
  or install the public scanner instead:
    TOKENMIN_FF=0 curl --proto '=https' --tlsv1.2 -fsSL https://tokenmin.ai/install.sh | bash"
    fi
  fi
elif [ "${FF_REQUESTED}" = "0" ]; then
  REPO="${PUBLIC_REPO}"
  KIND="public scanner (Apache-2.0)"
else
  REPO="${PUBLIC_REPO}"
  KIND="public scanner (Apache-2.0)"
fi

# ---- clone or update -------------------------------------------------------
if [ -d "${DEST}/.git" ]; then
  current_remote=$(git -C "${DEST}" remote get-url origin 2>/dev/null || echo "")
  if [[ "${current_remote}" != *"${REPO}"* ]]; then
    die "existing install at ${DEST} points at a different repo:
    ${current_remote}
  remove it or set TOKENMIN_HOME=<new path> and retry."
  fi
  say "updating existing install at ${DEST}"
  before=$(git -C "${DEST}" rev-parse HEAD 2>/dev/null || echo "")
  git -C "${DEST}" fetch --quiet origin 2>/dev/null || die "fetch failed (offline?)"
  git -C "${DEST}" pull --ff-only --quiet 2>/dev/null || warn "pull failed (local changes?)"
  after=$(git -C "${DEST}" rev-parse HEAD 2>/dev/null || echo "")
  if [ "${before}" = "${after}" ]; then
    ok "already up to date (${after:0:7})"
  else
    ok "updated ${before:0:7} -> ${after:0:7}"
  fi
else
  say "cloning ${REPO} into ${DEST}"
  if [ -n "${TOKEN}" ]; then
    # Embed token transiently for the clone, then rewrite remote to clean URL.
    if ! git clone --quiet "https://x-access-token:${TOKEN}@github.com/${REPO}.git" "${DEST}" 2>/dev/null; then
      die "clone failed. the token may have expired or been revoked.
  ask your sponsor for a fresh invite URL."
    fi
    # Don't leave the token in .git/config — overwrite the remote URL.
    git -C "${DEST}" remote set-url origin "https://github.com/${REPO}.git"
  else
    git clone --quiet "https://github.com/${REPO}.git" "${DEST}" \
      || die "clone failed (network?)."
  fi
  ok "${KIND} installed at ${DEST}"
fi

chmod +x "${DEST}/tokenmin"

# ---- symlink with conflict detection ---------------------------------------
mkdir -p "${BIN_DIR}"
link="${BIN_DIR}/tokenmin"
if [ -L "${link}" ]; then
  current_target=$(readlink "${link}")
  expected="${DEST}/tokenmin"
  if [ "${current_target}" != "${expected}" ]; then
    warn "${link} -> ${current_target} (not us)"
    if [ -t 0 ] && [ -t 2 ]; then
      printf "tokenmin: overwrite? [y/N] " >&2
      read -r ans < /dev/tty || ans=""
      case "${ans}" in y|Y|yes|YES) ;; *) die "aborted; existing symlink left alone";; esac
    else
      die "non-interactive; remove ${link} manually or set TOKENMIN_BIN_DIR to another path"
    fi
  fi
elif [ -e "${link}" ]; then
  die "${link} exists and is not a symlink we own.
  remove it or set TOKENMIN_BIN_DIR=<different-path>"
fi
ln -sf "${DEST}/tokenmin" "${link}"
ok "symlinked ${link}"

# ---- PATH check + autopatch -----------------------------------------------
patched=0
on_path=0
case ":${PATH}:" in
  *":${BIN_DIR}:"*) on_path=1;;
esac

if [ "${on_path}" = "1" ]; then
  ok "${BIN_DIR} is on PATH"
elif [ "${NO_PATCH}" = "1" ]; then
  warn "${BIN_DIR} is not on PATH (TOKENMIN_NO_PATH_PATCH=1)"
else
  # Detect shell + rc file.
  shell_name=$(basename "${SHELL:-/bin/bash}")
  rc=""
  case "${shell_name}" in
    bash) [ -f "$HOME/.bashrc" ] && rc="$HOME/.bashrc" || rc="$HOME/.bash_profile";;
    zsh)  rc="$HOME/.zshrc";;
    fish) rc="$HOME/.config/fish/config.fish";;
    *) rc="";;
  esac

  if [ -n "${rc}" ]; then
    if [ "${shell_name}" = "fish" ]; then
      line="set -gx PATH ${BIN_DIR} \$PATH"
    else
      line="export PATH=\"${BIN_DIR}:\$PATH\""
    fi

    if [ -f "${rc}" ] && grep -qF "${BIN_DIR}" "${rc}" 2>/dev/null; then
      ok "${BIN_DIR} already referenced in ${rc}"
    elif [ -t 0 ] && [ -t 2 ]; then
      printf "\ntokenmin: %s is not on PATH.\n" "${BIN_DIR}" >&2
      printf "tokenmin: append to %s?\n" "${rc}" >&2
      printf "  > %s\n" "${line}" >&2
      printf "tokenmin: [y/N] " >&2
      read -r ans < /dev/tty || ans=""
      case "${ans}" in
        y|Y|yes|YES)
          mkdir -p "$(dirname "${rc}")"
          printf "\n# Added by tokenmin installer on %s\n%s\n" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "${line}" >> "${rc}"
          ok "appended to ${rc} — restart your shell or 'source ${rc}'"
          patched=1
          ;;
        *) warn "skipped. add manually: ${line}";;
      esac
    else
      warn "non-interactive; add manually to ${rc}:"
      warn "  ${line}"
    fi
  else
    warn "couldn't detect your shell rc; add to your shell config:"
    warn "  export PATH=\"${BIN_DIR}:\$PATH\""
  fi
fi

# ---- post-install: detect Claude Code presence ----------------------------
if [ -d "$HOME/.claude" ]; then
  ok "found ~/.claude — ready for 'tokenmin --source code'"
else
  warn "no ~/.claude on this machine."
  say "  if you use Claude Code:    install it first (https://claude.com/code)"
  say "  if you use claude.ai or Claude Desktop:"
  say "    export your chats, then run:"
  say "      tokenmin --source export --from path/to/export.zip --out report.md"
fi

# ---- greet -----------------------------------------------------------------
say ""
ok "tokenmin ${KIND} installed."
if [ "${KIND}" = "F&F bundle (private)" ]; then
  say "  tokenmin --version              what you have"
  say "  tokenmin doctor                 self-diagnose"
  say "  tokenmin --selfcheck            see the anonymizer rules"
  say "  tokenmin --days 7 --out report.md   full report"
else
  say "  tokenmin --version              what you have"
  say "  tokenmin doctor                 self-diagnose"
  say "  tokenmin --selfcheck            see the anonymizer rules"
  say "  tokenmin --days 7 --snapshot snap.json  audit what would be sent"
  say ""
  say "this is the public scanner — no engine. for the full report,"
  say "ask Rick for an F&F invite URL."
fi
if [ "${patched}" = "1" ]; then
  say ""
  say "(restart your shell or 'source ${rc}' to pick up PATH)"
fi
