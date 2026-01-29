import csv
import io
import xml.etree.ElementTree as ET
from xml.dom import minidom
from django.apps import apps
from .rti_mapping import get_rti_data_map, get_safe_payment_date
from .engine import ReportEngine

class RTIGenerator:
    def __init__(self, company_id, period_id):
        self.company_id = company_id
        self.period_id = period_id
        
        Company = apps.get_model('company', 'Company')
        # FIX: Load the correct model 'PayrollPeriod'
        PayrollPeriod = apps.get_model('payroll', 'PayrollPeriod')
        
        self.company = Company.objects.get(pk=company_id)
        # Load the specific Period
        self.period = PayrollPeriod.objects.get(pk=period_id)
        # The parent Payroll definition
        self.payroll = self.period.payroll 

    def _get_financial_data(self):
        Employee = apps.get_model('employee', 'Employee')
        employees = Employee.objects.filter(company_id=self.company_id)
        results_map = {}
        
        for emp in employees:
            # Pass self.period (which contains the Payment Date)
            rti_static = get_rti_data_map(emp, self.period)
            
            # Placeholder for financials
            financials = {
                'GrossPay': 0.00,
                'TaxPaid': 0.00,
                'NationalInsurance': 0.00,
                'NetPay': 0.00
            }
            results_map[emp.id] = {**rti_static, **financials}
            
        return results_map

    def _get_employer_refs(self):
        paye_ref = getattr(self.company, 'tax_id_01', '') or ''
        accounts_ref = getattr(self.company, 'tax_id_02', '') or ''
        
        office_num = "000"
        office_ref = "00000"
        
        if '/' in paye_ref:
            parts = paye_ref.split('/', 1)
            office_num = parts[0].strip()
            office_ref = parts[1].strip()
        elif len(paye_ref) > 3:
            office_num = paye_ref[:3]
            office_ref = paye_ref[3:]
            
        return office_num, office_ref, accounts_ref

    def generate_xml(self):
        data_map = self._get_financial_data()
        office_num, office_ref, accounts_ref = self._get_employer_refs()
        
        root = ET.Element('GovTalkMessage', xmlns="http://www.govtalk.gov.uk/CM/envelope")
        
        header = ET.SubElement(root, 'Header')
        message_details = ET.SubElement(header, 'MessageDetails')
        ET.SubElement(message_details, 'Class').text = 'HMRC-PAYE-RTI-FPS'
        ET.SubElement(message_details, 'Qualifier').text = 'request'
        ET.SubElement(message_details, 'Function').text = 'submit'
        
        body = ET.SubElement(root, 'Body')
        ir_envelope = ET.SubElement(body, 'IRenvelope', xmlns="http://www.govtalk.gov.uk/taxation/PAYE/RTI/FullPaymentSubmission/18-19")
        
        ir_header = ET.SubElement(ir_envelope, 'IRheader')
        keys = ET.SubElement(ir_header, 'Keys')
        ET.SubElement(keys, 'Key', Type='TaxOfficeNumber').text = office_num
        ET.SubElement(keys, 'Key', Type='TaxOfficeReference').text = office_ref
        
        # Use Period Date directly from self.period
        payment_date = self.period.payment_date
        period_end = payment_date.replace(day=5) 
        
        ET.SubElement(ir_header, 'PeriodEnd').text = str(period_end)
        ET.SubElement(ir_header, 'Principal').text = self.company.trade_name or "Unknown"
        
        fps = ET.SubElement(ir_envelope, 'FullPaymentSubmission')
        ET.SubElement(fps, 'PaymentDate').text = str(payment_date)
        ET.SubElement(fps, 'OfficeNo').text = office_num
        ET.SubElement(fps, 'ReferenceNo').text = office_ref
        ET.SubElement(fps, 'EmployerAccountsRef').text = accounts_ref
        
        for emp_id, data in data_map.items():
            emp_block = ET.SubElement(fps, 'Employee')
            
            details = ET.SubElement(emp_block, 'EmployeeDetails')
            ET.SubElement(details, 'NINO').text = data['NINO'] or ''
            
            name = ET.SubElement(details, 'Name')
            ET.SubElement(name, 'Forename').text = data['Name']['Forename']
            ET.SubElement(name, 'Surname').text = data['Name']['Surname']
            
            ET.SubElement(details, 'BirthDate').text = data['BirthDate']
            ET.SubElement(details, 'Gender').text = data['Gender']
            
            addr = ET.SubElement(details, 'Address')
            for key in ['Line1', 'Line2', 'Line3', 'Line4', 'PostCode']:
                val = data['Address'].get(key)
                if val:
                    ET.SubElement(addr, key).text = val
            
            employment = ET.SubElement(emp_block, 'Employment')
            ET.SubElement(employment, 'PayId').text = str(emp_id)
            if data['Employment']['DirectorStatus'] == 'Yes':
                ET.SubElement(employment, 'DirectorStatus').text = 'Director'
            
            figures = ET.SubElement(emp_block, 'Figures')
            ET.SubElement(figures, 'TaxablePay').text = "{:.2f}".format(data['GrossPay'])
            ET.SubElement(figures, 'TotalTax').text = "{:.2f}".format(data['TaxPaid'])
            ET.SubElement(figures, 'StudentLoanRecovered').text = "0.00" 

        xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="   ")
        return xml_str

    def generate_csv(self):
        data_map = self._get_financial_data()
        output = io.StringIO()
        
        headers = [
            'Employee ID', 'NINO', 'Forename', 'Surname', 'DOB', 'Gender',
            'Address', 'Start Date', 'Director', 'Irregular Payment',
            'Starter Declaration', 'Late Reason',
            'Gross Pay', 'Tax Paid', 'NI'
        ]
        
        writer = csv.writer(output)
        writer.writerow(headers)
        
        for emp_id, data in data_map.items():
            addr_str = ", ".join([v for k,v in data['Address'].items() if v])
            
            row = [
                emp_id,
                data['NINO'],
                data['Name']['Forename'],
                data['Name']['Surname'],
                data['BirthDate'],
                data['Gender'],
                addr_str,
                data['Employment']['StartDate'],
                data['Employment']['DirectorStatus'],
                data['Employment']['IrregularPayment'],
                data['TaxAndNI']['StarterDeclaration'],
                data['Submission']['LateReason'],
                "{:.2f}".format(data['GrossPay']),
                "{:.2f}".format(data['TaxPaid']),
                "{:.2f}".format(data['NationalInsurance'])
            ]
            writer.writerow(row)
            
        return output.getvalue()