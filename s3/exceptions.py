class PdfServiceBaseError(Exception):
    def __init__(self, status_code=None, message=None):
        super().__init__(message)
        self.__status_code = status_code
        self.__message = message

    @property
    def status_code(self):
        return self.__status_code

    @property
    def message(self):
        return self.__message


class PdfServiceInternalError(PdfServiceBaseError):
    pass
