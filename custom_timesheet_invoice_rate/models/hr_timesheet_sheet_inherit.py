from odoo import models,fields,api,_
from calendar import monthrange
from datetime import datetime,date

class HrTimesheetInherited(models.Model):
    _inherit ="hr_timesheet.sheet"

    @api.onchange('date_start','date_end')
    def calculate_days(self):
        start = self.date_start
        end = self.date_end
        total_days = end - start
        self.document_day = total_days.days+1

    @api.depends('no_of_unpaid_leave')
    def calculate_unpaid_leave(self):
        hr_leave_id =self.env['hr.leave'].search([('employee_id','in',[self.employee_id.id])])
        days = 0
        for val in hr_leave_id:
            # print('val create_date',val.create_date)
            created_result = datetime.strptime(str(val.create_date).strip('\t\r\n'),'%Y-%m-%d %H:%M:%S.%f')
            create_month = created_result.strftime("%B")
            create_year = created_result.strftime("%Y")
            today = datetime.today()
            # print('print today', today)
            today_result = datetime.strptime(str(today),'%Y-%m-%d %H:%M:%S.%f')
            today_month = today_result.strftime("%B")
            today_year = today_result.strftime("%Y")
            if val.holiday_status_id.name == 'Unpaid' and val.state == 'validate' and create_month == today_month and create_year == today_year:
                days += val.number_of_days
        self.no_of_unpaid_leave = days

    @api.depends('client_holiday')
    def calculate_client_holiday(self):
        hr_leave_id = self.env['hr.leave'].search([('employee_id', 'in', [self.employee_id.id])])
        holiday = 0
        for val in hr_leave_id:
            if val.holiday_status_id.name == 'Client Paid Time Off' and val.state == 'validate' :
                holiday += val.number_of_days
        self.client_holiday = holiday

    @api.depends('no_of_working_day')
    def calculate_working_days(self):
        unpaid_leave = self.no_of_unpaid_leave
        client_holiday = self.client_holiday
        if self.document_day > 0:
            work_day = (float(self.document_day) - unpaid_leave) + client_holiday
            self.no_of_working_day = work_day
        else:
            self.no_of_working_day = False

    @api.depends('per_day_rate')
    def calculate_per_day_rate(self):
        po_rate = float(self.employee_id.po_rate)
        no_of_calender_day  = float(self.document_day)
        if int(po_rate) > 0 and int(no_of_calender_day) > 0 :
            working_days = po_rate / no_of_calender_day
            self.per_day_rate = working_days
        else:
            self.per_day_rate = False

    @api.depends('invoice_rate')
    def calculate_invoice_rate(self):
        no_of_working_day = float(self.no_of_working_day)
        per_day_rate = float(self.per_day_rate)
        if int(no_of_working_day) > 0:
            invoice_rate = per_day_rate * no_of_working_day
            self.invoice_rate = invoice_rate
        else:
            self.invoice_rate = False




    @api.depends('timesheet_ids')
    def customer_name_tree_view(self):
        self.customer_name =False
        for rec in self:
            if rec.timesheet_ids:
                project = rec.timesheet_ids.mapped('project_id')
            if project:
                final_project = project[-1]
                customer_name = final_project.partner_id.name
                rec.customer_name = customer_name

    document_day = fields.Integer(compute='calculate_days',string="No of Calendar Day")
    no_of_leave_approved = fields.Float(string="No of Leave Approve( Paid time off)",default=2,readonly=True)
    no_of_unpaid_leave = fields.Float(strig="No of Unpaid Leave",compute='calculate_unpaid_leave')
    client_holiday = fields.Float(string="Client Holiday",compute='calculate_client_holiday')
    no_of_working_day = fields.Float(string="No of Working Day",compute='calculate_working_days')
    per_day_rate = fields.Monetary(string="Per Day Rate",compute='calculate_per_day_rate')
    invoice_rate = fields.Monetary(string="Invoice Rate",compute='calculate_invoice_rate')
    customer_name = fields.Char(string="Customer Name",compute='customer_name_tree_view')
    currency_id = fields.Many2one('res.currency',string="Currency")