# Deploy

To deploy this project, follow these steps:

## GitLab Account Setup

1. **Create a bot account**
    - Create a new GitLab account for the bot

2. **Generate a Personal Access Token for the bot account**
    - Go to your GitLab account settings
    - Go to `Access Tokens` in the left sidebar
    - Create a new access token with the following scopes:
        - `api`
    - Copy the generated token as `GITLAB_PERSONAL_ACCESS_TOKEN`

    ![Generate Personal Access Token](/doc/img/gitlab_pat.png)

## Ollama Setup

1. **Deploy ollama**
    - Install [ollama](https://ollama.com/)
    - Run the ollama and get the API URL, e.g., `http://localhost:11434`

2. **Fetch an LLM model**
    - Choose a model name, e.g., `deepseek-r1:70b` as `LLM_MODEL_NAME`
    - Download the model from the ollama API, `ollama run deepseek-r1:70b`

## Server Setup

1. **Clone this repo**

    ```bash
    git clone <this-repo>
    ```

2. **Copy `config/.env.example` to `config/.env` and fill in the required information**

    ```bash
    cp config/.env.example config/.env
    ```

    | Variable                        | Description                                      | Example Value                                  |
    |---------------------------------|--------------------------------------------------|------------------------------------------------|
    | `GITLAB_SERVER`                 | URL of your GitLab server                        | `https://gitlab.com`            |
    | `GITLAB_PERSONAL_ACCESS_TOKEN`  | Personal access token for GitLab bot account                 | `xxxxxxx`                         |
    | `GITLAB_WEBHOOK_VERIFY_TOKEN`   | **(Optional)** Token to verify GitLab webhook, generate it by yourself                   | `yyyyyyyy`                             |
    | `LLM_API_BASE`                  | Base URL for the ollama API                         | `http://localhost:11434`                          |
    | `LLM_MODEL_NAME`                | Name of the LLM model                            | `deepseek-r1:70b`                              |
    | `LLM_HTTP_PROXY`                | **(Optional)** HTTP proxy for accessing the LLM API             | `http://<username>:<password>@<host>:<port>`    |


3. **Change the deploy configuration in `docker-compose.yml`**
    
    - Change the `ports` in the `app` service to fit your server configuration
    - Change the `GUNICORN_WORKERS` and `GUNICORN_THREADS` in the `app` if needed

4. **Start the server using Docker Compose**

    ```bash
    docker-compose up -d
    ```

5. **Expose the server to the internet**

    - Make sure your server is accessible by the GitLab webhook
    - Check the server status by visiting `http(s)://<your-server-ip>:<port>/git/ping`

## GitLab Webhook Setup

1. **Add the bot account as a member of your project**
    - Go to your project
    - Go to `Manage` - `Members` in the left sidebar
    - Add the bot account as a member with the `Developer` role
 

2. **Set up GitLab webhook**
    - Go to your project settings
    - Go to `Webhooks` in the left sidebar
    - Add a new webhook with the following settings:
        - URL: `http(s)://<your-server-ip>:<port>/git/webhook`
        - Secret Token: `<GITLAB_WEBHOOK_VERIFY_TOKEN>`
        - Trigger: `Merge request events`
        - Disable SSL verification if needed

    ![GitLab Webhook](/doc/img/gitlab_webhook.png)

## Trigger the Bot

1. **Create a new merge request**
    - Create a new merge request in your project
    - Add the bot as a reviewer
    - Make sure there is no `CrBot WIP`, `CrBot Done`, or `CrBot Failed` label in the merge request
    - Make sure the draft status is off

2. **Check the bot action**
    - You should see the bot action in the merge request
        - `CrBot WIP` label: The bot is working on the review
        - Comment, `CrBot Done` label: The bot has finished the review
        - `CrBot Failed` label: The bot failed to review the code (e.g., LLM API error)

    ![Bot Action](/doc/img/cr_bot.png)

