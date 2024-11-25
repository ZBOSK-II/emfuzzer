def decode_code(octet):
    clazz = (octet & 0b11100000) >> 5
    code = octet & 0xB00011111
    return clazz, code


def code_short_string(code):
    return f"{code[0]},{code[1]:02}"


__MESSAGES = {
    1: (
        "REQUEST",
        {
            0: "EMPTY",
            1: "GET",
            2: "POST",
            3: "PUT",
            4: "DELETE",
            5: "FETCH",
            6: "PATCH",
            7: "iPATCH",
        },
    ),
    2: (
        "SUCCESS",
        {
            1: "Created",
            2: "Deleted",
            3: "Valid",
            4: "Changed",
            5: "Content",
            31: "Continue",
        },
    ),
    4: (
        "CLIENT ERROR",
        {
            0: "Bad Request",
            1: "Unauthorized",
            2: "Bad Option",
            3: "Forbidden",
            4: "Not Found",
            5: "Method Not Allowed",
            6: "Not Acceptable",
            8: "Request Entity Incomplete",
            9: "Conflict",
            12: "Precondition Failed",
            13: "Request Entity Too Large",
            15: "Unsupported Content-Format",
        },
    ),
    5: (
        "SERVER ERROR",
        {
            0: "Internal server error",
            1: "Not implemented",
            2: "Bad gateway",
            3: "Service unavailable",
            4: "Gateway timeout",
            5: "Proxying not supported",
        },
    ),
    7: (
        "SIGNALING",
        {
            0: "Unassigned",
            1: "CSM",
            2: "Ping",
            3: "Pong",
            4: "Release",
            5: "Abort",
        },
    ),
}


def code_message(code):
    class_message, code_dict = __MESSAGES.get(code[0], ("UNKNOWN", {}))
    code_message = code_dict.get(code[1], "-unknown-")
    return f"{class_message}: {code_message}"


def code_to_string(code):
    return f"{code_short_string(code)} ({code_message(code)})"


def code_reports_success(code):
    return code[0] == 2
