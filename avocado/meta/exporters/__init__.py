from base import BaseExporter
from csv_e import CSVExporter
from excel import ExcelExporter
from sas import SasExporter
from r import RExporter

from avocado.utils import loader
## initialize the registry that contains all exporters
registry = loader.Registry()
registry.register(CSVExporter)
registry.register(ExcelExporterdt)
registry.register(SasExporter)
registry.register(RExporter)

loader.autodiscover('exporters')
