#!/bin/bash

LOGFILE="$1"
TARGET_SERVER="$2"
start=$(date +%s)

# 💡 Validasi awal
if [ -z "$LOGFILE" ]; then
  echo "❌ Log file argument missing." >&2
  exit 1
fi

touch "$LOGFILE" 2>/dev/null || {
  echo "❌ Cannot write to log file: $LOGFILE" >&2
  exit 1
}

# ===========================
# 🌐 Default deploy (tanpa target)
# ===========================
if [ -z "$TARGET_SERVER" ]; then
  echo "[$(date)] ⚙️ No target server provided, using default: 30.30.30.202" | tee -a "$LOGFILE"

  ssh -tt -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@30.30.30.202 \
    "cd /home/ubuntu/profiling-database && ./deploy.sh" 2>&1 | tee -a "$LOGFILE"

  RETVAL=${PIPESTATUS[0]}
else
  # ✅ Validasi jq tersedia
  if ! command -v jq &> /dev/null; then
    echo "❌ jq not installed. Please install jq." | tee -a "$LOGFILE"
    exit 1
  fi

  # 🔍 Cari info server di servers.json
  echo "🔍 Looking for server: $TARGET_SERVER in static/servers.json"
  MATCHED_SERVER=$(jq -r --arg ip "$TARGET_SERVER" '
  .[] | select(
    (.ip | ascii_downcase == ($ip | ascii_downcase)) or 
    (.alias | ascii_downcase == ($ip | ascii_downcase))
  )
' static/servers.json)

  if [ -z "$MATCHED_SERVER" ]; then
    echo "❌ Invalid server: IP or alias '$TARGET_SERVER' not found in servers.json" | tee -a "$LOGFILE"
    exit 1
  fi

  SSH_HOST=$(echo "$MATCHED_SERVER" | jq -r '.ip')
  SSH_USER=$(echo "$MATCHED_SERVER" | jq -r '.user')
  SERVER_PATH=$(echo "$MATCHED_SERVER" | jq -r '.path')

  echo "[$(date)] 🔧 Starting deploy to ${TARGET_SERVER} (${SSH_USER}@${SSH_HOST})..." | tee -a "$LOGFILE"

  if [ -z "$SERVER_PATH" ] || [ "$SERVER_PATH" == "null" ]; then
    echo "[$(date)] ⚠️ Server valid, but no path defined. Skipping execution." | tee -a "$LOGFILE"
    RETVAL=1
  else
    echo "[$(date)] 🔧 Executing SSH command: ssh ${SSH_USER}@${SSH_HOST} 'cd $SERVER_PATH && ./deploy.sh'" | tee -a "$LOGFILE"
    ssh -tt -o StrictHostKeyChecking=no -o ConnectTimeout=10 "${SSH_USER}@${SSH_HOST}" \
      "export TERM=dumb && cd $SERVER_PATH && ./deploy.sh 2>&1" | tee -a "$LOGFILE"
    RETVAL=${PIPESTATUS[0]}
  fi
fi

# ❌ Logging jika gagal
if [ "$RETVAL" -ne 0 ]; then
  echo "❌ SSH or deploy.sh exited with code $RETVAL" | tee -a "$LOGFILE"
fi

# ===========================
# ⏱️ Waktu Eksekusi
# ===========================
end=$(date +%s)
runtime=$((end - start))
hours=$((runtime / 3600))
minutes=$(((runtime % 3600) / 60))
seconds=$((runtime % 60))

echo "✅ Deploy finished in ${hours}h ${minutes}m ${seconds}s." | tee -a "$LOGFILE"
exit $RETVAL