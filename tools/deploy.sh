#!/usr/bin/env bash
# 배포 — 정적 사이트를 GCP VM(n8n-instance)의 /var/www/portfolio 로 올립니다.
#
#   bash tools/deploy.sh            # 검증 통과 시에만 배포
#   bash tools/deploy.sh --skip-verify
#
# gcloud 기본 계정이 다른 계정으로 바뀌어 있는 경우가 있어 portfolio 구성을 명시합니다.
set -euo pipefail

cd "$(dirname "$0")/.."

GCLOUD="${GCLOUD:-$HOME/google-cloud-sdk/bin/gcloud}"
[ -x "$GCLOUD" ] || GCLOUD="$(command -v gcloud || true)"
if [ -z "$GCLOUD" ]; then
  echo "gcloud를 찾지 못했습니다. GCLOUD=/path/to/gcloud 로 지정하세요." >&2
  exit 1
fi

export CLOUDSDK_ACTIVE_CONFIG_NAME="${CLOUDSDK_ACTIVE_CONFIG_NAME:-portfolio}"

# gcloud는 Python 3.10~3.14가 필요합니다. GUI 앱처럼 PATH가 최소인 환경에서는
# 시스템 3.9만 보여 실패하므로, 쓸 수 있는 인터프리터를 찾아 명시합니다.
if [ -z "${CLOUDSDK_PYTHON:-}" ]; then
  for v in 3.12 3.13 3.11 3.10 3.14; do
    for p in "$HOME/.local/bin/python$v" "/opt/homebrew/bin/python$v" "/usr/local/bin/python$v"; do
      if [ -x "$p" ]; then
        export CLOUDSDK_PYTHON="$p"
        break 2
      fi
    done
  done
fi
if [ -z "${CLOUDSDK_PYTHON:-}" ]; then
  echo "Python 3.10~3.14를 찾지 못했습니다. CLOUDSDK_PYTHON=/path/to/python3.12 로 지정하세요." >&2
  exit 1
fi
VM="${VM:-n8n-instance}"
ZONE="${ZONE:-us-west1-b}"
REMOTE_TMP="/tmp/site"
TARGET="/var/www/portfolio"

if [ "${1:-}" != "--skip-verify" ]; then
  echo "── 검증 ──"
  python3 tools/verify.py
fi

echo
echo "── 업로드 (${VM}, ${ZONE}) ──"
"$GCLOUD" compute ssh "$VM" --zone="$ZONE" --command="rm -rf ${REMOTE_TMP} && mkdir -p ${REMOTE_TMP}"
"$GCLOUD" compute scp --recurse \
  index.html favicon.ico favicon-32.png favicon.svg dashboard \
  "$VM:${REMOTE_TMP}/" --zone="$ZONE"

echo
echo "── 반영 ──"
# VM에 rsync가 없을 수 있어 cp 경로를 함께 둡니다. 배포 대상은 저장소에서 전부
# 재생성되는 디렉터리이므로 기존 내용을 지우고 새로 채웁니다.
"$GCLOUD" compute ssh "$VM" --zone="$ZONE" --command="
  set -e
  sudo mkdir -p ${TARGET}
  if command -v rsync >/dev/null 2>&1; then
    sudo rsync -a --delete ${REMOTE_TMP}/ ${TARGET}/
  else
    sudo find ${TARGET} -mindepth 1 -delete
    sudo cp -a ${REMOTE_TMP}/. ${TARGET}/
  fi
  sudo nginx -t && sudo systemctl reload nginx"

echo
echo "배포 완료 → http://34.83.67.147/dashboard/"
