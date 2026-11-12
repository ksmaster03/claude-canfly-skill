#!/usr/bin/env bash
# End-to-end whitelist test with a throwaway "fake customer" server.
# The fake server only accepts TCP 8080 from the bastion Elastic IP, like a customer firewall would.
#   1) this PC -> fake server directly        expect BLOCKED
#   2) bastion -> fake server                  expect OK, server sees the Elastic IP
#   3) this PC -> connect.sh forward -> server expect OK, server sees the Elastic IP
# The fake server and its security group are deleted on exit, pass or fail.
set -uo pipefail
export MSYS_NO_PATHCONV=1
# CONFIG: ตั้งค่าของคุณ (หรือ export ไว้ก่อนรัน)
export AWS_PROFILE="${AWS_PROFILE:-default}"
export AWS_REGION="${AWS_REGION:-ap-southeast-7}"
export AWS_PAGER=""
DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$DIR/bastion-state.env"
NAME=fake-customer-test
PORT=8080
LPORT=18081
TR=ap-southeast-1   # fake server lives in Singapore: Bangkok vCPU quota is full, and a separate network is closer to a real customer
TID=""; TSG=""; FWD_LOG="$DIR/.fwd-whitelist.log"; RESULT=2   # 2 = tests never ran

cleanup() {
  echo; echo "== cleanup"
  SID=$(grep -o 'SessionId: [^ .]*' "$FWD_LOG" 2>/dev/null | head -1 | cut -d' ' -f2)
  [ -n "$SID" ] && aws ssm terminate-session --session-id "$SID" >/dev/null 2>&1
  [ -n "${FWD_PID:-}" ] && kill "$FWD_PID" 2>/dev/null
  rm -f "$FWD_LOG" "$DIR/.fake-ud.sh"
  if [ -n "$TID" ]; then
    aws ec2 terminate-instances --region $TR --instance-ids "$TID" >/dev/null && aws ec2 wait instance-terminated --region $TR --instance-ids "$TID"
    echo "terminated $TID"
  fi
  if [ -n "$TSG" ]; then aws ec2 delete-security-group --region $TR --group-id "$TSG" >/dev/null && echo "deleted $TSG"; fi
  echo
  case $RESULT in 0) echo "ALL TESTS PASSED" ;; 2) echo "ABORTED before tests ran" ;; *) echo "SOME TESTS FAILED" ;; esac
}
trap cleanup EXIT

VPC=$(aws ec2 describe-vpcs --region $TR --filters Name=isDefault,Values=true --query 'Vpcs[0].VpcId' --output text)
AMI=$(aws ssm get-parameter --region $TR --name /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64 --query Parameter.Value --output text)

echo "== create fake customer server in $TR (whitelist: $EIP/32 on tcp $PORT only)"
TSG=$(aws ec2 create-security-group --region $TR --group-name "$NAME-$(date +%s)" --vpc-id "$VPC" \
  --description "throwaway whitelist test" --query GroupId --output text) || exit 1
aws ec2 authorize-security-group-ingress --region $TR --group-id "$TSG" --protocol tcp --port $PORT --cidr "$EIP/32" >/dev/null || exit 1
cat > "$DIR/.fake-ud.sh" <<'EOF'
#!/bin/bash
cat > /opt/whoami.py <<'PY'
from http.server import BaseHTTPRequestHandler, HTTPServer
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        b = ("fake-customer says: you came from %s\n" % self.client_address[0]).encode()
        self.send_response(200); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
HTTPServer(("0.0.0.0", 8080), H).serve_forever()
PY
nohup python3 /opt/whoami.py >/var/log/whoami.log 2>&1 &
EOF
TID=$(aws ec2 run-instances --region $TR --image-id "$AMI" --instance-type t4g.nano --security-group-ids "$TSG" \
  --metadata-options HttpTokens=required,HttpEndpoint=enabled \
  --user-data "file://$(cygpath -m "$DIR/.fake-ud.sh")" \
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$NAME},{Key=Project,Value=bastion-test}]" \
  --query 'Instances[0].InstanceId' --output text) || exit 1
aws ec2 wait instance-running --region $TR --instance-ids "$TID"
TIP=$(aws ec2 describe-instances --region $TR --instance-ids "$TID" --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
echo "fake server $TID at $TIP:$PORT"
RESULT=0

run_on_bastion() {  # run one shell line on the bastion, print stdout
  local cid s
  cid=$(aws ssm send-command --instance-ids "$IID" --document-name AWS-RunShellScript \
    --parameters "{\"commands\":[\"$1\"]}" --query Command.CommandId --output text)
  for _ in $(seq 1 12); do
    sleep 5
    s=$(aws ssm get-command-invocation --command-id "$cid" --instance-id "$IID" --query Status --output text 2>/dev/null)
    case "$s" in Success|Failed|TimedOut|Cancelled) break ;; esac
  done
  aws ssm get-command-invocation --command-id "$cid" --instance-id "$IID" --query StandardOutputContent --output text 2>/dev/null
}

echo; echo "== wait for fake server to answer (from bastion)"
OUT2=""
for _ in $(seq 1 10); do
  OUT2=$(run_on_bastion "curl -s -m 5 http://$TIP:$PORT/ || true")
  [ -n "$OUT2" ] && break
done

echo; echo "== TEST 1: this PC -> $TIP:$PORT directly (expect BLOCKED)"
MYIP=$(curl -s -m 10 https://checkip.amazonaws.com)
echo "this PC public ip = $MYIP"
if curl -s -m 8 "http://$TIP:$PORT/" >/dev/null; then echo "FAIL: reached server without the bastion"; RESULT=1
else echo "PASS: blocked (timeout), whitelist is working"; fi

echo; echo "== TEST 2: bastion -> $TIP:$PORT (expect OK from $EIP)"
echo "${OUT2:-<no answer>}"
if echo "$OUT2" | grep -q "you came from $EIP"; then echo "PASS"; else echo "FAIL"; RESULT=1; fi

echo; echo "== TEST 3: this PC -> connect.sh forward -> $TIP:$PORT (expect OK from $EIP)"
bash "$DIR/connect.sh" forward "$TIP" $PORT $LPORT > "$FWD_LOG" 2>&1 &
FWD_PID=$!
for _ in $(seq 1 20); do grep -q "Waiting for connections" "$FWD_LOG" 2>/dev/null && break; sleep 2; done
OUT3=$(curl -s -m 10 "http://localhost:$LPORT/")
echo "${OUT3:-<no answer>}"
if echo "$OUT3" | grep -q "you came from $EIP"; then echo "PASS"; else echo "FAIL"; cat "$FWD_LOG"; RESULT=1; fi
exit $RESULT
