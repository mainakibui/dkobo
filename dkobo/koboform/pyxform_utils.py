from pyxform import xls2json, xls2json_backends, builder, create_survey_from_xls
import StringIO
import xlrd
import csv

def create_survey_from_csv_text(csv_text, default_name='KoBoFormSurvey', default_language=u'default', warnings=None, ):
    workbook_dict = xls2json_backends.csv_to_dict(StringIO.StringIO(csv_text))
    dict_repr = xls2json.workbook_to_json(workbook_dict, default_name, default_language, warnings)
    dict_repr[u'name'] = dict_repr[u'id_string']
    return builder.create_survey_element_from_dict(dict_repr)

def convert_xls_to_xform(xls_file):
    """
    This receives an XLS file object and runs it through
    pyxform to create and validate the survey.
    """
    return create_survey_from_xls(xls_file).to_xml(validate=True)

def convert_xls_to_csv_string(xls_file_object, strip_empty_rows=True):
    """
    The goal: Convert an XLS file object to a CSV string.

    This draws on code from `pyxform.xls2json_backends` and `convert_file_to_csv_string`, however
    this works as it is expected (does not add extra sheets or perform misc conversions which are
    a part of `pyxform.xls2json_backends.xls_to_dict`.)
    """
    def _iswhitespace(string):
        return isinstance(string, basestring) and len(string.strip()) == 0

    def xls_value_to_unicode(value, value_type):
        """
        Take a xls formatted value and try to make a unicode string
        representation.
        """
        if value_type == xlrd.XL_CELL_BOOLEAN:
            return u"TRUE" if value else u"FALSE"
        elif value_type == xlrd.XL_CELL_NUMBER:
            #Try to display as an int if possible.
            int_value = int(value)
            if int_value == value:
                return unicode(int_value)
            else:
                return unicode(value)
        elif value_type is xlrd.XL_CELL_DATE:
            #Warn that it is better to single quote as a string.
            #error_location = cellFormatString % (ss_row_idx, ss_col_idx)
            #raise Exception(
            #   "Cannot handle excel formatted date at " + error_location)
            datetime_or_time_only = xlrd.xldate_as_tuple(
                value, workbook.datemode)
            if datetime_or_time_only[:3] == (0, 0, 0):
                # must be time only
                return unicode(datetime.time(*datetime_or_time_only[3:]))
            return unicode(datetime.datetime(*datetime_or_time_only))
        else:
            #ensure unicode and replace nbsp spaces with normal ones
            #to avoid this issue:
            #https://github.com/modilabs/pyxform/issues/83
            return unicode(value).replace(unichr(160), ' ')

    def _sheet_to_lists(sheet):
        result = []
        for row in range(0, sheet.nrows):
            row_results = []
            row_empty = True
            for col in range(0, sheet.ncols):
                value = sheet.cell_value(row, col)
                if isinstance(value, basestring):
                    value = value.strip()
                if (value is not None) and (not _iswhitespace(value)):
                    value = xls_value_to_unicode(value, sheet.cell_type(row, col))
                if value != "":
                    row_empty = False
                row_results.append(value)
            if not strip_empty_rows or not row_empty:
                result.append(row_results)
        return result

    workbook = xlrd.open_workbook(file_contents=xls_file_object.read())
    csvout = StringIO.StringIO()
    writer = csv.writer(csvout, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

    for sheet in workbook.sheets():
        writer.writerow([sheet.name])
        for row in _sheet_to_lists(sheet):
            writer.writerow([s.encode("utf-8") for s in ([""] + row)])
    return csvout.getvalue()