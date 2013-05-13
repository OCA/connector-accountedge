# -*- encoding: utf-8 -*-
##############################################################################
#····
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.·····
#
##############################################################################

import time
import base64

from osv import osv, fields


class hr_expense_expense(osv.osv):
    _inherit = 'hr.expense.expense'

    def _create_csv_report(self,cr,uid,ids,context={}):
        res = {}
        for id in ids:
            this    = self.browse(cr, uid, id)
            empl_id = self.pool.get('hr.employee').search(cr, uid, [('user_id','=', this.user_id.id)])
            empl    = self.pool.get('hr.employee').browse(cr, uid, empl_id)[0]

            output  = empl.name
            output += "\n"
            output += "RecordId\tDate\tVendor Invoice #\tAccount #\tAmout\tDescription\
                        \tTax Code\tTax Amount TVQ\tTax Amount TPS/TVH\tCurrency Code\tExchange Rate\n"

            for l in this.line_ids:
                output  += u"%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\r\n" % (
                        empl.supplier_id_accountedge,
                        l.date_value,
                        l.expense_id.id,
                        l.account_id.code,
                        (l.total_amount or '0.00'),
                        l.name,
                        (l.tax_id.description or '000'),
                        '0.00',
                        '0.00',
                        (l.expense_id.currency_id.name or 'CAD'),
                        (l.expense_id.currency_id.rate or '1'))
                byte_string  = output.encode('utf-8-sig')

            res[id] = base64.encodestring(byte_string)

            self.write(cr, uid, ids, {'csv_file':res[id]}, context=context)
            self._add_attachment(cr,uid,id,byte_string,context)

        return True


    def _add_attachment(self,cr,uid,ids,content,context={}):

        file_name   = 'rapport_'+time.strftime('%Y%m%d_%H%M%S')
        attach_id   = self.pool.get('ir.attachment').create(cr, uid, {
            'name'          : file_name,
            'datas'         : base64.encodestring(content),
            'datas_fname'   : file_name,
            'res_model'     : self._name,
            'res_id'        : ids,
            },
            context=context
        )
        return True

    def action_exported(self,cr,uid,ids,*args):
        if not len(ids):
            return False
        self.write(cr,uid,ids,{'state': 'exported'})
        self._create_csv_report(cr,uid,ids,{})
        return True

    _columns = {
        'state': fields.selection([
            ('draft', 'New'),
            ('confirm', 'Waiting Approval'),
            ('accepted', 'Approved'),
            ('exported', 'Exported'),
            ('imported', 'Imported'),
            ('cancelled', 'Refused'),],
            'State', readonly=True, help='When the expense request is created the state is \'Draft\'.\
                    \n It is confirmed by the user and request is sent to admin, the state is \'Waiting Confirmation\'.\
                    \nIf the admin accepts it, the state is \'Accepted\'.\
                    \nIf the admin refuses it, the state is \'Refused\'.\
                    \n If a csv file has been generated for the expense request, the state is  \'Exported\'.\
                    \n If the expense request has been imported in AccountEdge, the state is \'Imported\'.'
        ),
    }


hr_expense_expense()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

