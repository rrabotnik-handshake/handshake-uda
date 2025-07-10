from buf.validate import validate_pb2 as _validate_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Jobtype(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    JOBTYPE_UNSPECIFIED: _ClassVar[Jobtype]
    JOBTYPE_FULL_TIME: _ClassVar[Jobtype]
    JOBTYPE_PART_TIME: _ClassVar[Jobtype]
    JOBTYPE_INTERNSHIP: _ClassVar[Jobtype]
    JOBTYPE_CONTRACT: _ClassVar[Jobtype]

class Applicationstatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    APPLICATIONSTATUS_UNSPECIFIED: _ClassVar[Applicationstatus]
    APPLICATIONSTATUS_PENDING: _ClassVar[Applicationstatus]
    APPLICATIONSTATUS_ACCEPTED: _ClassVar[Applicationstatus]
    APPLICATIONSTATUS_REJECTED: _ClassVar[Applicationstatus]
JOBTYPE_UNSPECIFIED: Jobtype
JOBTYPE_FULL_TIME: Jobtype
JOBTYPE_PART_TIME: Jobtype
JOBTYPE_INTERNSHIP: Jobtype
JOBTYPE_CONTRACT: Jobtype
APPLICATIONSTATUS_UNSPECIFIED: Applicationstatus
APPLICATIONSTATUS_PENDING: Applicationstatus
APPLICATIONSTATUS_ACCEPTED: Applicationstatus
APPLICATIONSTATUS_REJECTED: Applicationstatus

class Application(_message.Message):
    __slots__ = ("applied_date",)
    APPLIED_DATE_FIELD_NUMBER: _ClassVar[int]
    applied_date: str
    def __init__(self, applied_date: _Optional[str] = ...) -> None: ...

class Employer(_message.Message):
    __slots__ = ("posted_job",)
    POSTED_JOB_FIELD_NUMBER: _ClassVar[int]
    posted_job: _containers.RepeatedCompositeFieldContainer[Job]
    def __init__(self, posted_job: _Optional[_Iterable[_Union[Job, _Mapping]]] = ...) -> None: ...

class Job(_message.Message):
    __slots__ = ("job_type",)
    JOB_TYPE_FIELD_NUMBER: _ClassVar[int]
    job_type: str
    def __init__(self, job_type: _Optional[str] = ...) -> None: ...

class JobSeeker(_message.Message):
    __slots__ = ("email", "attended_school")
    EMAIL_FIELD_NUMBER: _ClassVar[int]
    ATTENDED_SCHOOL_FIELD_NUMBER: _ClassVar[int]
    email: str
    attended_school: _containers.RepeatedCompositeFieldContainer[School]
    def __init__(self, email: _Optional[str] = ..., attended_school: _Optional[_Iterable[_Union[School, _Mapping]]] = ...) -> None: ...

class School(_message.Message):
    __slots__ = ("school_location",)
    SCHOOL_LOCATION_FIELD_NUMBER: _ClassVar[int]
    school_location: str
    def __init__(self, school_location: _Optional[str] = ...) -> None: ...

class Skill(_message.Message):
    __slots__ = ("skill_category",)
    SKILL_CATEGORY_FIELD_NUMBER: _ClassVar[int]
    skill_category: str
    def __init__(self, skill_category: _Optional[str] = ...) -> None: ...
