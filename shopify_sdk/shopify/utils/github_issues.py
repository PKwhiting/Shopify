import os
import requests

def create_github_issue(repo, title, body, labels=None):
    """
    Create a GitHub issue in the specified repo using the REST API.
    Requires a GitHub token in the GITHUB_TOKEN environment variable.
    """
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        raise RuntimeError('GITHUB_TOKEN environment variable not set')
    url = f'https://api.github.com/repos/{repo}/issues'
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    data = {
        'title': title,
        'body': body
    }
    if labels:
        data['labels'] = labels
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        return response.json()['html_url']
    else:
        raise RuntimeError(f'GitHub issue creation failed: {response.status_code} {response.text}')
