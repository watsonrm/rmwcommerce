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
  # If a TOKEN was provided and this install doesn't yet have a credential
  # helper, plant one now so the fetch (and subsequent auto-updates from
  # the wrapper) can authenticate against the private repo.
  if [ -n "${TOKEN}" ] && [ ! -f "${DEST}/.git-credentials" ]; then
    cred_file="${DEST}/.git-credentials"
    printf "https://x-access-token:%s@github.com\n" "${TOKEN}" > "${cred_file}"
    chmod 600 "${cred_file}"
    git -C "${DEST}" config --local credential.helper "store --file=${cred_file}"
  fi
  before=$(git -C "${DEST}" rev-parse HEAD 2>/dev/null || echo "")
  git -C "${DEST}" fetch --quiet origin 2>/dev/null || die "fetch failed (offline? auth?). if F&F: rerun the install URL to refresh credentials."
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
    # Don't leave the token in .git/config (would surface in screenshots /
    # `git config --list`). Instead, write to a per-install credential helper
    # file (chmod 0600) and point this repo's git config at it. The token
    # then stays usable for auto-update without being human-visible during
    # routine repo inspection.
    git -C "${DEST}" remote set-url origin "https://github.com/${REPO}.git"
    cred_file="${DEST}/.git-credentials"
    printf "https://x-access-token:%s@github.com\n" "${TOKEN}" > "${cred_file}"
    chmod 600 "${cred_file}"
    git -C "${DEST}" config --local credential.helper "store --file=${cred_file}"
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

# ---- telemetry: F&F default on, public scanner asks on first run ----------
# F&F users accept the "free for anonymized data" bargain via their invite —
# extending that to anonymous usage stats is a natural fit. Pre-seed the
# settings.json so they skip the first-run consent ask.
#
# If the per-user installer also carries TOKENMIN_TELEMETRY_ENDPOINT (and,
# for github:// transport, TOKENMIN_TELEMETRY_GITHUB_TOKEN), bake those into
# settings.json too so events transmit. The PATs stay file-local (chmod 0600)
# and never reach .git/config or git history.
if [ "${KIND}" = "F&F bundle (private)" ]; then
  settings_dir="${HOME}/.tokenmin"
  mkdir -p "${settings_dir}"
  settings_file="${settings_dir}/settings.json"
  if [ ! -f "${settings_file}" ]; then
    python3 - "${TOKENMIN_TELEMETRY_ENDPOINT:-}" "${TOKENMIN_TELEMETRY_GITHUB_TOKEN:-}" <<'PY'
import json, os, sys
endpoint, gh_token = sys.argv[1] or None, sys.argv[2] or None
settings = {
    "telemetry": "on",
    "telemetry_consent_asked": True,
    "telemetry_endpoint": endpoint,
}
if gh_token:
    settings["telemetry_github_token"] = gh_token
path = os.path.expanduser("~/.tokenmin/settings.json")
with open(path, "w") as f:
    json.dump(settings, f, indent=2, sort_keys=True)
os.chmod(path, 0o600)
PY
    chmod 600 "${settings_file}"
    if [ -n "${TOKENMIN_TELEMETRY_ENDPOINT:-}" ]; then
      ok "telemetry enabled + endpoint configured (transmitting to ${TOKENMIN_TELEMETRY_ENDPOINT})"
    else
      ok "telemetry enabled (no endpoint configured — events form but don't transmit)"
    fi
    say "  disable anytime: tokenmin telemetry off"
    say "  inspect what's sent: tokenmin telemetry dry-run"
  fi
fi

# ---- multi-Claude detection -----------------------------------------------
# Tokenmin supports every Claude variant: Code (native), Desktop (via export),
# claude.ai web (via export). Detect what's installed and tell the user what
# they can do without making them figure it out.

CLAUDE_CODE_DIR="$HOME/.claude"
case "$(uname -s 2>/dev/null)" in
  Darwin)  CLAUDE_DESKTOP_DIR="$HOME/Library/Application Support/Claude" ;;
  Linux)   CLAUDE_DESKTOP_DIR="$HOME/.config/Claude" ;;
  MINGW*|CYGWIN*|MSYS*) CLAUDE_DESKTOP_DIR="${APPDATA:-$HOME/AppData/Roaming}/Claude" ;;
  *)       CLAUDE_DESKTOP_DIR="" ;;
esac

found_code=0
found_desktop=0
say ""
say "Claude variants on this machine:"

if [ -d "${CLAUDE_CODE_DIR}" ]; then
  n_sess=0
  if [ -d "${CLAUDE_CODE_DIR}/projects" ]; then
    n_sess=$(find "${CLAUDE_CODE_DIR}/projects" -name '*.jsonl' -type f 2>/dev/null | wc -l | tr -d ' ')
  fi
  ok "Claude Code        ${CLAUDE_CODE_DIR} (${n_sess} session files)"
  found_code=1
else
  say "  Claude Code        not found at ${CLAUDE_CODE_DIR}"
fi

if [ -n "${CLAUDE_DESKTOP_DIR}" ] && [ -d "${CLAUDE_DESKTOP_DIR}" ]; then
  ok "Claude Desktop     ${CLAUDE_DESKTOP_DIR}"
  found_desktop=1
else
  if [ -n "${CLAUDE_DESKTOP_DIR}" ]; then
    say "  Claude Desktop     not found at ${CLAUDE_DESKTOP_DIR}"
  fi
fi

if [ "${found_code}" = "0" ] && [ "${found_desktop}" = "0" ]; then
  warn "no Claude install detected on this machine."
  say "  Claude Code:    https://claude.com/code"
  say "  Claude Desktop: https://claude.ai/download"
  say "  claude.ai web:  no install \xE2\x80\x94 export chats then use --source export"
fi

# ---- greet -----------------------------------------------------------------
say ""
ok "tokenmin ${KIND} installed."
say "  tokenmin --version              what you have"
say "  tokenmin doctor                 self-diagnose"
say "  tokenmin --selfcheck            see the anonymizer rules"

if [ "${KIND}" = "F&F bundle (private)" ]; then
  RUN="--out report.md"
  RUN_DESCRIPTION="full report"
else
  RUN="--snapshot snap.json"
  RUN_DESCRIPTION="audit what would be sent"
fi

if [ "${found_code}" = "1" ]; then
  say ""
  say "Claude Code (the easy one — reads your sessions directly):"
  say "  tokenmin --days 7 ${RUN}   # ${RUN_DESCRIPTION}"
fi

if [ "${found_desktop}" = "1" ]; then
  say ""
  say "Claude Desktop (live native parser still in progress; use export today):"
  say "  tokenmin help-export                 walk through the export, with a deep-link"
  say "  tokenmin --source export --watch-downloads   auto-run when the export arrives"
  say "  tokenmin demo                        see what a report looks like first"
fi

if [ "${found_code}" = "0" ] && [ "${found_desktop}" = "0" ]; then
  say ""
  say "Once you've used a Claude product on this machine, return and run:"
  say "  tokenmin --days 7 ${RUN}"
  say ""
  say "If you use claude.ai (web) only:"
  say "  tokenmin help-export                 step-by-step export instructions"
  say "  tokenmin demo                        see what a report looks like first"
fi

if [ "${KIND}" != "F&F bundle (private)" ]; then
  say ""
  say "(this is the public scanner — no engine. for the full report, ask Rick"
  say " for an F&F invite URL.)"
fi
if [ "${patched}" = "1" ]; then
  say ""
  say "(restart your shell or 'source ${rc}' to pick up PATH)"
fi
