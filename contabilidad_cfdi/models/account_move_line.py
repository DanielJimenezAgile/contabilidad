# -*- coding: utf-8 -*-
# Copyright 2019 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).-
from odoo import api, models, fields


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    
    contabilidad_electronica = fields.Boolean('CE', copy=False)
    account_cfdi_ids = fields.One2many('account.move.cfdi33','move_line_id', 'CFDI 3.3')

    
    def init(self):
        """
            The join between accounts_partners subquery and account_move_line
            can be heavy to compute on big databases.
            Join sample:
                JOIN
                    account_move_line ml
                        ON ap.account_id = ml.account_id
                        AND ml.date < '2018-12-30'
                        AND ap.partner_id = ml.partner_id
                        AND ap.include_initial_balance = TRUE
            By adding the following index, performances are strongly increased.
        :return:
        """
        self._cr.execute(
            "SELECT indexname FROM pg_indexes WHERE indexname = " "%s",
            ("account_move_line_account_id_partner_id_index",),
        )
        if not self._cr.fetchone():
            self._cr.execute(
                """
            CREATE INDEX account_move_line_account_id_partner_id_index
            ON account_move_line (account_id, partner_id)"""
            )

class AccountMoveCFDI33(models.Model):
    _name = 'account.move.cfdi33'

    fecha = fields.Date('Fecha')
    folio = fields.Char('Folio')
    uuid = fields.Char('UUID')
    partner_id = fields.Many2one('res.partner','Cliente')
    rfc_cliente = fields.Char('RFC')
    moneda = fields.Char('Moneda')
    tipocamb = fields.Float('T/C')
    monto = fields.Float('Monto')
    move_line_id = fields.Many2one('account.move.line', 'Move line')
    
    