# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import requests
import json
from odoo.exceptions import Warning, UserError
import logging
_logger = logging.getLogger(__name__)
from datetime import datetime

class PolizasReport(models.TransientModel):
    _name = 'polizas.report'
    
    start_date = fields.Date("Fecha inicio")
    end_date = fields.Date("Fecha fin")
    journal_ids = fields.Many2many('account.journal',string='Diarios', default=lambda self: self.env['account.journal'].search([]))
    
    
    def action_print_polizas_report(self):
        ctx = self._context.copy()
        domain = [('journal_id', 'in',self.journal_ids.ids)]
        if self.start_date:
            domain.append(('date','>=',self.start_date))
        if self.end_date:
            domain.append(('date','<=',self.end_date))
        
        journal_entries = self.env['account.move'].search(domain)
        company = self.env.user.company_id
        archivo_cer = company.archivo_cer
        archivo_key = company.archivo_key
        request_params = { 
                'company': {
                      'rfc': company.rfc,
                      'api_key': company.proveedor_timbrado,
                      'modo_prueba': company.modo_prueba,
                },
                'informacion':{
                      'proceso': 'polizas',
                      'fecha_inicio': datetime.strftime(self.start_date, '%Y-%m-%d %H:%M:%S') or '', #self.start_date or '',
                      'fecha_fin': datetime.strftime(self.end_date, '%Y-%m-%d %H:%M:%S') or '', #self.end_date or '',
                },
                'certificados': {
                      'archivo_cer': archivo_cer.decode("utf-8") or False,
                      'archivo_key': archivo_key.decode("utf-8") or False,
                      'contrasena': company.contrasena,
                },}
        polizas = []
        for move in journal_entries:
            
            mv_vals = {
                'nombre' : move.name,
                'reference' : move.ref or '',
                'diario' : move.journal_id.name,
                'fecha' : datetime.strftime(move.date, '%Y-%m-%d %H:%M:%S'), #move.date,
                }
            transaccion = []
            for line in move.line_ids:
                if len(line.account_cfdi_ids) >= 1:
                    cfdi_line = line.account_cfdi_ids[0]
                    transaccion.append({
                       'cuenta' : line.account_id.name or '',
                       'codigo' : line.account_id.code or '',
                       'cliente' : line.partner_id.name or '',
                       'label' : line.name or '',
                       'debe' : line.debit,
                       'haber' : line.credit,
                       'compnal':{
                           'uuid' : cfdi_line.uuid,
                           'rfc' : cfdi_line.rfc_cliente,
                           'monto' : cfdi_line.monto,
                           'moneda' : cfdi_line.moneda,
                           'tipcamb' : cfdi_line.tipocamb,
                           },
                       })
                else:
                    transaccion.append({
                       'cuenta' : line.account_id.name or '',
                       'codigo' : line.account_id.code or '',
                       'cliente' : line.partner_id.name or '',
                       'label' : line.name or '',
                       'debe' : line.debit,
                       'haber' : line.credit,
                       })
            mv_vals.update({'transaccion' : transaccion})
            polizas.append(mv_vals)
        request_params.update({'polizas': polizas})
        
        url=''
        company = self.env.user.company_id
        if company.proveedor_timbrado == 'multifactura':
            url = '%s' % ('http://facturacion.itadmin.com.mx/api/contabilidad')
        elif company.proveedor_timbrado == 'multifactura2':
            url = '%s' % ('http://facturacion2.itadmin.com.mx/api/contabilidad')
        elif company.proveedor_timbrado == 'multifactura3':
            url = '%s' % ('http://facturacion3.itadmin.com.mx/api/contabilidad')
        elif company.proveedor_timbrado == 'gecoerp':
            if company.modo_prueba:
                url = '%s' % ('https://itadmin.gecoerp.com/invoice/?handler=OdooHandler33')
            else:
                url = '%s' % ('https://itadmin.gecoerp.com/invoice/?handler=OdooHandler33')
        if not url:
            raise Warning("Seleccione el proveedor de timbrado en la configuración de la compañía.")
        
        response = requests.post(url,auth=None,verify=False, data=json.dumps(request_params),headers={"Content-type": "application/json"})
        _logger.info('something ... %s', response.text)

        json_response = response.json()
        estado_factura = json_response.get('estado_conta','')
        if estado_factura == 'problemas_contabilidad':
            raise UserError(_(json_response['problemas_message']))
        if json_response.get('conta_xml'):
            
            #_logger.info("xml %s", json_response['conta_xml'])
            #_logger.info("zip %s", json_response['conta_zip'])

            #return base64.b64decode(json_response['conta_xml'])
            try:
                form_id = self.env['ir.model.data'].get_object_reference('contabilidad_cfdi', 'reporte_conta_xml_zip_download_wizard_download_form_view_itadmin')[1]
            except ValueError:
                form_id = False
            ctx.update({'default_xml_data': json_response['conta_xml'], 'default_zip_data': json_response.get('conta_zip', None)})    
            return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'conta.xml.zip.download',
                'views': [(form_id, 'form')],
                'view_id': form_id,
                'target': 'new',
                'context': ctx,
            }
        return True
    