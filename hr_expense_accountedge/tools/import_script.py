# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010 Savoir-faire Linux (<http://www.savoirfairelinux.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import xmlrpclib
import base64
from datetime import datetime


def main():

    # Connection credentials
    server_url  = 'http://localhost:8069'
    username    = 'admin'
    pwd         = 'admin'
    dbname      = 'testV10'

    # Get the uid
    sock_common = xmlrpclib.ServerProxy('%s/xmlrpc/common' % server_url)
    uid = sock_common.login(dbname, username, pwd)

    # Connect to the server
    sock = xmlrpclib.ServerProxy('%s/xmlrpc/object' % server_url)

    # Search for exported expense notes
    args = [('state', '=', 'exported')]
    expense_ids = sock.execute(dbname, uid, pwd, 'hr.expense.expense', 'search', args)

    # Outpout file for AccountEdge
    final_csv   = open('hr_expense_accountedge.csv', 'w')

    # Write the file header
    final_csv.write("Card ID\tDate\tVendor Invoice #\tAccount Number\tAmount\tDescription\t\
        GST Amount\tPST/QST Amount\tCurrency Code\tExchange Rate\r\n")

    # For each exported expense note, search for the most recent csv file attachement
    for expense_id in expense_ids:

        args    = [('res_model','=','hr.expense.expense'),('res_id', '=', expense_id)]
        csv_ids = sock.execute(dbname, uid, pwd, 'ir.attachment', 'search', args)

        fields  = ['name', 'datas'] #fields to read
        csv_obj = sock.execute(dbname, uid, pwd, 'ir.attachment', 'read', csv_ids, fields)

        latest_csv  = None
        latest_date = datetime(2000, 1, 1, 0, 0, 0)

        # Find the latest csv
        for csv in csv_obj:
            format = 'rapport_%Y%m%d_%H%M%S'
            date_created = datetime.strptime(csv["name"], format)

            if date_created > latest_date:
                latest_date = date_created
                latest_csv  = csv

        # Copy the lines to the new summary file
        if latest_csv:
            content = base64.b64decode(csv['datas'])
            content = content.split("\r\n")

            for num_line in range(len(content)):
                if num_line > 1:
                    final_csv.write(content[num_line])
                    final_csv.write("\r\n")


        # Mark the expenses as imported
        values = {'state': 'exported'}
        result = sock.execute(dbname, uid, pwd, 'hr.expense.expense', 'write', expense_ids, values)


    final_csv.close()


if __name__ == "__main__":
    main()






