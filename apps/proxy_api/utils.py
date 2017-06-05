from jinja2 import Environment
import json


def replace_jinga_tags(text, params):
    env = Environment(extensions=['jinja2.ext.with_', 'jinja2.ext.do'])
    return env.from_string(text).render(**params)

def replace_jinga_tags_in_dict(payload, params):
    text = json.dumps(payload)
    result = replace_jinga_tags(text, params)
    return json.loads(result)