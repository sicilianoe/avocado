import StringIO
from django.test import TestCase
from django.db.models.query import QuerySet
from django.core.management import call_command
from avocado.meta.models import Definition, Concept, ConceptDefinition
from avocado.tests import models

from avocado.meta.exporters._base import BaseExporter
from avocado.meta.exporters._csv import CSVExporter
from avocado.meta.exporters._excel import ExcelExporter
from avocado.meta.exporters._sas import SasExporter
from avocado.meta.exporters._r import RExporter

class ExportTestCase(TestCase):
    fixtures = ['export_data.yaml']
    def setUp(self):
        call_command('avocado', 'sync', 'tests', verbosity=0)

        self.query = models.Employee.objects.all()

        first_name_def = Definition.objects.get_by_natural_key('tests',
                'employee', 'first_name')
        first_name_def.description = "First Name"
        last_name_def = Definition.objects.get_by_natural_key('tests',
                'employee', 'last_name')
        last_name_def.description = "Last Name"
        title_def = Definition.objects.get_by_natural_key('tests',
            'title', 'name')
        title_def.description = "Employee Title"
        salary_def = Definition.objects.get_by_natural_key('tests',
            'title', 'salary')
        salary_def.description = "Salary"
        is_manage_def = Definition.objects.get_by_natural_key('tests',
            'employee', 'is_manager')
        is_manage_def.description = "Is a Manager?"

        [x.save() for x in [first_name_def, last_name_def, title_def,
            salary_def, is_manage_def]]

        employee_concept = Concept()
        employee_concept.name="Employee"
        employee_concept.description = "A Single Employee"
        employee_concept.save()
#        title_concept = Concept()
#        title_concept.name="title"
#        title_concept.description = "A Single title"
#        title_concept.save()

        ConceptDefinition(concept=employee_concept,
                definition=title_def, order=4).save()
        ConceptDefinition(concept=employee_concept,
                definition=salary_def, order=5).save()
        ConceptDefinition(concept=employee_concept,
                definition=first_name_def, order=1).save()
        ConceptDefinition(concept=employee_concept,
                definition=last_name_def, order=2).save()
        ConceptDefinition(concept=employee_concept,
                definition=is_manage_def, order=3).save()



        self.concepts = [employee_concept,]

    def test_csv(self):
        buff = open('csv_export.csv', 'wb')
        test_export = CSVExporter(self.query, self.concepts)
        test_export.export(buff)

    def test_excel(self):
        test_export = ExcelExporter(self.query, self.concepts)
        test_export.export('excel_export.xlsx', virtual=False)

    def test_sas(self):
        test_export = SasExporter(self.query, self.concepts)
        buff  = 'sas_export.zip'
        test_export.export(buff)

    def test_r(self):
        test_export = RExporter(self.query, self.concepts)
        buff = 'r_export.zip'
        test_export.export(buff)
