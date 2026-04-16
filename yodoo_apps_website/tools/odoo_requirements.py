import shlex


def _parse_gitlab_ssh_url(url):
    url = url.strip()
    if url.startswith('git@'):
        url = url.split(':', 1)[-1]
    if url.endswith('.git'):
        url = url[:-4]
    return url


def parse_odoo_requirements(content):
    results = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        try:
            tokens = shlex.split(line)
        except ValueError:
            continue

        entry = None
        modules = []
        i = 0
        while i < len(tokens):
            token = tokens[i]
            if token == '--github' and i + 1 < len(tokens):
                i += 1
                val = tokens[i]
                if val.endswith('.git'):
                    val = val[:-4]
                parts = val.rsplit('/', 1)
                if len(parts) == 2:
                    entry = {
                        'type': 'github',
                        'owner': parts[0],
                        'repo': parts[1],
                    }
            elif token == '--oca' and i + 1 < len(tokens):
                i += 1
                repo = tokens[i]
                if repo.endswith('.git'):
                    repo = repo[:-4]
                entry = {
                    'type': 'github',
                    'owner': 'OCA',
                    'repo': repo,
                }
            elif token in ('-r', '--repo') and i + 1 < len(tokens):
                i += 1
                url = tokens[i]
                path = _parse_gitlab_ssh_url(url)
                entry = {
                    'type': 'gitlab',
                    'path': path,
                }
            elif token in ('-m', '--module') and i + 1 < len(tokens):
                i += 1
                modules.append(tokens[i])
            i += 1

        if entry:
            entry['modules'] = modules
            results.append(entry)

    return results
