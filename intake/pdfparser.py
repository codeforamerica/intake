import os
import subprocess
import json
from tempfile import mkstemp


class PDFParserError(Exception):
    pass


class InvalidOptionError(Exception):
    pass


class PDFParser:

    def __init__(self, tmp_path=None, clean_up=True):
        self.TEMP_FOLDER_PATH = tmp_path
        self._tmp_files = []
        self.clean_up = clean_up
        self.PDFPARSER_PATH = os.environ.get('PDFPARSER_PATH', 'pdfparser.jar')

    def _coerce_to_file_path(self, path_or_file_or_bytes):
        """This converts file-like objects and `bytes` into
        existing files and returns a filepath
        if strings are passed in, it is assumed that they are existing
        files
        """
        if not isinstance(path_or_file_or_bytes, str):
            if isinstance(path_or_file_or_bytes, bytes):
                return self._write_tmp_file(
                    bytestring=path_or_file_or_bytes)
            else:
                return self._write_tmp_file(
                    file_obj=path_or_file_or_bytes)
        return path_or_file_or_bytes

    def _write_tmp_file(self, file_obj=None, bytestring=None):
        """Take a file-like object or a bytestring,
        create a temporary file and return a file path.
        file-like objects will be read and written to the tempfile
        bytes objects will be written directly to the tempfile
        """
        tmp_path = self.TEMP_FOLDER_PATH
        os_int, tmp_fp = mkstemp(dir=tmp_path)
        with open(tmp_fp, 'wb') as tmp_file:
            if file_obj:
                tmp_file.write(file_obj.read())
            elif bytestring:
                tmp_file.write(bytestring)
        self._tmp_files.append(tmp_fp)
        return tmp_fp

    def _load_json(self, raw_string):
        return json.loads(raw_string)

    def _dump_json(self, data):
        return json.dumps(data)

    def clean_up_tmp_files(self):
        if not self._tmp_files:
            return
        for i in range(len(self._tmp_files)):
            path = self._tmp_files.pop()
            os.remove(path)

    def _get_name_option_lookup(self, field_data):
        return {
            item['name']: item.get('options', None)
            for item in field_data['fields']
        }

    def _get_file_contents(self, path):
        """given a file path, return the contents of the file
        if decode is True, the contents will be decoded using the default
        encoding
        """
        return open(path, 'rb').read()

    def run_command(self, args):
        """Run a command to pdftk on the command line.
            `args` is a list of command line arguments.
        This method is reponsible for handling errors that arise from
        pdftk's CLI
        """
        args = ['java', '-jar', self.PDFPARSER_PATH] + args
        process = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        out, err = process.communicate()
        if err:
            raise PDFParserError(err.decode('utf-8'))
        return out.decode('utf-8')

    def _fill(self, pdf_path, output_path, option_check, answers):
        answer_fields = {'fields': []}
        for k, v in answers.items():
            if k in option_check:
                if option_check[k]:
                    if v not in option_check[k]:
                        raise InvalidOptionError(
                            "''{}' is not a valid option for '{}'. Choices: {}".format(
                                v, k, option_check[k]
                                ))
            answer_fields['fields'].append({k: v})
        self.run_command([
            'set_fields',
            pdf_path,
            output_path,
            self._dump_json(answer_fields)
        ])

    def join_pdfs(self, list_of_pdf_paths):
        paths = [self._coerce_to_file_path(p) for p in list_of_pdf_paths]
        output_path = self._write_tmp_file()
        args = ['concat_files'] + paths + [output_path]
        self.run_command(args)
        result = self._get_file_contents(output_path)
        if self.clean_up:
            self.clean_up_tmp_files()
        return result

    def get_field_data(self, pdf_file_path):
        pdf_file_path = self._coerce_to_file_path(pdf_file_path)
        string = self.run_command(['get_fields', pdf_file_path])
        return self._load_json(string)

    def fill_pdf(self, pdf_path, answers):
        pdf_path = self._coerce_to_file_path(pdf_path)
        field_data = self.get_field_data(pdf_path)
        option_check = self._get_name_option_lookup(field_data)
        output_path = self._write_tmp_file()
        self._fill(pdf_path, output_path, option_check, answers)
        result = self._get_file_contents(output_path)
        if self.clean_up:
            self.clean_up_tmp_files()
        return result

    def fill_many_pdfs(self, pdf_path, answers_list):

        # don't clean up while filling multiple pdfs
        _clean_up_setting = self.clean_up
        self.clean_up = False

        pdf_path = self._coerce_to_file_path(pdf_path)
        field_data = self.get_field_data(pdf_path)
        option_check = self._get_name_option_lookup(field_data)
        tmp_filled_pdf_paths = []
        for answers in answers_list:
            output_path = self._write_tmp_file()
            self._fill(pdf_path, output_path, option_check, answers)
            tmp_filled_pdf_paths.append(output_path)
        self.clean_up = _clean_up_setting
        return self.join_pdfs(tmp_filled_pdf_paths)       


