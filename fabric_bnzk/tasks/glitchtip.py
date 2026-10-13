import requests
from fabric.api import env, task
from fabric.utils import puts

from .utils import load_remote_env_vars


def _glitchtip_request(method, path, params={}, payload={}):
    if not (env.glitchtip_api_token and env.glitchtip_url):
        return
    url = env.glitchtip_url + path
    headers = {"Authorization": "Bearer " + env.glitchtip_api_token}
    response = requests.request(
        method, url, headers=headers, params=params, json=payload
    )
    response.raise_for_status()
    return response.json()


@task
def setup_glitchtip():
    # check project there?
    path = f"api/0/projects/bnzk/{env.project_name}/keys/"
    keys = _glitchtip_request("get", path)
    if not len(keys):
        puts("Project not found. Aborting.")
        return
    # alerts
    _check_create_alerts(env.project_name)
    _check_create_uptime_monitor(env.project_name)


@task
def setup_all_glitchtip_alerts():
    path = "api/0/projects/"
    projects = _glitchtip_request("get", path)
    for proj in projects:
        puts(f"setup alerts for {proj['name']}")
        _check_create_alerts(proj["name"])
        puts("---")


def _check_create_uptime_monitor(account_slug):
    if not getattr(env, "env_file", None):
        puts("WARNING: no env file, no monitor check!")
        return
    import environ

    path = f"api/0/projects/bnzk/{account_slug}/monitors/"
    monitors = _glitchtip_request("get", path)
    needs_monitor = True
    load_remote_env_vars()
    e = environ.Env()
    required_url = e.get("ALLOWED_HOSTS")
    print(required_url)
    for monitor in monitors:
        if monitor["url"] == required_url:
            needs_monitor = False
    print(needs_monitor)


def _check_create_alerts(account_slug):
    # get alerts
    path = f"api/0/projects/bnzk/{account_slug}/alerts/"
    alerts = _glitchtip_request("get", path)
    needs_email = True
    needs_webhook = True
    for alert in alerts:
        for recipient in alert["alertRecipients"]:
            if (
                recipient["recipientType"] == "email"
                and alert["timespanMinutes"] == 1
                and alert["quantity"] == 1
                and alert["uptime"]
            ):
                needs_email = False
        for recipient in alert["alertRecipients"]:
            if recipient["recipientType"] == "webhook" and alert["uptime"]:
                needs_webhook = False
    # add alerts?
    path = f"api/0/projects/bnzk/{account_slug}/alerts/"
    if needs_email:
        payload = {
            "alertRecipients": [
                {
                    "recipientType": "email",
                    "url": env.glitchtip_webhook_url,
                }
            ],
            "quantity": 1,
            "timespanMinutes": 1,
            "uptime": True,
        }
        _glitchtip_request("post", path, payload=payload)
        puts("Email alert created.")
    else:
        puts("Email alert already exists.")
    if needs_webhook and env.glitchtip_webhook_url:
        payload = {
            "alertRecipients": [
                {
                    "recipientType": "webhook",
                    "url": env.glitchtip_webhook_url,
                }
            ],
            "quantity": 10,
            "timespanMinutes": 1,
            "uptime": True,
        }
        _glitchtip_request("post", path, payload=payload)
        puts("Webhook alert created.")
    else:
        puts("Webhook alert already exists.")
