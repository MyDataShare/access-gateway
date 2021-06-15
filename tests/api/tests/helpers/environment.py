from os import environ

required_run_env_vars = [
    'AGW',
    'MDS',
    'IDPMOCK',
]

run_env_vars = {
    "test": {
        "AGW": "http://localhost:8199",
        "MDS": "http://localhost:8099",
        "IDPMOCK": "http://localhost:19090",
    }
}


def get_run_env_vars():
    run_env = environ['RUN_ENV'] if 'RUN_ENV' in environ else 'test'
    if run_env not in run_env_vars:
        raise Exception("Unknown RUN_ENV: '%s'" % run_env)

    v = {**run_env_vars[run_env]}

    for i in required_run_env_vars:
        if i in environ:
            v[i] = environ[i]
        if i not in v:
            raise Exception("Required run environment variable '%s' not found!" % i)

    return v
