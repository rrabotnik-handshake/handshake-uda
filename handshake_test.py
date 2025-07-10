import unittest
from gen.python.handshake.v1 import handshake_domain_pb2
from datetime import datetime, timedelta
from protovalidate import ValidationError
from handshake import validateHandshake


class HandshakeTest(unittest.TestCase):
    def test_valid_request(self):
        message = handshake_domain_pb2.Employer()
        message.employer_name = "B"

        with self.assertRaises(ValidationError) as context:
            validateHandshake(message)

        validationErr = context.exception
        self.assertEqual(1, len(validationErr.violations))

        for violation in validationErr.violations:
            print(violation.proto.message)
