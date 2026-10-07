"""
Abstract interfaces for the taxi demand pipeline.

This module is the concrete fix for the biggest gap in the original
submission: the report *described* SOLID principles (particularly DIP,
ISP and LSP) in prose, but no actual abstraction existed anywhere in the
code for TaxiDemandPipeline to depend on - its constructor accepted
untyped, duck-typed objects. That made "dependency injection" true but
"Dependency Inversion Principle" only aspirational, since DIP specifically
means depending on an abstraction, not just on "some object passed in".

Each interface below is deliberately narrow (Interface Segregation): a
DataSource never has to implement write(), a ReportWriter never has to
implement batches(). Two concrete implementations of DataSource and two
of ReportWriter exist (see datasource.py / writer.py) and are proven
interchangeable by tests/test_liskov_substitution.py - this is what turns
the Liskov Substitution claim from a hypothetical ("a future data source
could...") into something actually demonstrated.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Iterator
import pandas as pd


class DataSource(ABC):
    """Contract for anything that can yield batches of raw trip records."""

    @abstractmethod
    def batches(self) -> Iterator[pd.DataFrame]:
        raise NotImplementedError


class Validator(ABC):
    """Contract for anything that can validate/clean a batch of records."""

    @abstractmethod
    def validate(self, frame: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError


class Transformer(ABC):
    """Contract for anything that can derive analysis-ready fields."""

    @abstractmethod
    def transform(self, frame: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError


class Analytics(ABC):
    """Contract for anything that can turn analysis-ready records into
    the client's demand summaries."""

    @abstractmethod
    def hourly(self, frame: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError

    @abstractmethod
    def by_zone(self, frame: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError

    @abstractmethod
    def summary(self, hourly: pd.DataFrame, zones: pd.DataFrame) -> Dict:
        raise NotImplementedError


class ReportWriter(ABC):
    """Contract for anything that can persist the final report outputs."""

    @abstractmethod
    def write(self, hourly: pd.DataFrame, zones: pd.DataFrame, summary: Dict) -> None:
        raise NotImplementedError
