# GitLab Token Rotator

GitLab access token rotation script.

# How it works

The script will run through all available groups and projects and check the expiration date of access tokens. If the token expires in less than 30 days, the script rotates it using the GitlLab API, generates a debug message and sends it to the Telegram bot.

# Dependencies

The script requires the installation of the library [python-gitlab](https://github.com/python-gitlab/python-gitlab) to work.

You can install dependencies with the command:

~~~
pip3 install -r requirements.txt 
~~~
