"""Application-specific exceptions, so callers can catch a precise failure
instead of a bare ValueError/Exception."""


class TaxiAppError(Exception):
    """Base class for all application-specific errors."""


class SchemaError(TaxiAppError):
    """Raised when a batch is missing columns the pipeline requires."""


class EmptySourceError(TaxiAppError):
    """Raised when a data source produces no usable batches at all."""
