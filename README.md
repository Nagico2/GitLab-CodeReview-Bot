# Automated Private LLM Code Review for Gitlab

A project using LLM to empower Code Review on Gitlab. 

> Modify from [mimo-x/Code-Review-GPT-Gitlab](https://github.com/mimo-x/Code-Review-GPT-Gitlab), focusing on the private LLM API using `ollama` and providing a better user experience. 

## Usage 📖

To use this project, you need:

- Deploy LLM locally using ollama (or other public/private API)
- A GitLab account as a bot
- A server accessible by GitLab webhook

### Quick Start

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
    | `GITLAB_WEBHOOK_VERIFY_TOKEN`   | **(Optional)** Token to verify GitLab webhook                   | `yyyyyyyy`                             |
    | `LLM_API_BASE`                  | Base URL for the ollama API                         | `http://localhost:11434`                          |
    | `LLM_MODEL_NAME`                | Name of the LLM model                            | `deepseek-r1:70b`                              |
    | `LLM_HTTP_PROXY`                | **(Optional)** HTTP proxy for accessing the LLM API             | `http://<username>:<password>@<host>:<port>`    |


3. **Start the server using Docker Compose**

    ```bash
    docker-compose up -d
    ```

4. **Set up GitLab webhook**
    - Go to your project settings
    - Go to `Webhooks` in the left sidebar
    - Add a new webhook with the following settings:
        - URL: `http(s)://<your-server-ip>:<port>/git/webhook`
        - Secret Token: `<GITLAB_WEBHOOK_VERIFY_TOKEN>`
        - Trigger: `Merge request events`

5. **Test the setup**
    - Create a new merge request in your project
    - Add the bot as a reviewer, make sure there is no `CrBot WIP`, `CrBot Done`, or `CrBot Failed`  label in the merge request
    - You should see the bot action in the merge request
        - `CrBot WIP` label: The bot is working on the review
        - Comment, `CrBot Done` label: The bot has finished the review
        - `CrBot Failed` label: The bot failed to review the code (e.g., LLM API error)

## Result Preview 🌈

![Preview](/doc/img/cr_bot.png)

## More Information 📚

- [Documentation](/doc/)