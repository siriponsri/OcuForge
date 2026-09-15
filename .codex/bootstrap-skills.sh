#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_ROOT="$SCRIPT_DIR/skills"
LICENSE_ROOT="$SCRIPT_DIR/THIRD_PARTY_LICENSES"

mkdir -p "$SKILLS_ROOT" "$LICENSE_ROOT"

command -v git >/dev/null 2>&1 || {
  echo "git is required to bootstrap OcuForge Codex skills." >&2
  exit 1
}

install_repo_skills() {
  local name="$1"
  local repo="$2"
  local ref="$3"
  shift 3

  local tmp
  tmp="$(mktemp -d "${TMPDIR:-/tmp}/ocuforge-codex.XXXXXX")"
  trap 'rm -rf "$tmp"' RETURN

  git clone --quiet --filter=blob:none --sparse --no-checkout "$repo" "$tmp"

  local paths=()
  local pair src dest
  for pair in "$@"; do
    src="${pair%%=*}"
    paths+=("$src")
  done

  git -C "$tmp" sparse-checkout set "${paths[@]}"
  git -C "$tmp" checkout --quiet "$ref"

  for pair in "$@"; do
    src="${pair%%=*}"
    dest="${pair#*=}"
    rm -rf "$SKILLS_ROOT/$dest"
    cp -R "$tmp/$src" "$SKILLS_ROOT/$dest"
    test -f "$SKILLS_ROOT/$dest/SKILL.md" || {
      echo "Installed skill '$dest' is missing SKILL.md." >&2
      exit 1
    }
  done

  if [[ -f "$tmp/LICENSE" ]]; then
    cp "$tmp/LICENSE" "$LICENSE_ROOT/$name.txt"
  fi

  rm -rf "$tmp"
  trap - RETURN
}

install_repo_skills \
  "andrej-karpathy-skills" \
  "https://github.com/multica-ai/andrej-karpathy-skills.git" \
  "2c606141936f1eeef17fa3043a72095b4765b9c2" \
  "skills/karpathy-guidelines=karpathy-guidelines"

install_repo_skills \
  "debug-skill" \
  "https://github.com/AlmogBaku/debug-skill.git" \
  "26ef325fe2188209d053f42a6ca0000942a94932" \
  "skills/debugging-code=debugging-code"

install_repo_skills \
  "mattpocock-skills" \
  "https://github.com/mattpocock/skills.git" \
  "3cca18b368ae95cdbdebbff572ccafa662551015" \
  "skills/engineering/wayfinder=wayfinder" \
  "skills/productivity/grilling=grilling" \
  "skills/engineering/domain-modeling=domain-modeling" \
  "skills/engineering/research=research" \
  "skills/engineering/prototype=prototype"

expected=(
  karpathy-guidelines
  debugging-code
  wayfinder
  grilling
  domain-modeling
  research
  prototype
  ocuforge-ai-research
)

for skill in "${expected[@]}"; do
  test -f "$SKILLS_ROOT/$skill/SKILL.md" || {
    echo "Skill verification failed: $SKILLS_ROOT/$skill/SKILL.md" >&2
    exit 1
  }
done

printf 'OcuForge Codex skills ready:\n'
printf ' - %s\n' "${expected[@]}"
printf 'Pins: .codex/skills.lock.json\n'
