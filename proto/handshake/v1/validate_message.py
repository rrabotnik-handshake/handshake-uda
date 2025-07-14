
import protovalidate


def validateMessage(request):
    protovalidate.validate(request)
