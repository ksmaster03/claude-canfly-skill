#!/usr/bin/env bash
# Connect to the customer bastion through SSM (no SSH key, no open port).
#
#   bash connect.sh shell                                  shell on the bastion
#   bash connect.sh forward <host> <port> [local-port]     tunnel localhost:<local-port> -> bastion -> <host>:<port>
#   bash connect.sh ssh <user@host> [ssh args...]          SSH to a customer host through the bastion (starts bastion if stopped)
#   bash connect.sh start | stop | status                  power the bastion on/off (Elastic IP stays the same)
#
# examples
#   bash connect.sh forward 10.0.1.10 3389        then RDP to localhost:13389
#   bash connect.sh forward erp.customer.example.com 443 then open https://localhost:443 (cert name will not match)
#   bash connect.sh forward 10.0.1.20 1433 11433  then SQL client to localhost,11433
set -euo pipefail
export MSYS_NO_PATHCONV=1
# CONFIG: ตั้งค่าของคุณ (หรือ export ไว้ก่อนรัน)
export AWS_PROFILE="${AWS_PROFILE:-default}"
export AWS_REGION="${AWS_REGION:-ap-southeast-7}"
DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$DIR/bastion-state.env"

state() { aws ec2 describe-instances --instance-ids "$IID" --query 'Reservations[0].Instances[0].State.Name' --output text | tr -d '\r'; }
ensure_running() {
  local s; s=$(state)
  [ "$s" = "running" ] || { echo "bastion is $s, starting"; aws ec2 start-instances --instance-ids "$IID" >/dev/null; aws ec2 wait instance-running --instance-ids "$IID"; }
  for _ in $(seq 1 36); do
    [ "$(aws ssm describe-instance-information --filters Key=InstanceIds,Values="$IID" \
        --query 'InstanceInformationList[0].PingStatus' --output text | tr -d '\r')" = "Online" ] && return 0
    sleep 5
  done
  echo "bastion SSM agent not online"; return 1
}

case "${1:-}" in
  start) ensure_running && echo "bastion running ($EIP)" ;;
  stop)  aws ec2 stop-instances --instance-ids "$IID" >/dev/null && echo "bastion stopping (Elastic IP $EIP kept)" ;;
  status) echo "bastion $(state) ($EIP)" ;;
  ssh)
    TARGET="${2:?user@host required}"; shift 2
    RUSER="${TARGET%@*}"; RHOST="${TARGET#*@}"; LPORT="${LPORT:-2222}"
    ensure_running || exit 1
    LOG="$(mktemp)"
    aws ssm start-session --target "$IID" --document-name AWS-StartPortForwardingSessionToRemoteHost \
      --parameters "{\"host\":[\"$RHOST\"],\"portNumber\":[\"22\"],\"localPortNumber\":[\"$LPORT\"]}" > "$LOG" 2>&1 &
    PF=$!
    for _ in $(seq 1 30); do grep -q "Waiting for connections" "$LOG" && break; sleep 1; done
    SID=$(grep -o 'SessionId: [^ .]*' "$LOG" | head -1 | cut -d' ' -f2)
    # HostKeyAlias keeps the real host name in known_hosts instead of 127.0.0.1:<port>
    ssh -p "$LPORT" -o HostKeyAlias="$RHOST" -o StrictHostKeyChecking=accept-new "$RUSER@127.0.0.1" "$@"
    RC=$?
    [ -n "$SID" ] && aws ssm terminate-session --session-id "$SID" >/dev/null 2>&1
    kill "$PF" 2>/dev/null; rm -f "$LOG"
    exit $RC
    ;;
  shell)
    aws ssm start-session --target "$IID"
    ;;
  forward)
    HOST="${2:?host required}"; RPORT="${3:?port required}"
    DEFAULT_LPORT="$RPORT"; [ "$RPORT" = "3389" ] && DEFAULT_LPORT=13389   # 3389 is often taken on Windows
    LPORT="${4:-$DEFAULT_LPORT}"
    echo "localhost:$LPORT -> bastion $IID ($EIP) -> $HOST:$RPORT   (Ctrl+C to stop)"
    aws ssm start-session --target "$IID" \
      --document-name AWS-StartPortForwardingSessionToRemoteHost \
      --parameters "{\"host\":[\"$HOST\"],\"portNumber\":[\"$RPORT\"],\"localPortNumber\":[\"$LPORT\"]}"
    ;;
  *)
    sed -n '2,12p' "$0"; exit 1
    ;;
esac
