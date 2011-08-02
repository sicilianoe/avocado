from zipfile import ZipFile
from StringIO import StringIO
from string import punctuation

from avocado.meta.exporters._base import BaseExporter
from avocado.meta.exporters._csv import CSVExporter

class RExporter(BaseExporter):
    "R Exporter. Creates R script file"

    preferred_formats = ('coded', 'number', 'string')

    def rify_name(self, name):
        punc = punctuation.replace("_", '')
        name = str(name).translate(None, punc)
        name = name.replace(" ", "_")
        words = name.split('_')
        for i, w in enumerate(words):
            if i == 0:
                name = w.lower()
                continue
            name += w.capitalize()
        if name[0].isdigit():
            name = "_" + name

        return name

    def r_coded(self, name, definition):
        """
        If the definition can be coded return the
        r factor and level for it.
        """
        d = definition
        factor = ""
        level = ""

        data_field = "data${0}".format(name)
        factor += "{0}.factor = factor({0},levels=c(".format(data_field)
        level += "levels({0}.factor)=c(".format(data_field)
        for i, (val, code) in enumerate(d.coded_values):
            factor += str(code)
            level += "\"" + str(val) + "\""
            if i == len(d.coded_values)-1:
                factor += "))\n"
                level += ")\n"
                continue
            factor += " ,"
            level += " ,"

        return factor, level

    def export(self, buff):
        r_zip = ZipFile(buff, 'w')
        r_file = StringIO()

        r_file.write("#Read Data\ndata=read.csv('r_data.csv')\n\n")
        factors = ""      # fi.eld names
        levels = ""       # value dictionaries
        labels = ""       # data labels

        for c in self.concepts:
            cdefs = c.conceptdefinitions.select_related('definition')
            for cdef in cdefs:
                d = cdef.definition
                name = self.rify_name(d.field_name)
                labels += "attr(data${0}, 'label') = \"{1}\"\n".format(
                        name, d.description)

                if d.coded_values:
                    codes = self.r_coded(name, d)
                    factors += codes[0]
                    levels += codes[1]

        # Write out the r file to the given r_fileer
        r_file.write("#Setting Labels\n")
        r_file.write(labels + "\n")

        r_file.write("#Setting Factors\n")
        r_file.write(factors + "\n")

        r_file.write("#Setting Levels\n")
        r_file.write(levels + "\n")

        r_zip.writestr('r_export.R', r_file.getvalue())
        r_file.close()

        # WRITE CSV 
        csv_file = StringIO()
        csv_export = CSVExporter(self.queryset, self.concepts)
        csv_export.preferred_formats = self.preferred_formats
        r_zip.writestr('r_data.csv', csv_export.export(csv_file).getvalue())
        csv_file.close()

        r_zip.close()
        return r_zip

