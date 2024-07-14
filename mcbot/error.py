class UnexpectedUI(Exception):
    def __init__(self, expect):
        self.expect = expect


class UserInterrupt(Exception):
    pass


class ConfigError(Exception):
    def __init__(self, message):
        self.message = message


class ReturnMainUIFail(Exception):
    pass


class GlobalVar:
    stop_main = False
