#!/usr/bin/env bash
# Bastion host with a fixed public IP (Elastic IP) on your AWS account.
# No inbound ports: the team connects through SSM Session Manager.
#
#   bash create-bastion.sh           preview only, creates nothing
#   bash create-bastion.sh --apply   create IAM role, security group, EC2, Elastic IP
set -euo pipefail
export MSYS_NO_PATHCONV=1          # stop Git Bash turning /aws/... and /dev/xvda into Windows paths
# CONFIG: ตั้งค่าของคุณ (หรือ export ไว้ก่อนรัน)
export AWS_PROFILE="${AWS_PROFILE:-default}"
export AWS_REGION="${AWS_REGION:-ap-southeast-7}"
EXPECTED_ACCOUNT="${EXPECTED_ACCOUNT:-123456789012}"   # เลขบัญชี AWS ที่อนุญาตให้สร้าง (กันพลาดบัญชี)
export AWS_PAGER=""

NAME=customer-bastion
TYPE=t4g.micro
ROLE=bastion-ec2-role
PROFILE=bastion-ec2-profile
SG_NAME=bastion-sg
DIR="$(cd "$(dirname "$0")" && pwd)"
STATE="$DIR/bastion-state.env"
APPLY="${1:-}"

ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
[ "$ACCOUNT" = "$EXPECTED_ACCOUNT" ] || { echo "wrong account: $ACCOUNT"; exit 1; }
VPC=$(aws ec2 describe-vpcs --filters Name=isDefault,Values=true --query 'Vpcs[0].VpcId' --output text)
AMI=$(aws ssm get-parameter --name /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-arm64 --query Parameter.Value --output text)

EXISTING=$(aws ec2 describe-instances \
  --filters Name=tag:Name,Values=$NAME Name=instance-state-name,Values=pending,running,stopping,stopped \
  --query 'Reservations[].Instances[].InstanceId' --output text)
if [ -n "$EXISTING" ]; then echo "instance $NAME already exists: $EXISTING"; exit 1; fi

echo "account  : $ACCOUNT ($AWS_PROFILE, $AWS_REGION)"
echo "vpc      : $VPC (default)"
echo "ami      : $AMI (Amazon Linux 2023 arm64)"
echo "instance : $TYPE, 8 GB gp3 encrypted, IMDSv2 only"
echo "iam      : role $ROLE + profile $PROFILE (AmazonSSMManagedInstanceCore only)"
echo "sg       : $SG_NAME, no inbound rules"
echo "eip      : new Elastic IP tagged $NAME"
if [ "$APPLY" != "--apply" ]; then echo; echo "preview only. run with --apply to create."; exit 0; fi

echo; echo "== 1/6 IAM role + instance profile"
if ! aws iam get-role --role-name $ROLE >/dev/null 2>&1; then
  aws iam create-role --role-name $ROLE --tags Key=Project,Value=bastion \
    --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"ec2.amazonaws.com"},"Action":"sts:AssumeRole"}]}' >/dev/null
  aws iam attach-role-policy --role-name $ROLE --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore
fi
if ! aws iam get-instance-profile --instance-profile-name $PROFILE >/dev/null 2>&1; then
  aws iam create-instance-profile --instance-profile-name $PROFILE >/dev/null
  aws iam add-role-to-instance-profile --instance-profile-name $PROFILE --role-name $ROLE
  echo "waiting 15s for IAM to propagate"; sleep 15
fi

echo "== 2/6 security group"
SG=$(aws ec2 describe-security-groups --filters Name=group-name,Values=$SG_NAME Name=vpc-id,Values=$VPC \
  --query 'SecurityGroups[0].GroupId' --output text)
if [ "$SG" = "None" ]; then
  SG=$(aws ec2 create-security-group --group-name $SG_NAME --vpc-id $VPC \
    --description "Bastion: no inbound, SSM only" --query GroupId --output text)
  aws ec2 create-tags --resources "$SG" --tags Key=Name,Value=$SG_NAME Key=Project,Value=bastion
fi
echo "sg=$SG"

echo "== 3/6 launch instance"
UD="$DIR/.user-data.sh"
cat > "$UD" <<'EOF'
#!/bin/bash
hostnamectl set-hostname customer-bastion
timedatectl set-timezone Asia/Bangkok
dnf -y install dnf-automatic nmap-ncat || true
sed -i 's/^upgrade_type.*/upgrade_type = security/; s/^apply_updates.*/apply_updates = yes/' /etc/dnf/automatic.conf || true
systemctl enable --now dnf-automatic.timer || true
EOF
IID=""
for i in 1 2 3 4; do
  if IID=$(aws ec2 run-instances --image-id "$AMI" --instance-type $TYPE \
      --iam-instance-profile Name=$PROFILE --security-group-ids "$SG" \
      --metadata-options HttpTokens=required,HttpEndpoint=enabled \
      --block-device-mappings '[{"DeviceName":"/dev/xvda","Ebs":{"VolumeSize":8,"VolumeType":"gp3","Encrypted":true,"DeleteOnTermination":true}}]' \
      --user-data "file://$(cygpath -m "$UD")" \
      --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$NAME},{Key=Project,Value=bastion}]" \
                           "ResourceType=volume,Tags=[{Key=Name,Value=$NAME},{Key=Project,Value=bastion}]" \
      --query 'Instances[0].InstanceId' --output text 2>"$DIR/.run-err.txt"); then break; fi
  if grep -q "instance profile" "$DIR/.run-err.txt"; then echo "instance profile not ready, retry $i"; sleep 10; else cat "$DIR/.run-err.txt"; exit 1; fi
done
[ -n "$IID" ] || { cat "$DIR/.run-err.txt"; exit 1; }
echo "instance=$IID"
echo "IID=$IID" > "$STATE"; echo "SG=$SG" >> "$STATE"
aws ec2 wait instance-running --instance-ids "$IID"

echo "== 4/6 Elastic IP"
ALLOC=$(aws ec2 allocate-address --domain vpc \
  --tag-specifications "ResourceType=elastic-ip,Tags=[{Key=Name,Value=$NAME},{Key=Project,Value=bastion}]" \
  --query AllocationId --output text)
echo "ALLOC=$ALLOC" >> "$STATE"
aws ec2 associate-address --instance-id "$IID" --allocation-id "$ALLOC" >/dev/null
EIP=$(aws ec2 describe-addresses --allocation-ids "$ALLOC" --query 'Addresses[0].PublicIp' --output text)
echo "EIP=$EIP" >> "$STATE"
echo "eip=$EIP"

echo "== 5/6 wait for SSM agent"
PING=""
for i in $(seq 1 30); do
  PING=$(aws ssm describe-instance-information --filters Key=InstanceIds,Values="$IID" \
    --query 'InstanceInformationList[0].PingStatus' --output text 2>/dev/null || true)
  [ "$PING" = "Online" ] && break
  sleep 10
done
echo "ssm=$PING"
[ "$PING" = "Online" ] || { echo "SSM not online after 5 min, check later"; exit 1; }

echo "== 6/6 verify outbound IP seen from the internet"
# the first command sent right after the agent registers can stay Pending forever, so cancel and resend
OUT=""
for attempt in 1 2 3; do
  CID=$(aws ssm send-command --instance-ids "$IID" --document-name AWS-RunShellScript \
    --parameters 'commands=["curl -s https://checkip.amazonaws.com"]' --query Command.CommandId --output text)
  for i in $(seq 1 12); do
    sleep 5
    S=$(aws ssm get-command-invocation --command-id "$CID" --instance-id "$IID" --query Status --output text 2>/dev/null || true)
    case "$S" in Success|Failed|TimedOut|Cancelled) break ;; esac
  done
  OUT=$(aws ssm get-command-invocation --command-id "$CID" --instance-id "$IID" \
    --query StandardOutputContent --output text 2>/dev/null | tr -d '[:space:]' || true)
  [ -n "$OUT" ] && break
  echo "check command $S, resend $attempt"
  aws ssm cancel-command --command-id "$CID" >/dev/null 2>&1 || true
done
echo "outbound ip = $OUT"
if [ "$OUT" = "$EIP" ]; then echo "OK: outbound traffic leaves from Elastic IP $EIP"; else echo "MISMATCH: expected $EIP"; exit 1; fi
echo; echo "state saved to $STATE"; cat "$STATE"
