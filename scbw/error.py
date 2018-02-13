class ScbwException(Exception):
    pass


class GameException(ScbwException):
    pass


class PlayerException(ScbwException):
    pass


class DockerException(ScbwException):
    pass


class ContainerException(DockerException):
    pass


class RealtimeOutedException(ContainerException):
    pass
