from zipfile import ZipFile
from StringIO import StringIO
from string import punctuation

from avocado.meta.exporters._base import BaseExporter
from avocado.meta.exporters._csv import CSVExporter


class SasExporter(BaseExporter):
    "SAS Exporter"

    preferred_formats = ('coded', 'number', 'string')
    num_lg_names = 0

    # informat/format mapping for all datatypes except strings
    sas_informat_map = {'number': "best32.", 'date': "MMDDYYw.",
                'boolean': "best32.", 'datetime': "DATETIMEw.d",
                'time': "TIMEw.d"}
    sas_format_map = {'number': "best12.", 'date': "MMDDYYw.",
                'boolean': "best12.", 'datatime': "DATETIMEw.d",
                'time': "TIMEw.d"}

    def sassify_name(self, name):
        punc = punctuation.replace('_', '')
        name = str(name).translate(None, punc)
        name = name.replace(' ', '_')
        if name[0].isdigit():
            name = "_" + name
        if len(name) < 30:
            return name
        else:
            self.num_lg_names += 1
            sas_name = name[:20]
            sas_name += "_lg_{0}".format(self.num_lg_names)
            return sas_name

    def sas_forms(self, sas_name, definition):
        """
        This method creates the sas format and informat lists for
        every variable.
        """
        d = definition

        # get the informat/format
        if d.datatype == 'string':
            informat = s_format = "${0}.".format(d.field.max_length)
        else:
            s_format = self.sas_format_map[d.datatype]
            informat = self.sas_informat_map[d.datatype]
        sas_informat = '\tinformat {0:<10}{1:>10};\n'.format(
                sas_name, informat)
        sas_format = '\tformat {0:<10}{1:>10};\n'.format(
                sas_name, s_format)

        return sas_format, sas_informat

    def sas_coded(self, name, definition):
        """
        If definition can be coded return the value dictionary
        and the format name for the dictionary
        """
        d = definition

        value_format = '\tformat {0} {0}_f.;\n'.format(name)
        value = '\tvalue {0}_f '.format(name)

        for i, (val, code) in enumerate(d.coded_values):
            value += "%d=\"%s\" "%(code, val)
            if (i != len(d.coded_values)-1 and (i % 2) == 1 and i != 0):
                value += "\n\t\t"
        value += ";\n"

        return value_format, value

    def export(self, buff):
        sas_zip = ZipFile(buff, 'w')
        sas_file = StringIO()

        sas_file.write("data SAS_EXPORT;\n")
        sas_file.write("INFILE 'sas_data.csv' TRUNCOVER DSD firstobs=2;\n")

        inputs = ""          # field names in sas format
        values = ""          # sas value dictionaries
        value_formats = ""   # labels for value dictionary
        labels = ""          # labels the field names
        informats = ""      # sas informats for all fields
        formats = ""        # sas formats for all fields


        for c in self.concepts:
            cdefs = c.conceptdefinitions.select_related('definition')
            for cdef in cdefs:
                d = cdef.definition
                name = self.sassify_name(d.field_name)

                # setting up formats/informats
                sas_form = self.sas_forms(name, d)
                formats += sas_form[0]
                informats += sas_form[1]

                # add the field names to the input statement
                inputs += '\t\t' + name
                if d.datatype == 'string':
                    inputs += " $"
                inputs += '\n'

                # if a field can be coded create a SAS PROC Format statement
                # that creates a value dictionary
                if d.coded_values:
                   codes = self.sas_coded(name, d)
                   value_formats += codes[0]
                   values += codes[1]

                # construct labels
                labels += "\tlabel {0}=\"{1}\";\n".format(name,
                        d.description)

        # Write the SAS File
        sas_file.write(informats + "\n")
        sas_file.write(formats + "\n")
        sas_file.write("input\n" + inputs +";\n\nrun;\n")
        sas_file.write("proc contents;run;\n\ndata SAS_EXPORT;\n")
        sas_file.write("\tset SAS_EXPORT;\n")
        sas_file.write(labels +"\trun;\n\n")
        sas_file.write("proc format;\n")
        sas_file.write(values + "\nrun;\n\n")
        sas_file.write("data SAS_EXPORT;\n\tset SAS_EXPORT;\n\n")
        sas_file.write(value_formats + "run;\n\n")
        sas_file.write("/*proc contents data=SAS_EXPORT;*/\n")
        sas_file.write("/*proc print data=SAS_EXPORT;*/\n")
        sas_file.write("run;\nquit;\n")

        sas_zip.writestr('sas_export.sas', sas_file.getvalue())
        sas_file.close()

        # WRITE CSV 
        csv_file = StringIO()
        csv_export = CSVExporter(self.queryset, self.concepts)
        csv_export.preferred_formats = self.preferred_formats
        sas_zip.writestr('sas_data.csv', csv_export.export(csv_file).getvalue())
        csv_file.close()

        sas_zip.close()
        return sas_zip
