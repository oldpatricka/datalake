from copy import deepcopy
from dateutil.parser import parse as dateparse
from datetime import datetime
from pytz import utc
from uuid import uuid4


class InvalidDatalakeMetadata(Exception):
    pass


class UnsupportedDatalakeMetadataVersion(Exception):
    pass

_EPOCH = datetime.fromtimestamp(0, utc)

class Metadata(dict):

    _VERSION = 0

    def __init__(self, *args, **kwargs):
        '''prepare compliant, normalized metadata from inputs

        Args:

            kwargs: key-value pairs for metadata fields.

        Raises:

            InvalidDatalakeMetadata if required fields are missing and cannot
            be inferred.
        '''
        # we want to own all of our bits so we can normalize them without
        # altering the caller's data unexpectedly. So deepcopy.
        args = deepcopy(args)
        kwargs = deepcopy(kwargs)
        super(Metadata, self).__init__(*args, **kwargs)
        self._ensure_id()
        self._ensure_version()
        self._ensure_work_id()
        self._validate()
        self._normalize_dates()

    def _ensure_id(self):
        if 'id' not in self:
            self['id'] = uuid4().hex

    def _ensure_version(self):
        if 'version' not in self:
            self['version'] = self._VERSION

    def _ensure_work_id(self):
        if 'work_id' not in self:
            self['work_id'] = None

    def _validate(self):
        self._validate_required_fields()
        self._validate_version()

    _REQUIRED_METADATA_FIELDS = ['version', 'start', 'where', 'what', 'id',
                                 'hash']

    def _validate_required_fields(self):
        for f in self._REQUIRED_METADATA_FIELDS:
            if self.get(f) is None:
                msg = '"{}" is a require field'.format(f)
                raise InvalidDatalakeMetadata(msg)

    def _validate_version(self):
        v = self['version']
        if v != self._VERSION:
            msg = ('Found version {}. '
                   'Only {} is supported').format(v, self._VERSION)
            raise UnsupportedDatalakeMetadataVersion(msg)

    def _normalize_dates(self):
        for d in ['start', 'end']:
            if d in self:
                self[d] = self._normalize_date(self[d])

    @staticmethod
    def _normalize_date(date):
        if type(date) is int:
            return date
        elif type(date) is float:
            return int(date * 1000.0)
        else:
            return Metadata._normalize_date_from_string(date)

    @staticmethod
    def _normalize_date_from_string(date):
        try:
            d = dateparse(date)
            if not d.tzinfo:
                d = d.replace(tzinfo=utc)
            return Metadata._datetime_to_milliseconds(d)
        except ValueError:
            msg = 'could not parse a date from {}'.format(date)
            raise InvalidDatalakeMetadata(msg)

    @staticmethod
    def _datetime_to_milliseconds(d):
        delta = d - _EPOCH
        return int(delta.total_seconds()*1000.0)
