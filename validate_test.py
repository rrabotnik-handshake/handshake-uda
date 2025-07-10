import unittest
from protovalidate import Validator, ValidationError
from gen.python.handshake.v1 import handshake_domain_pb2
from rich.console import Console
from rich.table import Table

console = Console()


def print_violations(reason: str, exc: ValidationError):
    console.print(f"\n❌ Validation failed: {reason}", style="bold red")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Field", style="yellow")
    table.add_column("Invalid Value", style="cyan")
    table.add_column("Violated Rule", style="green")

    for v in exc.violations:
        # Extract field path
        field_msg = getattr(v.proto, "field", None)
        if field_msg:
            try:
                field_path_parts = [
                    e.field_name for e in field_msg.elements if e.field_name]
                field = ".".join(
                    field_path_parts) if field_path_parts else "(unknown)"
            except Exception:
                field = "(unknown)"
        else:
            field = "(unknown)"

        val = repr(getattr(v, "field_value", ""))

        # Extract rule ID (fallback to rule_value if not found)
        try:
            rule_id = v.proto.rule.id if hasattr(v.proto, "rule") else None
            rule_str = rule_id if rule_id else repr(v.rule_value)
        except Exception:
            rule_str = repr(v.rule_value)

        table.add_row(field, val, rule_str)

    console.print(table)


class TestHandshakeValidation(unittest.TestCase):

    def setUp(self):
        self.validator = Validator()

    def test_valid_employer(self):
        employer = handshake_domain_pb2.Employer(
            employer_name="Valid Corp",
            industry="Technology"
        )
        try:
            self.validator.validate(employer)
        except ValidationError as e:
            self.fail(f"Validation unexpectedly failed: {e}")

    def test_invalid_employer_name_too_short(self):
        employer = handshake_domain_pb2.Employer(
            employer_name="A"  # Too short
        )
        with self.assertRaises(ValidationError) as ctx:
            self.validator.validate(employer)
        print_violations("Invalid employer_name (too short)", ctx.exception)

    def test_valid_jobseeker(self):
        js = handshake_domain_pb2.JobSeeker(
            email="test@example.com",
            full_name="Alice Johnson",
            graduation_year=2025
        )
        try:
            self.validator.validate(js)
        except ValidationError as e:
            self.fail(f"Validation unexpectedly failed: {e}")

    def test_invalid_jobseeker_email_too_short(self):
        js = handshake_domain_pb2.JobSeeker(
            email="t@x",
            full_name="Bob",
            graduation_year=2025
        )
        with self.assertRaises(ValidationError) as ctx:
            self.validator.validate(js)
        print_violations("Invalid email (too short)", ctx.exception)

    def test_invalid_graduation_year_too_early(self):
        js = handshake_domain_pb2.JobSeeker(
            email="test@example.com",
            full_name="John Doe",
            graduation_year=1990  # Too early
        )
        with self.assertRaises(ValidationError) as ctx:
            self.validator.validate(js)
        print_violations("Graduation year too early", ctx.exception)

    def test_invalid_job_description_too_short(self):
        job = handshake_domain_pb2.Job(
            title="X",
            description="Short"
        )
        with self.assertRaises(ValidationError) as ctx:
            self.validator.validate(job)
        print_violations("Job description too short", ctx.exception)


if __name__ == "__main__":
    unittest.main()
