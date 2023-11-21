from enum import Enum
class PresignedURLMethod(str, Enum):
    GET_OBJECT = 'get_object'
    PUT_OBJECT = 'put_object'