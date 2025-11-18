def _noop(*args, **kwargs):
    return None

class _TaskWrapper:
    def __call__(self, *args, **kwargs):
        return _noop(*args, **kwargs)
    def delay(self, *args, **kwargs):
        return _noop(*args, **kwargs)

enviar_email_notificacao = _TaskWrapper()
