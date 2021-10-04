# -*- coding: utf-8 -*-

from odoo import fields, models

class AccountMove(models.Model):
    _inherit = 'account.move'

    contabilidad_electronica = fields.Boolean('CE', copy=False)