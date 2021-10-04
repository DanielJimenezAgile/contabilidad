
from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)

class ActualizarPolizas(models.TransientModel):
    _name = 'actualizar.polizas'
    
    fecha_inicio = fields.Date('Fecha inicio')
    fecha_fin = fields.Date('Fecha fin')
    polizas_de_facturas_de_cliente = fields.Boolean('Polizas de facturas de cliente')
    polizas_de_facturas_de_proveedor = fields.Boolean('Polizas de facturas de proveedor')
    polizas_de_facturas_de_pagos = fields.Boolean('Polizas de facturas de pagos')
    polizas_de_inventarios = fields.Boolean('Polizas de inventarios')
    polizas_de_micelaneos = fields.Boolean('Polizas de micelaneos')
    
    
    def action_validar_actualizar_polizas(self):
        if self.polizas_de_facturas_de_cliente:
            invoices = self.env['account.move'].search([('invoice_date','>=',self.fecha_inicio),
                                                           ('invoice_date','<=', self.fecha_fin),
                                                           ('estado_factura','=','factura_correcta'),
                                                           ('state','in', ['open', 'paid']),
                                                           ('type', '=', 'out_invoice')])
            moves = invoices.mapped('id')
            if moves:
                moves.write({'contabilidad_electronica':True})
                moves.mapped('line_ids').write({'contabilidad_electronica':True})
            cfdi_obj = self.env['account.move.cfdi33']
            for inv in invoices:
                move_lines = inv.move_id.line_ids.filtered(lambda x:x.name=='/')
                #if move:
                for line in move_lines:
                    cfdi_data = {'fecha': inv.invoice_date, 
                                 'folio': inv.folio, 
                                 'uuid': inv.folio_fiscal, 
                                 'partner_id': inv.partner_id.id, 
                                 'monto': inv.amount_total, 
                                 'moneda': inv.moneda, 
                                'tipocamb': inv.tipocambio, 
                                'rfc_cliente': inv.partner_id.rfc
                                }
                    if line.account_cfdi_ids:
                        #Here, we are going to assume that move line will have only one cfdi line always
                        line.account_cfdi_ids[0].write(cfdi_data)
                    else:
                        cfdi_data['move_line_id'] = line.id
                        cfdi_obj.create(cfdi_data)


        if self.polizas_de_facturas_de_proveedor:
            invoices = self.env['account.move'].search([('invoice_date','>=',self.fecha_inicio),
                                                           ('invoice_date','<=', self.fecha_fin),
                                                           ('estado_factura','=','factura_correcta'),
                                                           ('state','in', ['open', 'paid']),
                                                           ('type', '=', 'in_invoice')])
            
            moves = invoices.mapped('id')
            if moves:
                moves.write({'contabilidad_electronica':True})
                moves.mapped('line_ids').write({'contabilidad_electronica':True})
            cfdi_obj = self.env['account.move.cfdi33']
            for inv in invoices:
                #move = inv.move_id
                move_lines = inv.move_id.line_ids.filtered(lambda x:x.name=='/')
                #if move:
                for line in move_lines:
                    cfdi_data = {'fecha': inv.invoice_date, 
                                 'folio': inv.folio, 
                                 'uuid': inv.folio_fiscal, 
                                 'partner_id': inv.partner_id.id, 
                                 'monto': inv.amount_total, 
                                 'moneda': inv.moneda, 
                                 'tipocamb': inv.tipocambio, 
                                 'rfc_cliente': inv.partner_id.rfc
                                 }
                    if line.account_cfdi_ids:
                        line.account_cfdi_ids[0].write(cfdi_data)
                    else:
                        cfdi_data['move_line_id'] = line.id
                        cfdi_obj.create(cfdi_data)


        if self.polizas_de_facturas_de_pagos:
             #payments
             payments = self.env['account.payment'].search([('payment_date','>=',self.fecha_inicio),
                                                            ('payment_date','<=', self.fecha_fin),
                                                           # ('estado_pago','=','pago_correcto'),
                                                            ('state','not in', ['draft', 'cancelled'])
                                                            ])
            
             move_lines = payments.mapped('move_line_ids')
             if move_lines:
                 move_lines.write({'contabilidad_electronica':True})
                 move_lines.mapped('move_id').write({'contabilidad_electronica':True})

             #cfdi_obj = self.env['account.move.cfdi33']
             #for payment in payments:
             #    for move in payment.move_line_ids.mapped('move_id'):
             #        cfdi_obj.create({'move_id': move.id,'fecha': payment.fecha_pago, 'folio': payment.name, 'uuid': payment.folio_fiscal, 'partner_id': payment.partner_id.id,
             #                         'monto': payment.amount, 'moneda': inv.moneda, 'tipocamb': inv.tipocambio, 'rfc_cliente': inv.partner_id.rfc})

             #effectively paid
             for payment in payments:
                   payment.diot = True
                   _logger.info("move name %s", payment.move_name)
                   effective_pay = self.env['account.move'].search([('ref','=',payment.move_name)],limit=1)
                   _logger.info("pasa 1")
                   if effective_pay:
                      _logger.info("pasa 2")
                      effective_pay.write({'contabilidad_electronica':True})
                      move_lines = effective_pay.line_ids
                      _logger.info("pasa 3")
                      for move in move_lines:
                         _logger.info("pasa 4")
                         move_lines.write({'contabilidad_electronica':True})
                         _logger.info("pasa 5")
                    #move_lines.mapped('move_id').write({'contabilidad_electronica':True})

        if self.polizas_de_micelaneos:
            moves = self.env['account.move'].search([('date','>=',self.fecha_inicio),
                                             ('date','<=', self.fecha_fin),
                                             ('state','=', 'posted')
                                             ('journal_id.type','=','general'),
                                             ])
            if moves:
                moves.write({'contabilidad_electronica':True})
                moves.mapped('line_ids').write({'contabilidad_electronica':True})
            
        return True
