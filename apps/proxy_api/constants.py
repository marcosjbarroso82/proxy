REQUEST_METHODS = [
    ('get', 'get'),
    ('post', 'post'),
    ('put', 'put'),
    ('patch', 'patch'),
    ('delete', 'delete'),
    ('options', 'options')
]

# TODO: find a way to set key and value as required
JSON_KEY_VALUE_SCHEMA = {
    "type": "array",
    "format": "table",
    "items": {
        "type": "object",
        "properties": {
            "key": {
                "type": "string", "propertyOrder": 1
            },
            "value": {
                "type": "string", "propertyOrder": 2
            },
            "debug_value": {
                "type": "string", "propertyOrder": 3
            }
        }
    }
}


JSON_KEY_ENV_VALUE_SCHEMA = {
    "type": "array",
    "format": "table",
    "items": {
        "type": "object",
        "properties": {
            "key": {
                "type": "string", "propertyOrder": 1
            },
            "type": {
                "type": "string", "propertyOrder": 2,
                "enum": [
                    "jinja"
                  ]
            },
            "value": {
                "type": "string", "propertyOrder": 3
            },
            "debug_value": {
                "type": "string", "propertyOrder": 4
            }
        }
    }
}


JSON_INTERFACE_SCHEMA = {
    "type": "array",
    "format": "table",
    "items": {
        "type": "object",
        "properties": {
            "key": {
                "type": "string", "propertyOrder": 1
            },
            "type": {
                "type": "string", "propertyOrder": 2,
                "enum": [
                        "jinja"
                      ]
            },
            "required":{
                "type": "boolean", "propertyOrder": 3,
                "format": "checkbox"
            }
        }
    }
}

JSON_OBJ_KEY_VALUE_SCHEMA = {
    "type": "object",
    "format": "grid",
        "properties": {
            "key": {
                "type": "string", "propertyOrder": 1, "required": True
            },
            "value": {
                "type": "string", "propertyOrder": 2, "required": True
            },
            "debug_value": {
                "type": "string", "propertyOrder": 3, "required": True
            }
        },
    "required": ["key", "value", "debug_value"],
    "defaultProperties": ["key", "value", "debug_value"]
    }


PRE_PORST_ACTIONS_JSON_SCHEMA = {
    "type": "array",
    "format": "table",
    "items": {
        "type": "object",
        "format": "grid",
        "properties": {
            "condition": {
                "type": "string", "propertyOrder": 1
            },
            "type": {
                "type": "string", "propertyOrder": 2,
                "enum": [
                        "update_state", "update_env", "update_temp"
                      ]
            },
            "key": {
                "type": "string", "propertyOrder": 3
            },
            "value": {
                "type": "string", "propertyOrder": 4
            }
        },
        "defaultProperties": ["condition", "type", "key", "value"]
    }
}