# 🤖 Stale Repo Watcher

[![AWS](https://img.shields.io/badge/AWS-Lambda-orange?logo=awslambda)](https://aws.amazon.com/lambda/)
[![Bedrock](https://img.shields.io/badge/Amazon-Bedrock-blueviolet?logo=amazonaws)](https://aws.amazon.com/bedrock/)
[![EventBridge](https://img.shields.io/badge/EventBridge-Scheduler-yellow?logo=amazonaws)](https://aws.amazon.com/eventbridge/)
[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-lightgrey)](#)

> An always-on agent that checks a GitHub repo for stale issues and PRs every morning, summarizes them with **Amazon Bedrock (Nova Micro)**, and emails a nudge report — no manual trigger required.

---

## ✨ What It Does

| | |
|---|---|
| ⏰ **Trigger** | EventBridge Scheduler fires on a daily cron schedule |
| 🔍 **Action** | Lambda fetches open issues/PRs, filters items untouched 7+ days |
| 🧠 **Intelligence** | Amazon Bedrock (Nova Micro) turns the raw list into a prioritized report |
| 📬 **Output** | SNS emails you the report — nothing to open, it's just there |


**EventBridge Schedule configured:**


![Schedule Detail](<schedule detail.png>)

**Lambda test execution succeeded:**


![Lambda Test](<Lambda test success.png>)

**IAM permissions configured:**


![IAM Role](<IAM role.png>)

**SNS email subscription confirmed:**


![SNS Subscription](<SNS subscription.png>)

**Automated email report received:**


![Email Report](<email report.png>)
---

## 🏗️ Architecture

```
┌─────────────────────────┐
│  EventBridge Scheduler  │   daily cron trigger
└────────────┬─────────────┘
             │
             ▼
┌─────────────────────────┐
│       AWS Lambda        │──────►  GitHub REST API
│   (stale-repo-watcher)  │         (fetch open issues/PRs)
└────────────┬─────────────┘
             │
             ▼
┌─────────────────────────┐
│   Amazon Bedrock         │   Nova Micro summarizes +
│   (Nova Micro)           │   drafts the nudge report
└────────────┬─────────────┘
             │
             ▼
┌─────────────────────────┐
│       Amazon SNS         │──────►  📧 Email report
└─────────────────────────┘
```

---

## ✅ Proof It Ran Automatically

<table>
<tr>
<td align="center" width="50%">
<b>EventBridge Schedule Configured</b><br><br>
<img src="schedule detail.png" width="90%">
</td>
<td align="center" width="50%">
<b>Lambda Test Execution Succeeded</b><br><br>
<img src="Lambda test success.png" width="90%">
</td>
</tr>
<tr>
<td align="center" width="50%">
<b>IAM Permissions Configured</b><br><br>
<img src="IAM role.png" width="90%">
</td>
<td align="center" width="50%">
<b>SNS Email Subscription Confirmed</b><br><br>
<img src="SNS subscription.png" width="90%">
</td>
</tr>
<tr>
<td align="center" colspan="2">
<b>Automated Email Report Received</b><br><br>
<img src="email report.png" width="60%">
</td>
</tr>
</table>

---

## 📁 Repo Structure

```
stale-repo-watcher/
├── src/
│   └── lambda_function.py   # the agent logic
├── README.md
└── .gitignore
```

---

## 🚀 Deploy via AWS Console

<details>
<summary><b>1. Create the SNS topic (for email alerts)</b></summary>
<br>

1. AWS Console → **SNS** → Topics → Create topic → type: **Standard** → name: `stale-repo-watcher-alerts`
2. Open the topic → Create subscription → protocol: **Email** → enter your email
3. Check your inbox and click **Confirm subscription**
4. Copy the **Topic ARN** — needed later

</details>

<details>
<summary><b>2. Request Bedrock model access</b></summary>
<br>

1. AWS Console → **Bedrock** → Model catalog
2. Search **Nova Micro** → confirm access (Amazon's own Nova models are often available instantly, no request needed)

</details>

<details>
<summary><b>3. Create the Lambda function</b></summary>
<br>

1. AWS Console → **Lambda** → Create function
2. Author from scratch → name: `stale-repo-watcher` → runtime: **Python 3.12**
3. **Code** tab → paste in `src/lambda_function.py` contents → **Deploy**
4. **Configuration → Environment variables**:

| Key | Value |
|---|---|
| `GITHUB_REPO` | `owner/repo-name` |
| `STALE_DAYS` | `7` |
| `SNS_TOPIC_ARN` | your topic ARN from step 1 |
| `BEDROCK_MODEL_ID` | `amazon.nova-micro-v1:0` |

5. **Configuration → General configuration** → Edit → **Timeout: 30 sec**

</details>

<details>
<summary><b>4. Grant Lambda permission to call SNS + Bedrock</b></summary>
<br>

1. **Configuration → Permissions** → click execution role (opens IAM)
2. Add permissions → Create inline policy → JSON tab:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {"Effect": "Allow", "Action": "sns:Publish", "Resource": "YOUR_SNS_TOPIC_ARN"},
    {"Effect": "Allow", "Action": "bedrock:InvokeModel", "Resource": "*"}
  ]
}
```

3. Name it `stale-watcher-permissions` → Create policy

</details>

<details>
<summary><b>5. Test manually before scheduling</b></summary>
<br>

1. **Test** tab → create test event → any dummy `{}` → **Test**
2. Check execution result + your inbox
3. Fix errors here — faster than waiting on a live cron trigger

</details>

<details>
<summary><b>6. Schedule with EventBridge Scheduler</b></summary>
<br>

1. **EventBridge → Scheduler → Create schedule**
2. Recurring or one-time — cron: `0 13 * * ? *` (adjust for your timezone)
3. Target: **AWS Lambda → Invoke** → `stale-repo-watcher`
4. Permissions: **Create new role for this schedule**
5. **Create schedule**

</details>

<details>
<summary><b>7. Confirm it fired on its own</b></summary>
<br>

Check **CloudWatch Logs** (Lambda → Monitor → View CloudWatch logs) for an execution timestamp matching the schedule — plus the email that landed in your inbox without you clicking anything.

</details>

---

## ⚙️ Environment Variables

| Variable | Description | Example |
|---|---|---|
| `GITHUB_REPO` | Repo to monitor | `octocat/Hello-World` |
| `STALE_DAYS` | Days of inactivity before flagging | `7` |
| `SNS_TOPIC_ARN` | SNS topic for reports | `arn:aws:sns:us-east-1:xxxx:stale-repo-watcher-alerts` |
| `BEDROCK_MODEL_ID` | Bedrock model used | `amazon.nova-micro-v1:0` |

---

## 💸 Cost Note

All services used (Lambda, EventBridge Scheduler, SNS, Bedrock Nova Micro at this scale) fall within **AWS Free Tier** for a personal project running on a schedule. Set a billing alarm in AWS Budgets if you plan to extend or scale this up.

---

<p align="center"><i>Built for the AWS Builder Center Weekend Agent Challenge 🏆</i></p>
