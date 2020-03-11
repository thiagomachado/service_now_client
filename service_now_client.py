import requests
import json
import ntpath
from exceptions import *


class ServiceNowClient:

    def __init__(self, instance, user, password, empty_error=True):
        """
        Initialize ServiceNow instance

        :param self: self object
        :param instance: url of instance (string)
        :param user: username (string)
        :param password: password (string)
        :param empty_error: raise exception if result is empty

        Output : none
        """

        self.username = user
        self.password = password
        self.headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
        self.instance = 'https://' + instance + '.service-now.com'
        self.empty_error = empty_error

    def create(self, table, data):
        """
        Create a new record

        :param self: self object
        :param table: name of table (string)
        :param data: fields and value to be set for record (dictionary)

        Output : returns all fields and details of new record
        """

        # Validation
        if not isinstance(data, dict):
            raise InvalidFormat('"data" format incorrect. Dictionary expected')
        if not isinstance(table, str):
            raise InvalidFormat('"table" format incorrect. String expected')

        # Set the request parameters
        self.url = self.instance + '/api/now/table/' + str(table)

        self.response = requests.post(url=self.url,
                                      auth=(self.username, self.password),
                                      headers=self.headers,
                                      data=json.dumps(data))

        if self.response.status_code != 201:
            raise ResponseError(
                'Error code = ' + str(self.response.status_code) + ' , Error details = ' + str(self.response.json()))

        # Return the ticket details
        return self.response.json()

    def update(self, table, search_list, data):
        """
        Update the parameters of a specific record

        :param self: self object
        :param table: name of table (string)
        :param search_list: comma separated field, operator and value to retrieve matching incidents (simple or nested lists)
        :param data: field and value to be updated (dictionary)

        Output : returns dictionary containing number and status of request as true or false or error
        """

        # Validation
        if not isinstance(data, dict):
            raise InvalidFormat('"data" format incorrect. Dictionary expected')
        if not isinstance(table, str):
            raise InvalidFormat('"table" format incorrect. String expected')

        # Calling search method to search for matching incidents
        incident_list = self.search(table, search_list, 'sys_id')

        # Terminate operation if no incidents are found
        if not incident_list:
            if self.empty_error:
                raise EmptyResult('No record found')
            else:
                return False

        # Output dictionary
        result = {}

        for item in incident_list:

            # Set the request parameters
            self.url = self.instance + '/api/now/table/' + str(table) + '/' + str(item['sys_id'])

            self.response = requests.put(url=self.url,
                                         auth=(self.username, self.password),
                                         headers=self.headers,
                                         data=json.dumps(data))

            if self.response.status_code != 200:
                result[str(item['sys_id'])] = 'Error Code ' + str(self.response.status_code) + ', ' + str(
                    self.response.json()['error'])
            else:
                result[str(item['sys_id'])] = 'true'

        # Return result
        return result

    def search(self, table, search_list, fields=''):
        """
        Method to retrieve an incident based on search parameters

        :param self: self object
        :param table: name of table (string)
        :param search_list: comma separated field, operator and value to retrieve matching incidents (simple or nested lists)
        :param fields: comma separated response fields (string)

        Output : returns response fields of each matching records
        """

        self.url = (self.instance
                    + '/api/now/table/' + str(table) + '?sysparm_limit=50&sysparm_query=sysparm_query='
                    )

        # ServiceNow operators and symbols dictionary
        operators = {
            'is': '=',
            'is not': '!=',
            'is one of': 'IN',
            'starts with': 'STARTSWITH',
            'ends with': 'ENDSWITH',
            'contains': 'LIKE',
            'does not contain': 'NOT LIKE',
            'less than or is': '<=',
            'greater than or is': '>=',
            'same as': 'SAMEAS',
            'is empty': 'ISEMPTY',
            'is not empty': 'ISNOTEMPTY',
            'is anything': 'ANYTHING',
            'is empty string': 'EMPTYSTRING'
        }

        # Validation
        if not isinstance(fields, str):
            raise InvalidFormat('"fields" format incorrect. String expected')
        if not isinstance(table, str):
            raise InvalidFormat('"table" format incorrect. String expected')

        # Validating, parsing searchList elements to form query part of url
        for line in search_list:
            # Nested list
            if isinstance(line, list):
                field = line[0]
                operator = line[1]
                try:
                    value = line[2]
                except IndexError:
                    # Each list must contain 3 elements
                    line.insert(2, '')
                    value = line[2]
                try:
                    self.url = self.url + '^%s%s%s' % (field, operators[operator.lower()], value)
                except KeyError:
                    raise InvalidValue(
                        'Operator value invalid. Choose one of the following:\n' + str(tuple(x for x in operators)))

            else:
                # Setting flag incase of a simple list
                single_list = 'true'

        try:
            # Simple list
            if (single_list == 'true') and (isinstance(search_list, list)):
                try:
                    self.url = self.url + '^%s%s' % (search_list[0], operators[search_list[1].lower()])
                except KeyError:
                    raise InvalidValue(
                        'Operator value invalid. Choose one of the following:\n' + str(tuple(x for x in operators)))

                try:
                    self.url = self.url + '%s' % (search_list[2])
                except IndexError:
                    # Each list must contain 3 elements
                    search_list.insert(2, '')
                    self.url = self.url + '%s' % (search_list[2])

            else:
                raise InvalidFormat('"searchList" format incorrect. Simple or nested list expected')

        except UnboundLocalError:
            print('')

        self.url = self.url + '&sysparm_fields=' + str(fields)

        # Do the HTTP request
        self.response = requests.get(self.url,
                                     auth=(self.username,
                                           self.password),
                                     headers=self.headers,
                                     )

        # Check for HTTP codes other than 200
        if self.response.status_code != 200:
            raise ResponseError(
                'Error code = ' + str(self.response.status_code) + ' , Error details = ' + str(self.response.json()))
        else:
            if not self.response.json()['result']:
                if self.empty_error:
                    raise EmptyResult('No record found')
                else:
                    print('\n\n**No record found**')
                    return False

        # Return the JSON response (dictionary type)
        return self.response.json()['result']

    def delete(self, table, search_list):
        """
        Method to delete record based on search parameters

        :param self: self object
        :param table: table name (string)
        :param search_list: comma separated field, operator and value to retrieve matching incidents (simple or nested lists)

        Output : returns dictionary containing number and status of request as true or false or error
        """

        # Validation
        if not isinstance(table, str):
            raise InvalidFormat('"table" format incorrect. String expected')

        # Calling search method to search for matching incidents
        incident_list = self.search(table, search_list, 'sys_id')

        # Terminate operation if no incidents are found
        if not incident_list:
            if self.empty_error:
                raise EmptyResult('No record found')
            else:
                return False

        # Output dictionary
        result = {}

        for item in incident_list:

            # Set the request parameters
            self.url = self.instance + '/api/now/table/' + str(table) + '/' + str(item['sys_id'])

            self.response = requests.delete(url=self.url,
                                            auth=(self.username, self.password),
                                            headers=self.headers,
                                            )

            if self.response.status_code != 204:
                result[str(item['sys_id'])] = 'Error Code ' + str(self.response.status_code) + ', ' + str(
                    self.response.json()['error'])
            else:
                result[str(item['sys_id'])] = 'true'

        # Return result
        return result

    def change_state(self, table, search_list, state):
        """
        Method to change state of an incident

        :param self: self object
        :param table: name of table (string)
        :param search_list: comma separated field, operator and value to retrieve matching incidents (simple or nested lists)
        :param state: the target state of the ticket (string)

        Output : returns dictionary containing number and status of request as true or false or error
        """

        # Validation
        if not isinstance(state, str):
            raise InvalidFormat('"state" format incorrect. String expected')
        if not isinstance(table, str):
            raise InvalidFormat('"table" format incorrect. String expected')

        table = table.lower()
        # Calling search method to search for matching incidents
        incident_list = self.search(table, search_list, fields='number,sys_id')

        # Terminate operation if no incidents are found
        if not incident_list:
            if self.empty_error:
                raise EmptyResult('No record found')
            else:
                return False

        # Incident states and value
        inc_state = {
            'new': '1',
            'in progress': '2',
            'on hold': '3',
            'resolved': '6',
            'closed': '7',
            'canceled': '8'
        }

        # Close Notes comments for incident state
        inc_notes = {
            'new': '',
            'in progress': '',
            'on hold': '',
            'resolved': 'Incident resolved',
            'closed': 'Incident closed',
            'canceled': 'Incident canceled'
        }

        # Close code selected for incident state
        inc_close_code = {
            'new': '',
            'in progress': '',
            'on hold': '',
            'resolved': 'Solved (Permanently)',
            'closed': 'Solved (Permanently)',
            'canceled': 'Closed/Resolved by Caller'
        }

        # Incident states and value
        prb_state = {
            'open': '1',
            'known error': '2',
            'pending change': '3',
            'closed/resolved': '4'
        }

        # Work Notes comments for incident state
        prb_work_notes = {
            'open': 'Problem in open state',
            'known error': 'Problem has known error',
            'pending change': 'Problem is pending change',
            'closed/resolved': 'Problem resolved'
        }

        # Close Notes comments for incident state
        prb_close_notes = {
            'open': '',
            'known error': '',
            'pending change': '',
            'closed/resolved': 'Problem closed/resolved'
        }

        # Output dictionary
        result = {}

        # Storing sys_id of each incident found
        for item in incident_list:
            if table == 'problem':
                self.url = self.instance + '/api/now/table/problem/' + item['sys_id']
                try:
                    self.data = ('{\"close_notes\":\"' + prb_close_notes[state.lower()]
                                 + '\",\"work_notes\":\"' + prb_work_notes[state.lower()]
                                 + '\",\"state\":\"' + prb_state[state.lower()]
                                 + '\"}'
                                 )
                except KeyError:
                    raise InvalidValue(
                        '"state" invalid. Choose one of the following:\n' + str(tuple(x for x in prb_state)))
            else:
                try:
                    self.url = self.instance + '/api/now/table/' + str(table) + '/' + item['sys_id']
                    self.data = ('{\"close_code\":\"' + inc_close_code[state.lower()]
                                 + '\",\"close_notes\":\"' + inc_notes[state.lower()]
                                 + '\",\"state\":\"' + inc_state[state.lower()]
                                 + '\"}'
                                 )
                except KeyError:
                    raise InvalidValue(
                        '"state" invalid. Choose one of the following:\n' + str(tuple(x for x in inc_state)))

            self.response = requests.put(url=self.url,
                                         auth=(self.username, self.password),
                                         headers=self.headers,
                                         data=self.data
                                         )

            if self.response.status_code != 200:
                result[str(item['number'])] = 'Error Code ' + str(self.response.status_code) + ', ' + str(
                    self.response.json()['error'])
            else:
                result[str(item['number'])] = 'true'

        # Return success
        return result

    def get_file(self, table, search_list, type=''):
        """
        Retrieve Attachment details pertaining to an incident and get the web link for download

        :param self: self object
        :param table: name of table (string)
        :param search_list: comma separated field, operator and value to retrieve matching incidents (simple or nested lists)
        :param type: dot extension of the type of attachment to be downloaded (string)

        Output : returns dictionary containing number and status of request as true or false or error
        """

        # Validation
        if not (type == ''):
            if not isinstance(type, str):
                raise InvalidFormat('"type" format incorrect. String expected')
        if not isinstance(table, str):
            raise InvalidFormat('"table" format incorrect. String expected')

        # Calling search method to search for matching incidents
        incident_list = self.search(table, search_list, 'number,sys_id')

        # Terminate operation if no incidents are found
        if not incident_list:
            if self.empty_error:
                raise EmptyResult('No record found')
            else:
                return False

        file_type_found_all = False

        # Output dictionary
        result = {}

        # Checking for incidents for attachments
        for item in incident_list:

            # URL to fetch attachment
            self.url = (self.instance
                        + '/api/now/attachment?sysparm_limit=50&sysparm_query=sysparm_query=active=true^table_sys_id='
                        + item['sys_id'])

            self.response = requests.get(url=self.url,
                                         auth=(self.username, self.password),
                                         headers=self.headers,
                                         )

            # Check for HTTP codes other than 200
            if self.response.status_code != 200:
                result[str(item['number'])] = 'Error Code ' + str(self.response.status_code) + ', ' + str(
                    self.response.json()['error'])
            else:
                result[str(item['number'])] = 'true'

            # Decode the JSON response
            attachment_data = self.response.json()

            # Terminate operation if no incidents are found
            if not attachment_data['result']:
                result[str(item['number'])] = 'false'
                continue
            else:
                result[str(item['number'])] = 'true'

            # Download the specified types of file from the web location received in JSON response
            file_type_found = False
            for item_attach in attachment_data['result']:
                if item_attach['file_name'].endswith(type):
                    file_type_found = True
                    file_type_found_all = True
                    r = requests.get(item_attach['download_link'], auth=(self.username, self.password))

                    # Files downloaded under Python directory
                    with open(item_attach['file_name'], 'wb') as code:
                        code.write(r.content)

            if file_type_found:
                result[str(item['number'])] = 'true'

        if file_type_found_all:
            return result
        else:
            if self.empty_error:
                raise EmptyResult('No record found')
            else:
                return False

    def upload_file(self, table, search_list, file_name):
        """
        Upload files to a specific ticket

        :param self: self object
        :param table: table name (string)
        :param search_list: comma separated field, operator and value to retrieve matching incidents (simple or nested lists)
        :param file_name: name of file to be uploaded (string)

        Output : returns dictionary containing number and status of request as true or false or error
        """

        # Validation
        if not isinstance(table, str):
            raise InvalidFormat('"table" format incorrect. String expected')
        if not isinstance(file_name, str):
            raise InvalidFormat('"filename" format incorrect. String expected')

        # Calling search method to search for matching incidents
        incident_list = self.search(table, search_list, 'number,sys_id')

        # Terminate operation if no incidents are found
        if not incident_list:
            if self.empty_error:
                raise EmptyResult('No record found')
            else:
                return False

        # Output dictionary
        result = {}

        for item in incident_list:

            # Set the request parameters
            self.url = self.instance + '/api/now/attachment/file?table_name=' + str(table) + '&table_sys_id=' + str(
                item['sys_id']) + '&file_name=' + ntpath.basename(file_name)

            data = open(file_name, 'rb').read()
            headers = {'Content-Type': '*/*', 'Accept': 'application/json'}

            response = requests.post(url=self.url,
                                     auth=(self.username, self.password),
                                     headers=headers, data=data)

            if self.response.status_code != 200:
                result[str(item['number'])] = 'Error Code ' + str(self.response.status_code) + ', ' + str(
                    self.response.json()['error'])
            else:
                result[str(item['number'])] = 'true'

        # Return result
        return result

    def delete_file(self, table, search_list, filename):
        """
        Deletes files to a specific ticket

        :param self: self object
        :param table: name of table (string)
        :param search_list: comma separated field, operator and value to retrieve matching incidents (simple or nested lists)
        :param filename: complete path of file to be uploaded (string)

        Output : returns dictionary containing number and status of request as true or false or error
        """

        # Validation
        if not isinstance(table, str):
            raise InvalidFormat('"table" format incorrect. String expected')

        if not isinstance(filename, str):
            raise InvalidFormat('"filename" format incorrect. String expected')

        # Calling search method to search for matching incidents
        incident_list = self.search(table, search_list, 'number,sys_id')

        # Terminate operation if no incidents are found
        if not incident_list:
            if self.empty_error:
                raise EmptyResult('No record found')
            else:
                return False

        file_found_all = False

        # Output dictionary
        result = {}

        # Checking incident for attachments
        for item in incident_list:
            # Set the request parameters
            self.url = (self.instance
                        + '/api/now/attachment?sysparm_limit=50&sysparm_query=sysparm_query=active=true^table_sys_id='
                        + item['sys_id'])

            self.response = requests.get(url=self.url,
                                         auth=(self.username, self.password),
                                         headers=self.headers,
                                         )

            # Check for HTTP codes other than 200
            if self.response.status_code != 200:
                result[str(item['number'])] = 'Error Code ' + str(self.response.status_code) + ', ' + str(
                    self.response.json()['error'])
            else:
                result[str(item['number'])] = 'true'

            # Decode the JSON response
            attachment_data = self.response.json()

            # Terminate operation if no incidents are found
            if not attachment_data['result']:
                result[str(item['number'])] = 'false'
                continue
            else:
                result[str(item['number'])] = 'true'

            # Delete the specified types of file from the web location received in JSON response
            file_found = False
            for item_attach in attachment_data['result']:
                if str(item_attach['file_name']) == filename:
                    file_found = True
                    file_found_all = True

                    self.url = self.instance + '/api/now/attachment/' + item_attach['sys_id']

                    self.response = requests.delete(url=self.url,
                                                    auth=(self.username, self.password),
                                                    headers=self.headers,
                                                    )

                    # Check for HTTP codes other than 204
                    if self.response.status_code != 204:
                        result[str(item['number'])] = 'Error Code ' + str(self.response.status_code) + ', ' + str(
                            self.response.json()['error'])
                    else:
                        result[str(item['number'])] = 'true'

            if not file_found:
                result[str(item['number'])] = 'false'

        if file_found_all:
            return result
        else:
            if self.empty_error:
                raise EmptyResult('File not found')
            else:
                return False

    def send_email(self, subject, message, to, cc='', bcc='', table='', sys_id=''):
        """
        Send email through ServiceNow

        :param self: self object
        :param subject: subject of email (string)
        :param message:	email body (string)
        :param to: email address of receiver (string)
        :param cc: Cc email addresses (string)
        :param bcc: Bcc email addresses (string)
        :param table: name of table (string)
        :param sys_id: sysId of incident (string)

        Output : returns email content
        """

        # Validation
        if not str(to):
            raise InvalidFormat('\nMandatory parameter "to" missing')

        if (str(sys_id) and (not str(table))) or ((not str(sys_id)) and (str(table))):
            raise InvalidFormat('\nBoth parameters "table" and "sysId" are required')

        if cc:
            if not isinstance(cc, str):
                raise InvalidFormat('"cc" format incorrect. String expected')
        if bcc:
            if not isinstance(bcc, str):
                raise InvalidFormat('"bcc" format incorrect. String expected')
        if table:
            if not isinstance(table, str):
                raise InvalidFormat('"table" format incorrect. String expected')
        if sys_id:
            if not isinstance(sys_id, str):
                raise InvalidFormat('"sysId" format incorrect. String expected')

        # Set the request parameters
        self.url = self.instance + '/api/now/v1/email'
        self.data = ('{\"to\": [\"' + str(to)
                     + '\"], \"cc\": [\"' + str(cc)
                     + '\"], \"bcc\": [\"' + str(bcc)
                     + '\"], \"subject\": \"' + str(subject)
                     + '\", \"text\": \"' + str(message)
                     + '\", \"table_name\": \"' + str(table)
                     + '\", \"table_record_id\": \"' + str(sys_id)
                     + '\"}'
                     )
        self.response = requests.post(url=self.url,
                                      auth=(self.username,
                                            self.password),
                                      headers=self.headers,
                                      data=self.data
                                      )

        if self.response.status_code != 200:
            raise ResponseError(
                'Error code = ' + str(self.response.status_code) + ' , Error details = ' + str(self.response.json()))

        # Decode the JSON response into a dictionary and use the data
        data = self.response.json()
        return data['result']

    def read_email(self, sys_id):
        """
        Send email through ServiceNow

        :param self: self object
        :param sys_id: sysId of email to be read (string)

        Output : returns email data
        """

        # Validation
        if not isinstance(sys_id, str):
            raise InvalidFormat('"filename" format incorrect. String expected')

        # Set the request parameters
        self.url = self.instance + '/api/now/v1/email/' + str(sys_id)

        self.response = requests.get(url=self.url,
                                     auth=(self.username, self.password),
                                     headers=self.headers
                                     )

        if self.response.status_code != 200:
            raise ResponseError(
                'Error code = ' + str(self.response.status_code) + ' , Error details = ' + str(self.response.json()))

        # Decode the JSON response into a dictionary and use the data
        data = self.response.json()

        return data['result']
