


class PollVoteException(Exception):

    def __init__(self, *args, **kwargs):
        self.message = kwargs.get('message', "")
        self.error_code = kwargs.get('error_code', 2)

    def to_dict(self):
        return {'message': self.message, 'code': self.error_code}
