# GitHub Secrets Configuration

This document describes the required secrets for the CI/CD pipeline to work properly.

## Required Secrets

### 1. BOT_TOKEN
- **Description**: Telegram bot token from @BotFather
- **Required for**: Testing, building, and deployment
- **How to get**: 
  1. Message @BotFather on Telegram
  2. Use `/newbot` command
  3. Follow the instructions to create a bot
  4. Copy the token provided

### 2. DOCKER_USERNAME
- **Description**: Docker Hub username for pushing images
- **Required for**: Building and pushing Docker images
- **How to get**: 
  1. Create account at https://hub.docker.com
  2. Use your Docker Hub username

### 3. DOCKER_PASSWORD
- **Description**: Docker Hub password or access token
- **Required for**: Building and pushing Docker images
- **How to get**: 
  1. Use your Docker Hub password, or
  2. Create an access token in Docker Hub settings
  3. Use the access token as password (recommended)

### 4. SLACK_WEBHOOK_URL (Optional)
- **Description**: Slack webhook URL for notifications
- **Required for**: Slack notifications on deployment status
- **How to get**:
  1. Go to your Slack workspace
  2. Create a new app at https://api.slack.com/apps
  3. Enable Incoming Webhooks
  4. Create a webhook for your desired channel
  5. Copy the webhook URL

## How to Add Secrets

1. Go to your GitHub repository
2. Click on **Settings** tab
3. In the left sidebar, click **Secrets and variables** > **Actions**
4. Click **New repository secret**
5. Enter the secret name and value
6. Click **Add secret**

## Environment-Specific Secrets

### Staging Environment
- `STAGING_DOMAIN`: Domain for staging environment
- `STAGING_SSL_EMAIL`: Email for SSL certificates in staging

### Production Environment
- `PRODUCTION_DOMAIN`: Domain for production environment
- `PRODUCTION_SSL_EMAIL`: Email for SSL certificates in production

## Security Notes

- Never commit secrets to the repository
- Use access tokens instead of passwords when possible
- Regularly rotate secrets and tokens
- Use different secrets for different environments
- Consider using GitHub Environments for additional security

## Testing Secrets

You can test if your secrets are properly configured by:

1. Running the CI pipeline manually
2. Checking the workflow logs for any authentication errors
3. Verifying that Docker images are pushed successfully
4. Confirming that Slack notifications are received (if configured)

## Troubleshooting

### Common Issues

1. **Docker login failed**
   - Check DOCKER_USERNAME and DOCKER_PASSWORD
   - Ensure the Docker Hub account has push permissions

2. **Bot token invalid**
   - Verify BOT_TOKEN is correct
   - Check if the bot is still active

3. **Slack notifications not working**
   - Verify SLACK_WEBHOOK_URL is correct
   - Check if the webhook is still active
   - Ensure the channel exists and the bot has access

4. **SSL certificate issues**
   - Check if STAGING_SSL_EMAIL and PRODUCTION_SSL_EMAIL are set
   - Verify domain names are correct