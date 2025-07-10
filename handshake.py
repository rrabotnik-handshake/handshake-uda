import protovalidate


def validateHandshake(request):
    protovalidate.validate(request)
