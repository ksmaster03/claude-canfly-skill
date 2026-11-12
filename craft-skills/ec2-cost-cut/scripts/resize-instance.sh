#!/usr/bin/env bash
# Resize one EC2 instance: stop -> snapshot root volume -> change type -> start -> verify containers + URLs.
# The instance is always started again, even if the type change fails.
#   bash resize-instance.sh <instance-id> <new-type> <probe-url>...
set -uo pipefail
# CONFIG: ตั้งค่าของคุณ (หรือ export ไว้ก่อนรัน)
export AWS_PROFILE="${AWS_PROFILE:-default}" AWS_REGION="${AWS_REGION:-ap-southeast-7}" AWS_PAGER="" MSYS_NO_PATHCONV=1
IID="$1"; NEW="$2"; shift 2; URLS=("$@")

ssm() {  # run one shell line on the instance, print stdout
  local params cid s
  params=$(python -c 'import json,sys; print(json.dumps({"commands":[sys.argv[1]]}))' "$1")
  cid=$(aws ssm send-command --instance-ids "$IID" --document-name AWS-RunShellScript --parameters "$params" \
        --query Command.CommandId --output text | tr -d '\r') || return 1
  for _ in $(seq 1 24); do
    sleep 5
    s=$(aws ssm get-command-invocation --command-id "$cid" --instance-id "$IID" --query Status --output text 2>/dev/null | tr -d '\r')
    case "$s" in Success|Failed|TimedOut|Cancelled) break ;; esac
  done
  aws ssm get-command-invocation --command-id "$cid" --instance-id "$IID" --query StandardOutputContent --output text 2>/dev/null | tr -d '\r'
}
q() { aws ec2 describe-instances --instance-ids "$IID" --query "Reservations[0].Instances[0].$1" --output text | tr -d '\r'; }

NAME=$(q "Tags[?Key=='Name']|[0].Value"); OLD=$(q InstanceType)
VOL=$(q "BlockDeviceMappings[0].Ebs.VolumeId")
echo "== $NAME $IID: $OLD -> $NEW (root $VOL)"
[ "$OLD" = "$NEW" ] && { echo "already $NEW"; exit 0; }

BEFORE=$(ssm "docker ps --format '{{.Names}}' | sort")
echo "containers before: $(echo $BEFORE)"
[ -n "$BEFORE" ] || { echo "could not read containers, abort before stopping"; exit 1; }

T_STOP=$(date +%s)
echo "== stop ($(date +%H:%M:%S))"
aws ec2 stop-instances --instance-ids "$IID" >/dev/null || { echo "stop failed"; exit 1; }
aws ec2 wait instance-stopped --instance-ids "$IID"
echo "stopped after $(( $(date +%s) - T_STOP ))s"

SNAP=$(aws ec2 create-snapshot --volume-id "$VOL" --description "$NAME before resize $OLD to $NEW" \
  --tag-specifications "ResourceType=snapshot,Tags=[{Key=Name,Value=$NAME-pre-resize},{Key=Purpose,Value=rollback}]" \
  --query SnapshotId --output text | tr -d '\r')
echo "snapshot $SNAP (point-in-time of the stopped disk)"

if aws ec2 modify-instance-attribute --instance-id "$IID" --instance-type "Value=$NEW"; then
  echo "type changed to $NEW"
else
  echo "TYPE CHANGE FAILED, starting again as $OLD"
fi

echo "== start"
aws ec2 start-instances --instance-ids "$IID" >/dev/null
aws ec2 wait instance-running --instance-ids "$IID"
echo "running as $(q InstanceType), ip $(q PublicIpAddress)"

for _ in $(seq 1 36); do
  P=$(aws ssm describe-instance-information --filters Key=InstanceIds,Values="$IID" \
      --query 'InstanceInformationList[0].PingStatus' --output text 2>/dev/null | tr -d '\r')
  [ "$P" = "Online" ] && break; sleep 5
done
echo "ssm $P"

AFTER=""
for _ in $(seq 1 12); do
  AFTER=$(ssm "docker ps --format '{{.Names}}' | sort")
  STARTING=$(ssm "docker ps --format '{{.Status}}' | grep -c 'health: starting' || true")
  [ "$AFTER" = "$BEFORE" ] && [ "${STARTING:-0}" = "0" ] && break
  sleep 10
done
echo "containers after:  $(echo $AFTER)"
ssm "docker ps --format '{{.Names}} | {{.Status}}'"
OK=1; [ "$AFTER" = "$BEFORE" ] || { echo "MISSING: $(comm -23 <(echo "$BEFORE") <(echo "$AFTER") | tr '\n' ' ')"; OK=0; }

for u in "${URLS[@]}"; do
  code=000
  for _ in $(seq 1 18); do code=$(curl -s -o /dev/null -m 15 -w '%{http_code}' "$u"); [ "$code" = "200" ] && break; sleep 10; done
  echo "$u -> $code"; [ "$code" = "200" ] || OK=0
done
echo "downtime about $(( $(date +%s) - T_STOP ))s (stop to all checks done)"
echo "FINAL: $NAME $(q InstanceType) $([ $OK = 1 ] && echo OK || echo CHECK-FAILED) snapshot=$SNAP"
[ $OK = 1 ]
