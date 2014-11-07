# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Business Applications
#    Copyright (c) 2011 OpenERP S.A. <http://openerp.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, orm
from edi import EDIMixin

URL = "%s/web/webclient/home#id=%s&view_type=page&model=hr.expense.expense"


class hr_expense_expense(orm.Model, EDIMixin):
    _inherit = 'hr.expense.expense'

    def _edi_get_web_url_view(self, cr, uid, ids, field_name, arg, context):
        res = {}
        for id in ids:
            web_root_url = self.pool.get('ir.config_parameter').get_param(
                cr, uid, 'web.base.url',
            )
            res[id] = URL % (web_root_url, id)
        return res

    _columns = {
        'web_url_view': fields.function(
            _edi_get_web_url_view,
            string='Url of the expense view',
            type='char',
            size=255,
            readonly=True,
        ),
    }
