from django import forms
from django.core.exceptions import ValidationError
import re
from Exactus.company.models import Company
from Exactus.company.registry import register_company_form

# ================================================================
# 🌍 GLOBAL COUNTRY CONFIGURATION
# ================================================================

COUNTRY_FIELD_RULES = {
    "BR": {  # BRAZIL
        "labels": {
            "company_number": "Número da Empresa",
            "company_code": "Código da Empresa",
            "trade_name": "Nome Fantasia",
            "legal_name": "Razão Social",
            
            # Address
            "building_name": "Logradouro",
            "road_name_1": "Nome da rua",
            "road_name_2": "Complemento",
            "town": "Cidade",
            "county": "Estado",
            "post_code": "CEP",
            "country": "País",
            
            # Tax IDs
            "tax_id_01": "CNPJ",
            "tax_id_02": "Inscrição Estadual (IE)",
            "tax_id_03": "Inscrição Municipal (IM)",
            "tax_id_04": "CNAE Principal",
            "tax_id_05": "CNAEs Secundárias",
            "tax_id_06": "Regime Tributário",
            "tax_id_07": "PIS/PASEP",
            "tax_id_08": "COFINS",
            "tax_id_09": "IRPJ",
            "tax_id_10": "CSLL",
            
            # Banking (mapped to bank_01 to bank_20)
            "bank_01": "Nome do Banco",
            "bank_02": "Código do Banco",
            "bank_03": "Número da Agência",
            "bank_04": "Dígito da Agência",
            "bank_05": "Número da Conta",
            "bank_06": "Dígito da Conta",
            "bank_07": "Tipo de Conta",
            "bank_08": "CNPJ da Conta",
            "bank_09": "Titular da Conta",
            "bank_10": "Chave PIX",
            "bank_11": "Tipo Chave PIX",
            "bank_12": "CBU",
            "bank_13": "Endereço da Agência",
            "bank_14": "Cidade da Agência",
            "bank_15": "Telefone do Banco",
            "bank_16": "E-mail Bancário",
            "bank_17": "Data Abertura Conta",
            "bank_18": "Limite da Conta",
            "bank_19": "Observações",
            "bank_20": "Código Pagamento FGTS",
            
            # eSocial/Government Registrations
            "government_id_01": "Código Empregador eSocial",
            "government_id_02": "Código CAIXA FGTS",
            "government_id_03": "Número CAGED",
            "government_id_04": "CRC Contador",
            
            # Company Structure
            "company_structure": "Tipo Empresa",
            "number_of_employees": "Número de Funcionários",
            "pay_frequency": "Frequência de Pagamento",
            "pay_day": "Dia do Pagamento",
            "standard_work_hours": "Jornada Semanal",
            
            # Contact Information
            "contact_person": "Responsável Legal",
            "contact_cpf": "CPF do Responsável",
            "contact_phone": "Telefone Comercial",
            "contact_email": "E-mail Comercial",
            "accountant_name": "Nome do Contador",
            "accountant_crc": "CRC do Contador",
        },

        "hidden": {
            "tax_id_11","tax_id_12","tax_id_13", "rti_password",
            "tax_id_14","tax_id_15","tax_id_16","tax_id_17",
            "tax_id_18","tax_id_19","tax_id_20", "rti_user_id",

    },

        "placeholders": {
            "tax_id_01": "00.000.000/0000-00",
            "postal_code": "00000-000",
            "bank_02": "001, 341, 237...",
            "bank_03": "1234",
            "bank_05": "123456-7",
            "contact_cpf": "000.000.000-00",
        },
        "helptext": {
            "tax_id_01": "Informe o CNPJ completo da empresa (14 dígitos).",
            "tax_id_02": "Inscrição Estadual (obrigatória para ICMS).",
            "tax_id_04": "Código CNAE principal da atividade.",
            "tax_id_06": "Simples Nacional, Lucro Presumido ou Lucro Real.",
            "bank_10": "Chave PIX para pagamentos instantâneos.",
            "bank_12": "Clave Bancária Uniforme (opcional).",
        },
        "required_fields": [
            "company_code", "trade_name", "legal_name", "tax_id_01",
            "address_line_1", "city", "state", "postal_code",
            "bank_01", "bank_02", "bank_03", "bank_05", "bank_09",
            "contact_person", "contact_phone", "contact_email"
        ],
        "choices": {
            "company_structure": [
                ("", "Selecione..."),
                ("LTDA", "Sociedade Limitada (Ltda.)"),
                ("SA", "Sociedade Anônima (S/A)"),
                ("EI", "Empresário Individual"),
                ("MEI", "Microempreendedor Individual"),
                ("EPP", "Empresa de Pequeno Porte"),
            ],
            "tax_id_06": [
                ("", "Selecione..."),
                ("SIMPLES", "Simples Nacional"),
                ("PRESUMIDO", "Lucro Presumido"),
                ("REAL", "Lucro Real"),
                ("MEI", "MEI"),
            ],
            "bank_07": [
                ("", "Selecione..."),
                ("CORRENTE", "Conta Corrente"),
                ("POUPANCA", "Conta Poupança"),
                ("SALARIO", "Conta Salário"),
                ("PAGAMENTOS", "Conta Pagamentos"),
            ],
            "bank_11": [
                ("", "Selecione..."),
                ("CPF", "CPF"),
                ("CNPJ", "CNPJ"),
                ("EMAIL", "E-mail"),
                ("TELEFONE", "Telefone"),
                ("ALEATORIA", "Chave Aleatória"),
            ],
            "pay_frequency": [
                ("", "Selecione..."),
                ("SEMANAL", "Semanal"),
                ("QUINZENAL", "Quinzenal"),
                ("MENSAL", "Mensal"),
            ],
        },
    },

    "AU": {  # AUSTRALIA
        "labels": {
            "company_number": "Australian Company Number (ACN)",
            "company_code": "Company Code",
            "trade_name": "Trading Name",
            "legal_name": "Legal Name",
            
            # Address
            "address_line_1": "Street Address",
            "address_line_2": "Address Line 2",
            "city": "Suburb/Town",
            "state": "State/Territory",
            "postal_code": "Postcode",
            "country": "Country",
            
            # Tax IDs
            "tax_id_01": "Australian Business Number (ABN)",
            "tax_id_02": "Tax File Number (TFN)",
            "tax_id_03": "PAYG Withholding Number",
            "tax_id_04": "GST Registration",
            "tax_id_05": "Fringe Benefits Tax (FBT)",
            "tax_id_06": "Payroll Tax Number",
            "tax_id_07": "WorkCover Number",
            "tax_id_08": "Superannuation Fund Number",
            
            # Banking
            "bank_01": "Bank Name",
            "bank_02": "Account Holder Name",
            "bank_03": "BSB Number",
            "bank_04": "Account Number",
            "bank_05": "Account Type",
            "bank_06": "Bank Address",
            "bank_07": "Bank City",
            "bank_08": "Bank State",
            "bank_09": "Bank Postcode",
            "bank_10": "Payment Reference",
            "bank_11": "Direct Debit Authority",
            "bank_12": "Bank Phone",
            "bank_13": "Bank Email",
            "bank_14": "Super Fund BSB",
            "bank_15": "Super Fund Account",
            "bank_16": "Super Fund Name",
            "bank_17": "Account Opening Date",
            "bank_18": "Last Updated",
            "bank_19": "Payment Method",
            "bank_20": "Banking Notes",
            
            # Government Registrations
            "government_id_01": "STP Business ID",
            "government_id_02": "Single Touch Payroll ID",
            "government_id_03": "Workers Compensation Policy",
            "government_id_04": "Long Service Leave ID",
            
            # Company Structure
            "company_structure": "Business Structure",
            "number_of_employees": "Number of Employees",
            "pay_frequency": "Pay Frequency",
            "pay_day": "Pay Day",
            "standard_work_hours": "Standard Hours per Week",
            
            # Contact Information
            "contact_person": "Director/Manager",
            "contact_phone": "Business Phone",
            "contact_email": "Business Email",
            "accountant_name": "Accountant Name",
            "accountant_tfn": "Accountant TFN",
        },
        "hidden": {
            "tax_id_09","tax_id_10",
            "tax_id_11","tax_id_12","tax_id_13", "rti_password",
            "tax_id_14","tax_id_15","tax_id_16","tax_id_17",
            "tax_id_18","tax_id_19","tax_id_20", "rti_user_id",

            },
        "placeholders": {
            "tax_id_01": "00 000 000 000",
            "tax_id_02": "000 000 000",
            "bank_03": "000-000",
            "bank_04": "00000000",
            "postal_code": "0000",
        },
        "helptext": {
            "tax_id_01": "11 digit Australian Business Number",
            "tax_id_03": "PAYG Withholding registration number",
            "bank_03": "6 digit Bank-State-Branch number",
            "pay_frequency": "Weekly, Fortnightly, or Monthly",
        },
        "required_fields": [
            "company_code", "trade_name", "legal_name", "tax_id_01",
            "address_line_1", "city", "state", "postal_code",
            "bank_01", "bank_02", "bank_03", "bank_04",
            "contact_person", "contact_phone", "contact_email"
        ],
        "choices": {
            "company_structure": [
                ("", "Select..."),
                ("PTY_LTD", "Proprietary Limited (Pty Ltd)"),
                ("PUBLIC", "Public Company"),
                ("PARTNERSHIP", "Partnership"),
                ("SOLE_TRADER", "Sole Trader"),
                ("TRUST", "Trust"),
            ],
            "tax_id_04": [
                ("", "Select..."),
                ("REGISTERED", "GST Registered"),
                ("NOT_REGISTERED", "Not GST Registered"),
            ],
            "bank_05": [
                ("", "Select..."),
                ("SAVINGS", "Savings Account"),
                ("CHECKING", "Checking Account"),
                ("BUSINESS", "Business Account"),
                ("TRUST", "Trust Account"),
            ],
            "pay_frequency": [
                ("", "Select..."),
                ("WEEKLY", "Weekly"),
                ("FORTNIGHTLY", "Fortnightly"),
                ("MONTHLY", "Monthly"),
            ],
            "state": [
                ("", "Select State/Territory..."),
                ("NSW", "New South Wales"),
                ("VIC", "Victoria"),
                ("QLD", "Queensland"),
                ("WA", "Western Australia"),
                ("SA", "South Australia"),
                ("TAS", "Tasmania"),
                ("ACT", "Australian Capital Territory"),
                ("NT", "Northern Territory"),
            ],
        },
    },

    "GB": {  # UNITED KINGDOM
        "labels": {
            "company_number": "Company Registration Number",
            "company_code": "Company Code",
            "trade_name": "Trading Name",
            "legal_name": "Registered Name",
            
            # Address
            "address_line_1": "Building and Street",
            "address_line_2": "Address Line 2",
            "city": "Town/City",
            "state": "County",
            "postal_code": "Postcode",
            "country": "Country",
            
            # Tax IDs
            "tax_id_01": "PAYE Reference",
            "tax_id_02": "Accounts Office Reference",
            "tax_id_03": "VAT Registration Number",
            "tax_id_04": "Corporation Tax UTR",
            "tax_id_05": "Employer's NI Number",
            "tax_id_06": "Construction Industry Scheme",
            
            # Banking
            "bank_01": "Bank Name",
            "bank_02": "Account Holder Name",
            "bank_03": "Sort Code",
            "bank_04": "Account Number",
            "bank_05": "IBAN",
            "bank_06": "SWIFT/BIC",
            "bank_07": "Account Type",
            "bank_08": "Building Society Roll No",
            "bank_09": "Bank Address",
            "bank_10": "Bank City",
            "bank_11": "Bank Postcode",
            "bank_12": "Payment Reference",
            "bank_13": "Direct Debit Instruction",
            "bank_14": "Standing Order Details",
            "bank_15": "Bank Phone",
            "bank_16": "Bank Email",
            "bank_17": "Account Opening Date",
            "bank_18": "Last Updated",
            "bank_19": "Payment Method",
            "bank_20": "Banking Notes",
            
            # Government Registrations
            "government_id_01": "HMRC Online Services ID",
            "government_id_02": "Pension Regulator ID",
            "government_id_03": "Workplace Pension Scheme",
            "government_id_04": "Auto-enrolment Staging Date",
            
            # Company Structure
            "company_structure": "Company Type",
            "number_of_employees": "Number of Employees",
            "pay_frequency": "Pay Frequency",
            "pay_day": "Pay Day",
            "standard_work_hours": "Standard Weekly Hours",
            
            # Contact Information
            "contact_person": "Director/Manager",
            "contact_phone": "Business Phone",
            "contact_email": "Business Email",
            "accountant_name": "Accountant Name",
            "accountant_aca": "Accountant ACA Number",
        },
        "placeholders": {
            "tax_id_01": "123/AB45678",
            "tax_id_03": "GB999 9999 73",
            "bank_03": "00-00-00",
            "bank_04": "12345678",
            "postal_code": "SW1A 1AA",
        },
        "helptext": {
            "tax_id_01": "PAYE reference from HMRC",
            "tax_id_03": "VAT registration number (if applicable)",
            "bank_03": "6 digit sort code",
            "bank_05": "International Bank Account Number",
        },
        "required_fields": [
            "company_code", "trade_name", "legal_name", "tax_id_01",
            "address_line_1", "city", "postal_code",
            "bank_01", "bank_02", "bank_03", "bank_04",
            "contact_person", "contact_phone", "contact_email"
        ],
        "choices": {
            "company_structure": [
                ("", "Select..."),
                ("LTD", "Private Limited Company (Ltd)"),
                ("PLC", "Public Limited Company (PLC)"),
                ("LLP", "Limited Liability Partnership"),
                ("PARTNERSHIP", "Partnership"),
                ("SOLE_TRADER", "Sole Trader"),
            ],
            "bank_07": [
                ("", "Select..."),
                ("PERSONAL", "Personal Account"),
                ("BUSINESS", "Business Account"),
                ("JOINT", "Joint Account"),
            ],
            "pay_frequency": [
                ("", "Select..."),
                ("WEEKLY", "Weekly"),
                ("FORTNIGHTLY", "Fortnightly"),
                ("FOUR_WEEKLY", "Four Weekly"),
                ("MONTHLY", "Monthly"),
            ],
        },
    },

    "AR": {  # ARGENTINA
        "labels": {
            "company_number": "Número de Empresa",
            "company_code": "Código de Empresa",
            "trade_name": "Nombre Comercial",
            "legal_name": "Razón Social",
            
            # Address
            "address_line_1": "Calle",
            "address_line_2": "Número",
            "city": "Localidad",
            "state": "Provincia",
            "postal_code": "Código Postal",
            "country": "País",
            
            # Tax IDs
            "tax_id_01": "CUIT",
            "tax_id_02": "IIBB (Ingresos Brutos)",
            "tax_id_03": "IVA Condition",
            "tax_id_04": "Monotributo Category",
            "tax_id_05": "Autónomo Registration",
            "tax_id_06": "Sindicato Registration",
            
            # Banking
            "bank_01": "Banco",
            "bank_02": "Nombre del Titular",
            "bank_03": "CBU",
            "bank_04": "Alias CBU",
            "bank_05": "Tipo de Cuenta",
            "bank_06": "Sucursal",
            "bank_07": "Dirección del Banco",
            "bank_08": "Localidad del Banco",
            "bank_09": "Provincia del Banco",
            "bank_10": "Moneda",
            "bank_11": "Límite de Cuenta",
            "bank_12": "Teléfono del Banco",
            "bank_13": "Email Bancario",
            "bank_14": "Fecha Apertura",
            "bank_15": "Última Actualización",
            "bank_16": "Observaciones",
            "bank_17": "CVU (Mercado Pago)",
            "bank_18": "Alias Mercado Pago",
            "bank_19": "Datos Adicionales",
            "bank_20": "Referencia de Pago",
            
            # Government Registrations
            "government_id_01": "Registro AFIP",
            "government_id_02": "Clave Fiscal",
            "government_id_03": "Registro ANSES",
            "government_id_04": "Obra Social",
            
            # Company Structure
            "company_structure": "Tipo de Empresa",
            "number_of_employees": "Número de Empleados",
            "pay_frequency": "Frecuencia de Pago",
            "pay_day": "Día de Pago",
            "standard_work_hours": "Horas Semanales",
            
            # Contact Information
            "contact_person": "Responsable Legal",
            "contact_cuit": "CUIT del Responsable",
            "contact_phone": "Teléfono Comercial",
            "contact_email": "Email Comercial",
            "accountant_name": "Nombre del Contador",
            "accountant_cuit": "CUIT del Contador",
        },
        "placeholders": {
            "tax_id_01": "00-00000000-0",
            "bank_03": "0000000000000000000000",
            "bank_04": "ALIAS.BANCARIO",
            "postal_code": "0000",
        },
        "helptext": {
            "tax_id_01": "Clave Única de Identificación Tributaria (11 dígitos)",
            "bank_03": "Clave Bancaria Uniforme (22 dígitos)",
            "bank_04": "Alias bancario (opcional)",
        },
        "required_fields": [
            "company_code", "trade_name", "legal_name", "tax_id_01",
            "address_line_1", "city", "state",
            "bank_01", "bank_02", "bank_03",
            "contact_person", "contact_phone", "contact_email"
        ],
        "choices": {
            "company_structure": [
                ("", "Seleccione..."),
                ("SA", "Sociedad Anónima"),
                ("SRL", "Sociedad de Responsabilidad Limitada"),
                ("SC", "Sociedad Colectiva"),
                ("SCOM", "Sociedad en Comandita"),
                ("UNIPERSONAL", "Empresa Unipersonal"),
            ],
            "tax_id_03": [
                ("", "Seleccione..."),
                ("RI", "Responsable Inscripto"),
                ("MONOTRIBUTO", "Monotributista"),
                ("EXENTO", "Exento"),
                ("NO_ALCANZADO", "No Alcanzado"),
            ],
            "bank_05": [
                ("", "Seleccione..."),
                ("CUENTA_CORRIENTE", "Cuenta Corriente"),
                ("CAJA_AHORRO", "Caja de Ahorro"),
                ("CUENTA_SUELDO", "Cuenta Sueldo"),
            ],
            "pay_frequency": [
                ("", "Seleccione..."),
                ("SEMANAL", "Semanal"),
                ("QUINCENAL", "Quincenal"),
                ("MENSUAL", "Mensual"),
            ],
            "state": [
                ("", "Seleccione Provincia..."),
                ("CABA", "Ciudad de Buenos Aires"),
                ("BA", "Buenos Aires"),
                ("CBA", "Córdoba"),
                ("SF", "Santa Fe"),
                ("MZA", "Mendoza"),
                ("TU", "Tucumán"),
                ("ER", "Entre Ríos"),
                ("SL", "San Luis"),
                ("SJ", "San Juan"),
                ("CC", "Chaco"),
                ("LR", "La Rioja"),
                ("SE", "Santiago del Estero"),
                ("MI", "Misiones"),
                ("NQ", "Neuquén"),
                ("CH", "Chubut"),
                ("RN", "Río Negro"),
                ("SCR", "Santa Cruz"),
                ("TF", "Tierra del Fuego"),
            ],
        },
    },
}

# ================================================================
# 📄 UPLOAD FORM
# ================================================================

class CompanyUploadForm(forms.Form):
    file = forms.FileField(label="CSV File")
    dry_run = forms.BooleanField(required=False, initial=False)


# ================================================================
# 🏢 BASE COMPANY FORM
# ================================================================

class CompanyForm(forms.ModelForm):
    
    # Add all required fields dynamically
    def __init__(self, *args, **kwargs):
        self.country_instance = kwargs.pop("country", None)
        super().__init__(*args, **kwargs)
        
        # Add additional fields not in base model
        self._add_additional_fields()
        
        if self.country_instance:
            self._apply_country_rules()
            self._set_required_fields()
    
    def _add_additional_fields(self):
        """Add fields that might not be in the base model"""
        additional_fields = {
            # Address fields
            'address_line_1': forms.CharField(max_length=100, required=False),
            'address_line_2': forms.CharField(max_length=100, required=False),
            'city': forms.CharField(max_length=50, required=False),
            'state': forms.CharField(max_length=50, required=False),
            'postal_code': forms.CharField(max_length=20, required=False),
            
            # Company structure
            'company_structure': forms.ChoiceField(choices=[], required=False),
            'number_of_employees': forms.IntegerField(min_value=0, required=False),
            'pay_frequency': forms.ChoiceField(choices=[], required=False),
            'pay_day': forms.CharField(max_length=20, required=False),
            'standard_work_hours': forms.IntegerField(min_value=0, max_value=168, required=False),
            
            # Contact information
            'contact_person': forms.CharField(max_length=100, required=False),
            'contact_phone': forms.CharField(max_length=20, required=False),
            'contact_email': forms.EmailField(required=False),
            'contact_cpf': forms.CharField(max_length=14, required=False),
            'contact_cuit': forms.CharField(max_length=13, required=False),
            
            # Accountant information
            'accountant_name': forms.CharField(max_length=100, required=False),
            'accountant_crc': forms.CharField(max_length=20, required=False),
            'accountant_cuit': forms.CharField(max_length=13, required=False),
            'accountant_tfn': forms.CharField(max_length=20, required=False),
            'accountant_aca': forms.CharField(max_length=20, required=False),
            
            # Government registrations
            'government_id_01': forms.CharField(max_length=50, required=False),
            'government_id_02': forms.CharField(max_length=50, required=False),
            'government_id_03': forms.CharField(max_length=50, required=False),
            'government_id_04': forms.CharField(max_length=50, required=False),
        }
        
        for field_name, field in additional_fields.items():
            if field_name not in self.fields:
                self.fields[field_name] = field
    
    def _get_country_iso(self):
        c = self.country_instance
        if not c:
            return ""
        return (
            getattr(c, "iso2_code", None)
            or getattr(c, "iso2", None)
            or getattr(c, "code", None)
            or ""
        ).upper()
    
    def _apply_country_rules(self):
        iso = self._get_country_iso()
        rules = COUNTRY_FIELD_RULES.get(iso)
        if not rules:
            return
        
        # Apply labels
        for name, label in rules.get("labels", {}).items():
            if name in self.fields:
                self.fields[name].label = label
        
        # Hide fields
        for name in rules.get("hidden", []):
            if name in self.fields:
                self.fields[name].widget = forms.HiddenInput()
        
        # Apply placeholders
        for name, ph in rules.get("placeholders", {}).items():
            if name in self.fields:
                self.fields[name].widget.attrs["placeholder"] = ph
        
        # Apply help text
        for name, helptext in rules.get("helptext", {}).items():
            if name in self.fields:
                self.fields[name].help_text = helptext
        
        # Apply choices
        for name, choices in rules.get("choices", {}).items():
            if name in self.fields:
                self.fields[name].choices = choices
        
        # Set widget classes
        for field_name, field in self.fields.items():
            if field_name.startswith('bank_'):
                field.widget.attrs.update({
                    'class': 'form-control',
                    'data-section': 'banking',
                    'data-country': iso
                })
            elif field_name.startswith('tax_id_'):
                field.widget.attrs.update({
                    'class': 'form-control',
                    'data-section': 'tax',
                    'data-country': iso
                })
            elif field_name.startswith('government_id_'):
                field.widget.attrs.update({
                    'class': 'form-control',
                    'data-section': 'government',
                    'data-country': iso
                })
            elif field_name in ['address_line_1', 'address_line_2', 'city', 'state', 'postal_code']:
                field.widget.attrs.update({
                    'class': 'form-control',
                    'data-section': 'address'
                })
            elif field_name in ['contact_person', 'contact_phone', 'contact_email', 'contact_cpf', 'contact_cuit']:
                field.widget.attrs.update({
                    'class': 'form-control',
                    'data-section': 'contact'
                })
    
    def _set_required_fields(self):
        iso = self._get_country_iso()
        rules = COUNTRY_FIELD_RULES.get(iso)
        if not rules:
            return
        
        for field_name in rules.get("required_fields", []):
            if field_name in self.fields:
                self.fields[field_name].required = True
    
    class Meta:
        model = Company
        exclude = ["country", "company_id"]
        
        widgets = {
            # Basic info
            "company_code": forms.TextInput(attrs={"class": "form-control", "data-section": "basic"}),
            "company_number": forms.TextInput(attrs={"class": "form-control", "data-section": "basic"}),
            "trade_name": forms.TextInput(attrs={"class": "form-control", "data-section": "basic"}),
            "legal_name": forms.TextInput(attrs={"class": "form-control", "data-section": "basic"}),
            
            # Account settings
            "account_status": forms.Select(attrs={"class": "form-select", "data-section": "account"}),
            "account_archive": forms.Select(attrs={"class": "form-select", "data-section": "account"}),
            
            # Logo
            "logo": forms.FileInput(attrs={"class": "form-control", "data-section": "logo"}),
            
            # Tax fields (01-20)
            **{f"tax_id_{i:02d}": forms.TextInput(attrs={
                "class": "form-control", 
                "data-section": "tax",
                "data-tax-field": f"tax_{i:02d}"
            }) for i in range(1, 21)},
            
            # Banking fields (01-20)
            **{f"bank_{i:02d}": forms.TextInput(attrs={
                "class": "form-control", 
                "data-section": "banking",
                "data-bank-field": f"bank_{i:02d}"
            }) for i in range(1, 21)},
        }


# ================================================================
# 🇧🇷 BRAZIL - Custom Validation
# ================================================================

@register_company_form("BR")
class CompanyFormBR(CompanyForm):
    def clean_tax_id_01(self):
        """Validate CNPJ"""
        cnpj = self.cleaned_data.get("tax_id_01")
        if not cnpj:
            return cnpj
        
        # Remove non-digits
        cnpj = re.sub(r'\D', '', cnpj)
        
        # Validate length
        if len(cnpj) != 14:
            raise ValidationError("O CNPJ deve conter 14 dígitos.")
        
        # Basic CNPJ validation (first check digit)
        def calculate_digit(cnpj, weight_start, weight_end):
            total = 0
            weight = weight_start
            for digit in cnpj:
                total += int(digit) * weight
                weight -= 1
                if weight < weight_end:
                    weight = 9
            remainder = total % 11
            return '0' if remainder < 2 else str(11 - remainder)
        
        # Validate first check digit
        base = cnpj[:12]
        first_digit = calculate_digit(base, 5, 2)
        if cnpj[12] != first_digit:
            raise ValidationError("CNPJ inválido (dígito verificador incorreto).")
        
        # Validate second check digit
        base_with_first = base + first_digit
        second_digit = calculate_digit(base_with_first, 6, 2)
        if cnpj[13] != second_digit:
            raise ValidationError("CNPJ inválido (dígito verificador incorreto).")
        
        return cnpj
    
    def clean_bank_02(self):
        """Validate Brazilian bank code"""
        bank_code = self.cleaned_data.get("bank_02", "")
        if bank_code:
            bank_code = re.sub(r'\D', '', bank_code)
            valid_codes = ["001", "033", "104", "237", "341", "356", "389", "399", 
                          "422", "453", "633", "652", "745", "748", "756"]
            if bank_code not in valid_codes:
                raise ValidationError("Código do banco inválido.")
        return bank_code
    
    def clean_postal_code(self):
        """Validate Brazilian CEP"""
        cep = self.cleaned_data.get("postal_code", "")
        if cep:
            cep = re.sub(r'\D', '', cep)
            if len(cep) != 8:
                raise ValidationError("CEP deve conter 8 dígitos.")
        return cep


# ================================================================
# 🇦🇺 AUSTRALIA - Custom Validation
# ================================================================

@register_company_form("AU")
class CompanyFormAU(CompanyForm):
    def clean_tax_id_01(self):
        """Validate ABN"""
        abn = self.cleaned_data.get("tax_id_01")
        if not abn:
            return abn
        
        # Remove spaces
        abn = re.sub(r'\s', '', abn)
        
        # Validate length
        if len(abn) != 11:
            raise ValidationError("ABN must contain 11 digits.")
        
        # ABN validation algorithm
        try:
            weights = [10, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19]
            total = 0
            
            # Convert to list of integers
            digits = [int(d) for d in abn]
            
            # Subtract 1 from first digit
            digits[0] -= 1
            
            # Calculate weighted sum
            for i in range(11):
                total += digits[i] * weights[i]
            
            # Check if divisible by 89
            if total % 89 != 0:
                raise ValidationError("Invalid ABN.")
                
        except (ValueError, IndexError):
            raise ValidationError("ABN must contain only numbers.")
        
        return abn
    
    def clean_bank_03(self):
        """Validate BSB number"""
        bsb = self.cleaned_data.get("bank_03", "")
        if bsb:
            # Remove hyphens
            bsb = re.sub(r'[^\d]', '', bsb)
            if len(bsb) != 6:
                raise ValidationError("BSB must contain 6 digits.")
        return bsb
    
    def clean_postal_code(self):
        """Validate Australian postcode"""
        postcode = self.cleaned_data.get("postal_code", "")
        if postcode:
            postcode = re.sub(r'\D', '', postcode)
            if len(postcode) != 4:
                raise ValidationError("Postcode must contain 4 digits.")
        return postcode


# ================================================================
# 🇬🇧 UNITED KINGDOM - Custom Validation
# ================================================================

@register_company_form("GB")
class CompanyFormGB(CompanyForm):
    def clean_bank_03(self):
        """Validate Sort Code"""
        sort_code = self.cleaned_data.get("bank_03")
        if sort_code:
            digits = "".join(d for d in sort_code if d.isdigit())
            if len(digits) != 6:
                raise ValidationError("Sort Code must contain 6 digits.")
        return sort_code
    
    def clean_tax_id_03(self):
        """Validate VAT number"""
        vat = self.cleaned_data.get("tax_id_03")
        if vat:
            # Basic UK VAT validation (starts with GB)
            if vat.upper().startswith("GB"):
                vat = vat[2:].strip()
                vat = re.sub(r'[^\d]', '', vat)
                if len(vat) != 9:
                    raise ValidationError("UK VAT number must be 9 digits after GB.")
        return vat
    
    def clean_postal_code(self):
        """Validate UK postcode format"""
        postcode = self.cleaned_data.get("postal_code", "").upper()
        if postcode:
            # Basic UK postcode pattern validation
            uk_postcode_pattern = r'^[A-Z]{1,2}[0-9][A-Z0-9]? ?[0-9][A-Z]{2}$'
            if not re.match(uk_postcode_pattern, postcode):
                raise ValidationError("Invalid UK postcode format.")
        return postcode


# ================================================================
# 🇦🇷 ARGENTINA - Custom Validation
# ================================================================

@register_company_form("AR")
class CompanyFormAR(CompanyForm):
    def clean_tax_id_01(self):
        """Validate CUIT"""
        cuit = self.cleaned_data.get("tax_id_01")
        if not cuit:
            return cuit
        
        # Remove non-digits
        cuit = re.sub(r'\D', '', cuit)
        
        # Validate length
        if len(cuit) != 11:
            raise ValidationError("El CUIT debe tener 11 dígitos.")
        
        # CUIT validation algorithm
        coefficients = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
        total = 0
        
        for i in range(10):
            total += int(cuit[i]) * coefficients[i]
        
        remainder = total % 11
        check_digit = 11 - remainder
        
        if check_digit == 11:
            check_digit = 0
        elif check_digit == 10:
            check_digit = 9
        
        if int(cuit[10]) != check_digit:
            raise ValidationError("CUIT inválido (dígito verificador incorrecto).")
        
        return cuit
    
    def clean_bank_03(self):
        """Validate CBU"""
        cbu = self.cleaned_data.get("bank_03", "")
        if cbu:
            cbu = re.sub(r'\D', '', cbu)
            if len(cbu) != 22:
                raise ValidationError("CBU debe contener 22 dígitos.")
        return cbu
    
    def clean_postal_code(self):
        """Validate Argentine postal code"""
        postal_code = self.cleaned_data.get("postal_code", "")
        if postal_code:
            postal_code = re.sub(r'\D', '', postal_code)
            if len(postal_code) != 4:
                raise ValidationError("Código postal debe contener 4 dígitos.")
        return postal_code


# ================================================================
# 🇺🇸 UNITED STATES - Additional Country
# ================================================================

@register_company_form("US")
class CompanyFormUS(CompanyForm):
    # US-specific validation can be added here
    def clean_tax_id_01(self):
        """Validate US EIN"""
        ein = self.cleaned_data.get("tax_id_01", "")
        if ein:
            ein = re.sub(r'[^\d]', '', ein)
            if len(ein) != 9:
                raise ValidationError("EIN must contain 9 digits.")
        return ein
    
    def clean_bank_03(self):
        """Validate US Routing Number"""
        routing = self.cleaned_data.get("bank_03", "")
        if routing:
            routing = re.sub(r'[^\d]', '', routing)
            if len(routing) != 9:
                raise ValidationError("Routing number must contain 9 digits.")
        return routing