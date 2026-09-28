# Facilitator guide / Guía del facilitador

## Before the session (T-1 day)

1. **Deploy the guide** with `scripts/deploy.sh` (or the console) passing all participant emails in `ParticipantEmails`.
   * Each student receives *"Amazon Web Services – Email Address Verification Request"*. Ask them to click it **before** the session; it removes friction from Module 3.
   * Share the `GuideUrl` (and the password if you set one).
2. **Student accounts**: Workshop Studio event, sandbox accounts, or IAM users with `PowerUserAccess` plus permissions to create/attach IAM roles for Lambda. Confirm the region (default `us-east-1`); SES must be available there.
3. **SES sandbox** is fine: students send from and to their own verified address.
4. Open the slides `slides/AWS_Services_Basics_101_SantiGarcia.pdf` (≈ 20–25 min intro) before the hands-on.

## Suggested timing (120 min)

| Time | Block |
|------|-------|
| 00:00 | Intro slides (cloud, serverless, S3, DynamoDB, Athena — skip Aurora/QuickSight/Terraform or keep as 1 slide each) — *optional 20 min if the session is 2h20* |
| 00:00–00:10 | Module 0 – setup |
| 00:10–00:25 | Module 1 – S3 |
| 00:25–00:40 | Module 2 – DynamoDB (spend time on PK/SK with the CSV rows on screen) |
| 00:40–00:50 | Module 3 – SES |
| 00:50–01:15 | Module 4 – Lambda (the longest; walk through the code once on the projector) |
| 01:15–01:30 | Module 5 – EventBridge (the "wow" moment) |
| 01:30–01:45 | Module 6 – Athena |
| 01:45–01:55 | Module 7 – wrap-up, quiz, cleanup |
| 01:55–02:00 | Q&A |

## Expected numbers (to verify quickly on screen)

* `transacciones_2026_09.csv`: 30 rows → Lambda test returns `transacciones: 30`; DynamoDB Query `CLI-001` returns 6 items.
* `transacciones_2026_10.csv`: 15 rows → after EventBridge, DynamoDB holds 45 items.
* Athena: `SELECT COUNT(*)` = 45; JOIN by `segmento` returns 3 rows.

## Common issues

| Symptom | Fix |
|---------|-----|
| Resources "disappeared" | Wrong region selected. |
| Bucket name exists | Add a suffix and set it in the guide's setup panel. |
| Lambda `AccessDenied` | Missing managed policy on the execution role. |
| `Email address is not verified` | Verify recipient/sender in SES in the same region. |
| EventBridge rule never fires | S3 → Properties → Amazon EventBridge = On; pattern bucket name exact; key under `entrada/`. |
| Athena 0 rows | `LOCATION` must end with `/` and point to the right prefix. |

## Cleanup

Students follow Module 7. As instructor, delete the hosting stack with `scripts/deploy.sh --delete` (the custom resource empties the bucket and removes the SES identities it created).
