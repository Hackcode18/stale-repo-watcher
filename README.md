# Stale Repo Watcher

An always-on agent that checks a GitHub repo for stale issues/PRs every morning, summarizes them with Amazon Bedrock (Nova Micro), and emails you a nudge report — no manual trigger required.

## What it does

- **Trigger:** EventBridge Scheduler fires on a daily cron schedule
- **Action:** Lambda fetches open issues/PRs from a GitHub repo, filters for items untouched 7+ days, sends them to Bedrock for summarization
- **Output:** Emails you a prioritized report via SNS

```
EventBridge Scheduler (daily cron)
        │
        ▼
    AWS Lambda ──► GitHub REST API
        │
        ▼
  Amazon Bedrock (Nova Micro)
        │
        ▼
     Amazon SNS ──► Email
```

## Repo structure

```
stale-repo-watcher/
├── src/
│   └── lambda_function.py   # the agent logic
├── README.md
└── .gitignore
```

## Deploy via AWS Console (step by step)

### 1. Create the SNS topic (for email alerts)
1. AWS Console → **SNS** → Topics → Create topic → type: **Standard** → name: `stale-repo-watcher-alerts`
2. Open the topic → Create subscription → protocol: **Email** → enter your email
3. Check your inbox and click **Confirm subscription** (report emails won't arrive until you do this)
4. Copy the **Topic ARN** — you'll need it in step 3

### 2. Request Bedrock model access (do this first, can take time to approve)
1. AWS Console → **Bedrock** → Model access (left sidebar)
2. Request access to **Amazon Nova Micro**
3. Wait for status to show "Access granted" before testing the Lambda

### 3. Create the Lambda function
1. AWS Console → **Lambda** → Create function
2. Author from scratch → name: `stale-repo-watcher` → runtime: **Python 3.12**
3. Once created, go to the **Code** tab → open `lambda_function.py` in the inline editor
4. Delete the placeholder content, paste in the contents of `src/lambda_function.py` from this repo → **Deploy**
5. Go to **Configuration → Environment variables** → add:
   | Key | Value |
   |---|---|
   | `GITHUB_REPO` | `owner/repo-name` (the repo you want watched) |
   | `STALE_DAYS` | `7` |
   | `SNS_TOPIC_ARN` | the ARN from step 1 |
   | `BEDROCK_MODEL_ID` | `amazon.nova-micro-v1:0` |
6. Go to **Configuration → General configuration** → Edit → set **Timeout** to 30 seconds

### 4. Give the Lambda permission to call SNS and Bedrock
1. Go to **Configuration → Permissions** → click the execution role link (opens IAM)
2. Add permissions → Attach policies → search and attach `AWSLambdaBasicExecutionRole` (usually already there)
3. Add permissions → Create inline policy → JSON tab → paste:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {"Effect": "Allow", "Action": "sns:Publish", "Resource": "YOUR_SNS_TOPIC_ARN"},
       {"Effect": "Allow", "Action": "bedrock:InvokeModel", "Resource": "*"}
     ]
   }
   ```
4. Name it `stale-watcher-permissions` → Create policy

### 5. Test it manually before scheduling
1. In Lambda → **Test** tab → create a test event (any dummy JSON, e.g. `{}`)
2. Click **Test** → check execution result and your email inbox
3. Fix any errors here before moving to step 6 — this is faster to debug than waiting on a cron trigger

### 6. Schedule it with EventBridge Scheduler
1. AWS Console → **EventBridge** → Scheduler → Create schedule
2. Name: `stale-repo-watcher-schedule`
3. Schedule pattern: **Recurring schedule** → Cron-based → e.g. `0 13 * * ? *` (7 AM CT / adjust for your timezone — this is in UTC)
4. Target: **AWS Lambda → Invoke** → select `stale-repo-watcher`
5. Action after schedule completes: leave default
6. On the permissions step, choose **Create new role for this schedule** (console handles the trust policy automatically — this is the part that's easy to misconfigure via CLI, the console does it for you)
7. Create schedule

### 7. Confirm it fired on its own
- Wait for the next scheduled run, or check **CloudWatch Logs** for the Lambda (Lambda → Monitor → View CloudWatch logs) to see execution history
- Screenshot the CloudWatch log timestamp + the email you received — this is your "it ran without me" proof for the article

## Environment variables reference

| Variable | Description | Example |
|---|---|---|
| `GITHUB_REPO` | Repo to monitor | `octocat/Hello-World` |
| `STALE_DAYS` | Days of inactivity before flagging | `7` |
| `SNS_TOPIC_ARN` | SNS topic to publish reports to | `arn:aws:sns:us-east-1:123456789012:stale-repo-watcher-alerts` |
| `BEDROCK_MODEL_ID` | Bedrock model for summarization | `amazon.nova-micro-v1:0` |

## Cost note

All services used (Lambda, EventBridge Scheduler, SNS, Bedrock Nova Micro at this scale) fall within AWS Free Tier for a personal project running a daily job. Monitor usage in Billing if you extend it.
