class QueryServiceError(Exception):
    code = "QUERY_ERROR"

class InvalidViewError(QueryServiceError):
    code = "INVALID_VIEW"

class InvalidFieldError(QueryServiceError):
    code = "INVALID_FIELD"
