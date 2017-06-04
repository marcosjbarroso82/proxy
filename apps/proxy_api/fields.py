from django.db.models import TextField


class JSONTextField(TextField):
    def __init__(self, *args, **kwargs):
        self.json_schema = kwargs.pop('json_schema', None)
        super().__init__(*args, **kwargs)
