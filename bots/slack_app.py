import os
from slack_bolt import App

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")
app = App(token=SLACK_BOT_TOKEN, signing_secret=SLACK_SIGNING_SECRET)

@app.event("app_mention")
def handle_mention(body, say):
    say("ERP-BERHAN Slack bot online.")

if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))


