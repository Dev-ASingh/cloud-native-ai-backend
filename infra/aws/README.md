# On-demand AWS demonstration

This deployment is intentionally temporary. It creates one EC2 instance that
runs the API, worker, and PostgreSQL through Docker Compose. It does not create
RDS, NAT Gateway, a load balancer, an SSH ingress rule, or long-lived access
keys.

The public repository does not contain AWS credentials. GitHub Actions assumes
a narrowly scoped IAM role through GitHub's OIDC provider. The role ARN is
stored as a GitHub Actions secret, not in source code.

## One-time AWS setup

Create an IAM OIDC provider for `token.actions.githubusercontent.com`, then
create a role with a trust policy restricted to:

```text
repo:Dev-ASingh/cloud-native-ai-backend:ref:refs/heads/main
```

The exact trust-policy shape is checked in at
`infra/aws/github-actions-trust-policy.json`. Replace
`<AWS_ACCOUNT_ID>` before applying it. Do not broaden the repository, branch,
or audience conditions.

Attach only the permissions required by the two workflows:

- CloudFormation create/update/delete and describe operations for the
  `flagship-01-demo` stack.
- EC2 describe operations and the EC2 actions required by the stack.
- `budgets:CreateBudget`, `budgets:ViewBudget`, `budgets:ModifyBudget`, and
  `budgets:DeleteBudget`.
- `iam:PassRole` is not required because the template creates no IAM role.

The starting policy document is checked in at
`infra/aws/github-actions-role-policy.json`. Review it against the selected
AWS region and account before attaching it. The EC2 create and delete APIs
require wildcard resource scope, so the role trust policy and the fixed
CloudFormation stack name are important compensating controls.

Store the resulting role ARN in the repository's GitHub Actions secrets as
`AWS_DEMO_ROLE_ARN`. Store the AWS region as the non-sensitive repository
variable `AWS_DEMO_REGION`. Store the selected public VPC and subnet IDs as
`AWS_DEMO_VPC_ID` and `AWS_DEMO_SUBNET_ID`. Store your email as the repository
secret `AWS_DEMO_BUDGET_EMAIL`.

The workflows require GitHub authentication and manual dispatch. They never
accept AWS access keys and never put credentials in the frontend.

## Start and stop

Run **Start Demo** from GitHub Actions. The workflow deploys the stack, waits
for the API health endpoint, and prints the temporary URL.

Run **Stop Demo** after the demonstration. The workflow deletes the entire
CloudFormation stack and verifies that it no longer exists. The instance,
encrypted EBS volume, public IP, security group, and budget are stack-owned and
are removed with it.

AWS billing data can appear after teardown for usage that occurred before
deletion. A budget alert is a notification, not a spending cap. The workflow
therefore never claims a mathematically guaranteed zero bill.
