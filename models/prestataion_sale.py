# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta
from odoo import models, fields,api


class ResPartnerPres(models.Model):
    _inherit = 'res.partner'

    number_pres = fields.Integer(string='Nombre de Prestation',compute='_compute_prestataion_count' )


    def _compute_prestataion_count(self):
        sale_data = self.env['medical.prestation_sale'].read_group(domain=[('partner_id', 'child_of', self.ids)],
                                                      fields=['partner_id'], groupby=['partner_id'])
        # read to keep the child/parent relation while aggregating the read_group result in the loop
        partner_child_ids = self.read(['child_ids'])
        mapped_data = dict([(m['partner_id'][0], m['partner_id_count']) for m in sale_data])
        for partner in self:
            # let's obtain the partner id and all its child ids from the read up there
            partner_ids = filter(lambda r: r['id'] == partner.id, partner_child_ids)[0]
            partner_ids = [partner_ids.get('id')] + partner_ids.get('child_ids')
            # then we can sum for all the partner's child
            partner.number_pres = sum(mapped_data.get(child, 0) for child in partner_ids)

class ProductPrestataion(models.Model):
    _inherit = 'product.category'

    medecament = fields.Boolean(string='Ordonance')
    prestation = fields.Boolean(string='Prestation')




class PatientPrestataion(models.Model):
    _inherit = 'res.partner'

    date_naissance = fields.Date(string='Date de naissance')
    nss_pat = fields.Char(string='NSS')
    age = fields.Char(string='Age', compute='compute_age')
    date_actuel = fields.Datetime(string='Date', default=lambda s: fields.Datetime.now(), invisible=True)

    @api.multi
    def compute_age(self):
        for data in self:
            if data.date_naissance:
                date_naissance = fields.Datetime.from_string(data.date_naissance)
                date = fields.Datetime.from_string(data.date_actuel)
                delta = relativedelta(date, date_naissance)
            data.age = str(delta.years) + ' ans'



class LignePrestataion(models.Model):
    _name = 'sale.order.line'
    _description = "Prestation patient"
    
    
    _inherit = 'sale.order.line'

    prduitcategory = fields.Many2one('product.category', string='Catégorie des produits', domain = "[('prestation','=',True)]")

    
    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return {'domain': {'product_uom': []}}

        vals = {}
        domain = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
            vals['product_uom'] = self.product_id.uom_id
            vals['product_uom_qty'] = 1.0

        product = self.product_id.with_context(
            lang=self.order_id.partner_id.lang,
            partner=self.order_id.partner_id.id,
            quantity=vals.get('product_uom_qty') or self.product_uom_qty,
            date=self.order_id.date_order,
            pricelist=self.order_id.pricelist_id.id,
            uom=self.product_uom.id
        )

        name = product.name_get()[0][1]
        if product.description_sale:
            name += '\n' + product.description_sale
        vals['name'] = name

        self._compute_tax_id()

        if self.order_id.pricelist_id and self.order_id.partner_id:
            vals['price_unit'] = product.list_price
        else :
            vals['price_unit'] = product.list_price
        self.update(vals)

        title = False
        message = False
        warning = {}
        if product.sale_line_warn != 'no-message':
            title = _("Warning for %s") % product.name
            message = product.sale_line_warn_msg
            warning['title'] = title
            warning['message'] = message
            if product.sale_line_warn == 'block':
                self.product_id = False
            return {'warning': warning}
        return {'domain': domain}


class MedicalPrestaion(models.Model):
    _name = 'medical.prestation_sale'
    _description = "Prestation patient"
    _rec_name = 'name_prestation'
    
    _inherits = {'sale.order':'sale_id'}

    date = fields.Date(default=fields.Date.today)
    demandeur = fields.Many2one('res.partner', string='Demandeur', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},change_default=True, index=True)
    partner_id_socity = fields.Many2one('res.partner', string='Customer', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},change_default=True, index=True)
    pec_interne = fields.Boolean(string="PEC soins en interne")
    pec_etranger = fields.Boolean(string="PEC soins à l'étragere")
    name_prestation = fields.Text(string="ID")
    couverture_med_san = fields.Selection(
        [('1', 'Evènementiel culturel'), ('2', 'Evènementiel sportif'),
         ('3', 'Entreprise')], 'Couverture médico-sanitaire')
    type_demande = fields.Selection(
        [('1', 'Lui-meme'), ('2', 'Ayant droit'),
         ], 'Type demandeur')
    garde_malade = fields.Selection(
        [('1', '24H'), ('2', '08H'),
         ('3', '12H')], 'Garde malade')
    pathology = fields.Char(string='Pathologie')
    etat_clinique = fields.Char(string='Etat clinique')
    point_depart_reel =fields.Char(string="Point de départ réel")
    point_chute_reel =fields.Char(string="Point de chutte réel")
    agence = fields.Many2one('lab.request', string='Agence')
    type_patient = fields.Selection(
        [('1', 'Particlier'), ('2', 'Conventionner'),
         ('3', 'Non Conventionner')], 'Type patient')
    heure_appel = fields.Datetime(string='Date d\'appel', default=fields.Datetime.now)
    heure_souhaite = fields.Datetime(string='Date souhaité', default=fields.Datetime.now)
    point_depart = fields.Char(string="Point de départ")
    point_chute = fields.Char(string="Point de chutte")
    aller_simple = fields.Boolean(default=True,string="Aller simple")
    aller_retour = fields.Boolean(string="Aller/Retour")
    patient = fields.Many2one('lab.patient', string='Patient', )
    equipe_interv = fields.Many2one('crm.team', string='Equipe intervenante' )
    
    observation = fields.Text(string='Observation')
    conclusion = fields.Text(string='Conclusion')
    examen_simple=fields.Boolean(string="Examen simple")
    
    urgence = fields.Boolean(string="Urgence")
    fiche_liaison_state = fields.Boolean(string="Fiche liaison")
    vers = fields.Char(string="VERS")
    transfert_de = fields.Char(string="TRANSFERT DE")
    motif_transport = fields.Char(string="MOTIF DE TRANSFERT")
    temps_attente = fields.Integer(string="Heure d'attente")
    accord = fields.Boolean(string="ACCORD DU SERVICE D\'ACCEUIL")
    type_transfert = fields.Selection([
        ('1', 'MEDICALISE'),
        ('2', 'PARAMEDICALISE')        
    ], string='TYPE DE TRANSFERT')
    state = fields.Selection([
        ('draft', 'Prestation'),
        ('sent', 'Prestation envoyé'),
        ('sale', 'Fin de mission'),
        ('done', 'Locked'),
        ('cancel', 'Annulé'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')
    test_fact = fields.Char(string='test', compute='compute_test')


    
   

    @api.model
    def create(self, vals):
        vals['name_prestation'] = self.env['ir.sequence'].next_by_code('medical.prestation_sale') or 'New'
        vals['name'] = self.env['ir.sequence'].next_by_code('sale.order') or 'New'
        return super(MedicalPrestaion, self).create(vals)
    @api.multi
    def compute_test(self):

        self.env.cr.execute("select SUM(balance)from account_move_line join account_account on account_move_line.account_id= account_account.id where account_account.code like '%700%' " )
        self.test_fact = self.env.cr.fetchone()[0]
    

    @api.multi
    def action_confirm(self):
        for order in self:
            order.state = 'sale'
            order.confirmation_date = fields.Datetime.now()
            if self.env.context.get('send_email'):
                self.force_quotation_send()
            order.order_line._action_procurement_create()
        if self.env['ir.values'].get_default('sale.config.settings', 'auto_done_setting'):
            self.action_done()
        return True



        




class PassifReport(models.TransientModel):
    _name = "passif.report"
    _inherit = "account.common.report"
    _description = "Passif Report"

    @api.model
    def _get_account_report(self):
        reports = []
        if self._context.get('active_id'):
            menu = self.env['ir.ui.menu'].browse(self._context.get('active_id')).name
            reports = self.env['account.financial.report'].search([('name', 'ilike', menu)])
        return reports and reports[0] or False

    enable_filter = fields.Boolean(string='Enable Comparison')
    account_report_id = fields.Many2one('account.financial.report', string='Account Reports', required=True, default=_get_account_report)
    label_filter = fields.Char(string='Column Label', help="This label will be displayed on report to show the balance computed for the given comparison filter.")
    filter_cmp = fields.Selection([('filter_no', 'No Filters'), ('filter_date', 'Date')], string='Filter by', required=True, default='filter_no')
    date_from_cmp = fields.Date(string='Start Date')
    date_to_cmp = fields.Date(string='End Date')
    debit_credit = fields.Boolean(string='Display Debit/Credit Columns', help="This option allows you to get more details about the way your balances are computed. Because it is space consuming, we do not allow to use it while doing a comparison.")

    def _build_comparison_context(self, data):
        result = {}
        result['journal_ids'] = 'journal_ids' in data['form'] and data['form']['journal_ids'] or False
        result['state'] = 'target_move' in data['form'] and data['form']['target_move'] or ''
        if data['form']['filter_cmp'] == 'filter_date':
            result['date_from'] = data['form']['date_from_cmp']
            result['date_to'] = data['form']['date_to_cmp']
            result['strict_range'] = True
        return result

    @api.multi
    def check_report(self):
        res = super(PassifReport, self).check_report()
        data = {}
        data['form'] = self.read(['account_report_id', 'date_from_cmp', 'date_to_cmp', 'journal_ids', 'filter_cmp', 'target_move'])[0]
        for field in ['account_report_id']:
            if isinstance(data['form'][field], tuple):
                data['form'][field] = data['form'][field][0]
        comparison_context = self._build_comparison_context(data)
        res['data']['form']['comparison_context'] = comparison_context
        return res

    def _print_report(self, data):
        data['form'].update(self.read(['date_from_cmp', 'debit_credit', 'date_to_cmp', 'filter_cmp', 'account_report_id', 'enable_filter', 'label_filter', 'target_move'])[0])
        return self.env['report'].get_action(self, 'account.report_financial', data=data)


       

        


    






    



