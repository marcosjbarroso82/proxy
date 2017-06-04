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