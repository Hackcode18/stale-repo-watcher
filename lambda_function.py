import json
import os
import urllib.request
import boto3
from datetime import datetime, timezone

GITHUB_REPO = os.environ["GITHUB_REPO"]  # format: "owner/repo"
STALE_DAYS = int(os.environ.get("STALE_DAYS", "7"))
SNS_TOPIC_ARN = os.environ["SNS_TOPIC_ARN"]
BEDROCK_MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "amazon.nova-micro-v1:0")

bedrock = boto3.client("bedrock-runtime")
sns = boto3.client("sns")


def get_stale_items():
    """Fetch open issues/PRs from GitHub, filter by last update date."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues?state=open&sort=updated&direction=asc&per_page=30"
    req = urllib.request.Request(url, headers={"User-Agent": "stale-watcher-agent"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        items = json.loads(resp.read().decode())

    stale = []
    now = datetime.now(timezone.utc)
    for item in items:
        updated = datetime.fromisoformat(item["updated_at"].replace("Z", "+00:00"))
        age_days = (now - updated).days
        if age_days >= STALE_DAYS:
            stale.append({
                "title": item["title"],
                "number": item["number"],
                "url": item["html_url"],
                "age_days": age_days,
                "is_pr": "pull_request" in item,
            })
    return stale


def summarize_with_bedrock(stale_items):
    """Ask Bedrock Nova to draft a short nudge report."""
    if not stale_items:
        return "No stale issues or PRs found. Repo is current."

    listing = "\n".join(
        f"- #{i['number']} ({'PR' if i['is_pr'] else 'Issue'}): \"{i['title']}\" — "
        f"quiet for {i['age_days']} days — {i['url']}"
        for i in stale_items
    )

    prompt = (
        "You are an assistant that writes a short daily nudge report for a "
        "software repo maintainer. Given this list of stale issues/PRs, write "
        "a concise report (under 150 words) grouping by urgency, and suggest "
        "one concrete next action per item. Be direct, no fluff.\n\n"
        f"Stale items:\n{listing}"
    )

    body = {
        "messages": [{"role": "user", "content": [{"text": prompt}]}],
        "inferenceConfig": {"maxTokens": 400, "temperature": 0.3},
    }

    response = bedrock.invoke_model(
        modelId=BEDROCK_MODEL_ID,
        body=json.dumps(body),
    )
    result = json.loads(response["body"].read())
    return result["output"]["message"]["content"][0]["text"]


def lambda_handler(event, context):
    stale_items = get_stale_items()
    report = summarize_with_bedrock(stale_items)

    message = (
        f"Stale Repo Watcher Report — {GITHUB_REPO}\n"
        f"Run time: {datetime.now(timezone.utc).isoformat()}\n"
        f"{'-'*50}\n\n{report}"
    )

    sns.publish(
        TopicArn=SNS_TOPIC_ARN,
        Subject=f"[Stale Watcher] {len(stale_items)} item(s) need attention — {GITHUB_REPO}",
        Message=message,
    )

    return {
        "statusCode": 200,
        "body": json.dumps({"stale_count": len(stale_items), "report": report}),
    }
