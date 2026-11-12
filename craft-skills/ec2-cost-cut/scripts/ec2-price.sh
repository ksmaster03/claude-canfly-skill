#!/usr/bin/env bash
# On-demand Linux price per hour, vCPU and memory from the AWS Pricing API (works from any profile with pricing:GetProducts).
#   bash ec2-price.sh [region] type ...      e.g. bash ec2-price.sh ap-southeast-7 t3.medium t3.large m7i-flex.large
set -uo pipefail
export AWS_PAGER=""
REGION="ap-southeast-7"
case "${1:-}" in *-*-[0-9]) REGION="$1"; shift ;; esac
for t in "$@"; do
  p=$(aws pricing get-products --region us-east-1 --service-code AmazonEC2 --filters \
     Type=TERM_MATCH,Field=regionCode,Value="$REGION" Type=TERM_MATCH,Field=instanceType,Value="$t" \
     Type=TERM_MATCH,Field=operatingSystem,Value=Linux Type=TERM_MATCH,Field=tenancy,Value=Shared \
     Type=TERM_MATCH,Field=preInstalledSw,Value=NA Type=TERM_MATCH,Field=capacitystatus,Value=Used \
     Type=TERM_MATCH,Field=licenseModel,Value="No License required" \
     --query "PriceList[0]" --output text 2>&1 | python -c "import sys,json
s=sys.stdin.read().strip()
try:
  d=json.loads(s); a=d['product']['attributes']; od=list(d['terms']['OnDemand'].values())[0]; pd=list(od['priceDimensions'].values())[0]
  print('%s/h  %s vCPU  %s  ~\$%.1f/month 24x7' % (pd['pricePerUnit']['USD'], a.get('vcpu'), a.get('memory'), float(pd['pricePerUnit']['USD'])*730))
except Exception: print('n/a')")
  echo "$REGION $t $p"
done
