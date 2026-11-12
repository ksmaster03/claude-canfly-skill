#!/usr/bin/env bash
# List every non-terminated EC2 instance in every region of the given AWS CLI profiles, plus Elastic IPs.
#   bash list-ec2.sh [profile ...]        default: every profile whose keys work
set -uo pipefail
export AWS_PAGER="" MSYS_NO_PATHCONV=1
PROFILES=("$@")
if [ ${#PROFILES[@]} -eq 0 ]; then
  for p in $(aws configure list-profiles | tr -d '\r'); do
    a=$(aws sts get-caller-identity --profile "$p" --query Account --output text 2>/dev/null | tr -d '\r')
    if [ -n "$a" ]; then echo "profile $p => $a"; PROFILES+=("$p"); else echo "profile $p => keys invalid, skipped"; fi
  done
fi
OUT="$(mktemp -d)"   # fresh folder, nothing to delete first
for p in "${PROFILES[@]}"; do
  for r in $(aws ec2 describe-regions --profile "$p" --region ap-southeast-1 --query "Regions[].RegionName" --output text | tr -d '\r'); do
    ( aws ec2 describe-instances --profile "$p" --region "$r" --filters Name=instance-state-name,Values=pending,running,stopping,stopped \
        --query "Reservations[].Instances[].[InstanceId,Tags[?Key=='Name']|[0].Value,InstanceType,State.Name,PublicIpAddress,LaunchTime]" \
        --output text 2>/dev/null | tr -d '\r' | sed "s/^/$p\t$r\t/" > "$OUT/$p-$r.tsv" ) &
  done
done; wait
echo; echo "profile	region	id	name	type	state	public-ip	launched(UTC)"
cat "$OUT"/*.tsv | sort -t$'\t' -k1,1 -k2,2 -k6,6
echo; echo "== Elastic IPs (ap-southeast-7)"
for p in "${PROFILES[@]}"; do aws ec2 describe-addresses --profile "$p" --region ap-southeast-7 --query "Addresses[].[PublicIp,InstanceId]" --output text | tr -d '\r' | sed "s/^/$p\t/"; done
