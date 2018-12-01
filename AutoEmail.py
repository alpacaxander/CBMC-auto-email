import smtplib

import os
from string import Template
import csv
import getpass

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def join(table1, table2, key1, key2):
    result = []
    for row1 in table1[1:]:
        for row2 in table2[1:]:
            if row1[key1] == row2[key2]:
                temp_row = {}
                temp_row.update(row1)
                temp_row.update(row2)
                result.append(temp_row)
    return result

def csvToTable(filename):
    result = []
    with open(filename, encoding='utf-8') as csv_file:
        csv_reader = csv.reader(csv_file, quotechar='"', delimiter=',',
                     quoting=csv.QUOTE_ALL, skipinitialspace=True)
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                columns = row
                line_count += 1
            else:
                row_dict = dict(zip(columns, row))
                result.append(row_dict)
                line_count += 1
    return result

def read_template(filename):
    """
    Returns a Template object comprising the contents of the 
    file specified by filename.
    """
    with open(filename, 'r', encoding='utf-8') as template_file:
        template_file_content = template_file.read()
    return Template(template_file_content)

def extractData(filename):
    """Read a dictionary/list from file"""
    s = open(filename, 'r').read()
    data = eval(s)
    return data

def getTables(tables):
    tables = []
    for table in tables:
        if os.path.isfile(table["path"]):
            tables.append(csvToTable(table["path"]))
        else:
            tables.append(csvToTable(os.path.join(
                table["path"], os.listdir(table["path"])[0])))
    return tables

def main():
    # Get instructions
    formatfile = input("Format File: ")
    format = extractData(formatfile)

    # Get data from each source
    tables = getTables(format["tables"])

    # Group data (assumes 2 tables)
    new_table = join(tables[0], tables[1], format["tables"][0]["key"], format["tables"][1]["key"])
    
    #input 
    MY_ADDRESS = input("Gmail Username: ")
    PASSWORD =   getpass.getpass("------Password: ")
    TITLE = input("Title: ")

    message_template = read_template(format["template"])
    messages = []

    # For each row of data compose an email and ready it
    for row in new_table:
        #if conditions are false then ignore this one
        for condition in format["conditions"]["greater_than"]:
            try:
                if not (int(row[condition["attribute"]]) > int(condition["value"])):
                    continue
            except ValueError:
                pass

        for condition in format["conditions"]["less_than"]:
            try:
                if not (int(row[condition["attribute"]]) < int(condition["value"])):
                    continue
            except ValueError:
                pass
    
        for condition in format["conditions"]["equal"]:
            try:
                if not (str(row[condition["attribute"]]) == str(condition["value"])):
                    continue
            except ValueError:
                pass

        msg = MIMEMultipart()       # create a message

        substitution = format["substitution"].copy()
        for key in substitution:
            substitution[key] = row[substitution[key]]

        message = message_template.substitute(substitution)

        msg['From']=MY_ADDRESS
        msg['To']=row['PrimaryManagerEmail']
        msg['Subject']=TITLE

        msg.attach(MIMEText(message, 'plain'))

        messages.append(msg)

        print(msg)

    if input("Confirm send all emails (y/n)") == "y":
        s = smtplib.SMTP('smtp.gmail.com:587')
        s.ehlo()
        s.starttls()
        s.login(MY_ADDRESS, PASSWORD)
        for msg in messages:
            s.send_message(msg)
        s.quit()
    
if __name__ == '__main__':
    main()