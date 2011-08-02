import csv
from avocado.meta.exporters._base import BaseExporter

class CSVExporter(BaseExporter):
    "CSV Exporter"

    preferred_formats = ('string',)

    def export(self, buff):
        """ Export to csv method
        `buff` - file-like object that is being written to
        """

        headers = []
        table_gen = self.read()

        writer = csv.writer(buff, quoting=csv.QUOTE_MINIMAL)

        for i, row_gen in enumerate(table_gen):
            row = []
            for data in row_gen:
                values = data.values()
                if i == 0:
                    headers.extend(data.keys())

                for value in values:
                    row.append(value['value'])

            if i == 0:
                writer.writerow(headers)
            writer.writerow(row)
            row = []

        return buff

