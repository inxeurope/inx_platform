from configparser import ConfigParser
import pyodbc
import glob
import pandas as pd
import numpy as np
import datetime
import time
import requests

# Connects to the db (connection string is passed)
# Returns True is succesfully connected, and the connection object, and the cursor
def connect_db(the_socket, conn_string, company):
    
    public_ip = 'Local, not getting public ip'
    if company != "loc":
        try:
            the_socket.send ("Getting public ip address ...")
            response = requests.get('https://api.ipify.org?format=json')
            data = response.json()
            public_ip = data['ip']
            the_socket.send("public ip: " + public_ip)
        except requests.RequestException:
            return False, None, None

    try:
        conx = pyodbc.connect(conn_string)
        the_socket.send("Connection established successfully from ip " + public_ip)
        # cursor = conx.curs()
        # the_socket.send(conx)
        # HURRAY!
        conx.autocommit = False
        curs = conx.cursor()
        return True, conx, curs
    except pyodbc.OperationalError as err:
        the_socket.send("DB connection could not be established </br>" + err.args[1])
        return False, None, None
    except pyodbc.ProgrammingError as ex:
        the_socket.send ("Program error. </br>" + ex.args[1])
        return False, None, None
    except Exception as ex:
        the_socket.send("Database connection terminated with unhandled eception")
        the_socket.send ("Generic exception. </br>" + ex.args[1])
        return False, None, None

def run_process(ws, conx, curs, files, stored_proc=False):
    # This function manages the process, launching function
    # work_on_the_file on each file (files), passing the required arguments
    # After all files are worked out, if setting is True, it runs stored procedures
    
    duties ={}
    for file in files:
        if "ke30" in file:
            duties["ke30"] = file
        if "ke24" in file:
            duties["ke24"] = file
        if "zaq" in file:
            duties["zaq"] = file
        if "oo" in file:
            duties["oo"] = file
        if "oh" in file:
            duties["oh"] = file
        if "oit" in file:
            duties["oit"] = file
        if "arr" in file:
            duties["arr"] = file
        if "prl" in file:
            duties["prl"] = file
    ws.send("new duties dict: <br/>" + str(duties))
    ws.send("Processing, it may take some time ...")
    ws.send("<h1 class='text-center text-uppercase'>don't refresh or leave the page</h1>")
    for duty_key, duty in duties.items():
        ws.send(duty_key + "***duty_key: " + duty_key + ", duty: " + duty)
        oggi = datetime.datetime.now()
        oggi = oggi.strftime("%Y%m%d-%H%M%S") # example format 20201120-203456
        match duty_key:
            case "ke30":
                #Preparing dictionaries
                converters_dict = {
                    'Customer': str,
                    'Customer.1': str,
                    'Product': str,
                    'Product.1': str,
                    'Profit Center': str,
                    'Profit Center.1': str,
                    'Period/Year': str,
                    'Period/Year.1': str,
                    'Material Group': str,
                    'Material Group.1': str,
                    'Product Hierarchy': str,
                    'Prod.hierarachy':str,
                    'Cust.Acct.Assg.Group': str,
                    'AccAssmtGrpCust':str,
                    'Fiscal Year': str,
                    'Fiscal Year.1': str,
                    'Sales employee': str,
                    'Sales employee.1': str,
                    'CustomerHierarchy01': str,
                    'CustomerHier01': str,
                    'Sales district': str,
                    'Sales district.1': str,
                    'Period': str,
                    'Period.1': str,
                    'Material pricing grp': str,
                    'Mat.pricing grp': str,
                    'Price group': str,
                    'Price group.1': str,
                    'Division': str,
                    'Division.1': str,
                    'Color': str,
                    'Color.1': str,
                    'Color Group': str,
                    'Color Group.1': str,
                    'Product Line': str,
                    'Product Line.1': str,
                    'Market Segment': str,
                    'Mareket Segment.1': str,
                    'Major Label': str,
                    'Major Label.1': str,
                    'Industry': str,
                    'Industry.1': str,
                    'Brand Name': str,
                    'Brand Name.1': str,
                    'Country': str,
                    'Country.1': str,
                    'Currency': str,
                    'Unit of Measure': str,
                    'Ship-to party': str,
                    'Ship-to party.1': str,
                    'National Account Mgr':str,
                    'National Account Mgr.1':str,
                    'Field Sales Mgr': str,
                    'Field Sales Mgr.1': str,
                    'Unit Sales quantity':str,
                    'VP sales': str
                }
                rename_dict = {
                    "Customer.1":"Customer1",
                    "Product.1":"Product1",
                    "N.Sales/unit Actual": "N#Sales/unit Actual",
                    "Material Group.1":"Material Group1",
                    "Prod.hierarchy": "Prod#hierarchy",
                    "Color.1":"Color1",
                    "Product Line.1":"Product Line1",
                    "Cust.Acct.Assg.Group": "Cust#Acct#Assg#Group",
                    "AccAssmtGrpCust": "CustAcctAssgGrp",
                    "Profit Center.1":"Profit Center1",
                    "Market Segment.1":"Market Segment1",
                    "Major Label.1":"Major Label1",
                    "National Account Mgr.1": "National Account Mgr1",
                    "C.Margin % Actual": "C#Margin % Actual",
                    "Fiscal Year.1": "Fiscal Year1",
                    "Country.1":"Country1",
                    "Sales employee.1": "Sales employee1",
                    "Sales district.1": "Sales district1",
                    "Color Group.1":"Color Group1",
                    "Mat.pricing grp": "Mat#pricing grp", 
                    "Price group.1": "Price group1", 
                    "Industry.1": "Industry1", 
                    "Brand Name.1":"Brand Name1",
                    "Period.1":"Period1",
                    "Division.1": "Division1",
                    "Field Sales Mgr.1":"Field Sales Mgr1",
                    "Period/Year.1":"Period/year1",
                    "Ship-to party.1":"Ship-to party1"
                }
                table_name = "KE30_import"
                work_on_the_file(ws, duty_key, duty, converters_dict, rename_dict, table_name, conx, curs)
            case "ke24":
                converters_dict = {
                    "Currency": str,
                    "CurrencyType": str,
                    "RecordType": str,
                    "YearMonth": str,
                    "DocumentNumber": str,
                    "ItemNumber": str,
                    "ReferenceDocument": str,
                    "ReferenceItemNo": str,
                    "CreateBy": str,
                    "CompanyCode": str,
                    "SenderCostCenter": str,
                    "CostElement": str,
                    "CurrencyKey": str,
                    "CostElement": str,
                    "CurrencyKey": str,
                    "SalesQuantity": str,
                    "UnitSalesQuantity": str,
                    "YearWeek": str,
                    "Product": str,
                    "IndustryCode1": str,
                    "Industry": str,
                    "SalesDistrict": str,
                    "ReferenceOrgUnit": str,
                    "LogSystemSource": str,
                    "ReferenceTransaction": str,
                    "PointOfValuation": str,
                    "BillingType": str,
                    "BusinessArea": str,
                    "CustomerHierarchy01": str,
                    "CustomerHierarchy02": str,
                    "CustomerHierarchy03": str,
                    "CustomerHierarchy04": str,
                    "CustomerHierarchy05": str,
                    "Origin": str,
                    "SalesOrder": str,
                    "CustomerGroup": str,
                    "Customer": str,
                    "ControllingArea": str,
                    "PriceGroup": str,
                    "MaterialPricingGroup": str,
                    "CostObject": str,
                    "CustomerAccountAssignmentGroup": str,
                    "ShiToParty": str,
                    "Country": str,
                    "Client": str,
                    "MaterialGroup": str,
                    "MarketSegment": str,
                    "Color": str,
                    "MajorLabel": str,
                    "BrandName": str,
                    "ColorGroup": str,
                    "ProfitabilitySegmentNo": str,
                    "PartnerProfSegment": str,
                    "PartSubNumber": str,
                    "SubNumber": str,
                    "PartnerProfitCenter": str,
                    "DyeInk": str,
                    "ProfitCenter": str,
                    "ProductHierarchy": str, 
                    "SenderBusinessProcess": str,
                    "WBSElement": str,
                    "CurrencyOfRecord": str,
                    "Order": str, 
                    "Update status": str,
                    "Division": str,
                    "CanceledDocument": str, 
                    "CanceledDocumentItem": str,
                    "TimeCreated": str, 
                    "Version": str,
                    "SalesOrg": str,
                    "SalesEmployee": str,
                    "DistributionChannel": str,
                    "Plant": str,
                    "NationalAccountManager": str,
                    "ProductLine": str,
                    "VPSales": str,
                    "ProductLineSalesManager": str,
                    "FieldSalesManager": str,
                    
                    "CreateOn": datetime.date,
                    "PostingDate": datetime.date,
                    "InvoiceDate": datetime.date,
                    "Date": datetime.date,
                    "Time": datetime.datetime,
                    # "Time": "%H:%M:%S",
                    "GoodsIssueDate": datetime.date,

                    "Year": int,
                    "HierarchyAssignment": int,
                    "SalesOrderItem": int,
                    "Period": int,
                    "PlanActIndicator": int,

                    "SalesQuantity": float,
                    "Revenue": float,
                    "AnnualRebates": float,
                    "ExchangeRate": float,
                    "QuantityDiscount": float,
                    "CostOfSales": float,
                    "Inplant_Depreciation": float,
                    "FreightCharges": float,
                    "MTS_InputVar": float,
                    "MTS_InputPriveVar": float,
                    "MTS_LotsizeVar": float,
                    "MTO_FixFreightCost": float,
                    "MTO_FixMaterialCost": float,
                    "MTO_VariableMaterialCost": float,
                    "MTO_FixOverheadCost": float,
                    "MTO_VariableOverheadCost": float,
                    "MTO_FixProductionCost": float,
                    "MTS_OutputPriceVar": float,
                    "MTO_VariableProductionCost": float,
                    "Inplant_OtherExpenses": float,
                    "Inplant_Payroll": float,
                    "MTS_QuantityVar": float,
                    "MTS_RemainingVar": float,
                    "MTS_ResUsageVar": float,
                    "MTS_FixFreightCost": float,
                    "MTS_FixMaterialCost": float,
                    "MTS_VariableMaterialCost": float,
                    "MTS_FixOverheadCost": float,
                    "MTS_VarialbleOverheadCost": float,
                    "MTS_FixProductionCost": float,
                    "MTS_VariableProductionCost": float    
                    }
                rename_dict = {
                    'Currency type':'CurrencyType',
                    'Record Type':'RecordType',
                    'Period/Year':'YearMonth',
                    'Document number':'DocumentNumber',
                    'Item number':'ItemNumber',
                    'Created On':'CreatedOn',
                    'Reference document':'ReferenceDocument',
                    'Reference item no.':'ReferenceItemNo',
                    'Created By':'CreatedBy',
                    'Company Code':'CompanyCode',
                    'Sender cost center':'senderCostCenter',
                    'Cost Element':'CostElement',
                    'Currency key':'CurrencyKey',
                    'Sales quantity':'SalesQuantity',
                    'Unit Sales quantity':'UnitSalesQuantity',
                    'Week/year':'YearWeek',
                    'Industry Code 1': 'IndustryCode1',
                    'Posting date': 'PostingDate',
                    'Sales district': 'SalesDistrict',
                    'Reference Org Unit': 'ReferenceOrgUnit',
                    'Log. system source': 'LogsystemSource',
                    'Reference Transact.': 'ReferenceTransaction',
                    'Point of valuation': 'PointOfValuation',
                    'Invoice date': 'InvoiceDate',
                    'Billing Type': 'BillingType',
                    'Fiscal Year': 'Year',
                    'Business Area': 'BusinessArea',
                    'CustomerHierarchy01': 'CustomerHierarchy01',
                    'CustomerHierarchy02': 'CustomerHierarchy02',
                    'CustomerHierarchy03': 'CustomerHierarchy03',
                    'CustomerHierarchy04': 'CustomerHierarchy04',
                    'CustomerHierarchy05': 'CustomerHierarchy05',
                    'Origin': 'Origin',
                    'Hierarchy Assignment': 'HierarchyAssignment',
                    'Annual rebates': 'AnnualRebates',
                    'Sales Order': 'SalesOrder',
                    'Customer group': 'CustomerGroup',
                    'Sales Order Item': 'SalesOrderItem',
                    'Customer': 'Customer',
                    'Controlling Area': 'ControllingArea',
                    'Price group': 'PriceGroup',
                    'Material pricing grp': 'MaterialPricingGroup',
                    'Cost Object': 'CostObject',
                    'Cust.Acct.Assg.Group': 'CustomerAccountAssignmentGroup',
                    'Ship-to party': 'ShiToParty',
                    'Exchange rate': 'ExchangeRate',
                    'Material Group': 'MaterialGroup',
                    # SAP have changed the nameof the following column
                    # from "Quantity discount" to "Qty discount"
                    # 'Quantity discount': 'QuantityDiscount',
                    'Qty discount': 'QuantityDiscount',
                    'Market Segment': 'MarketSegment',
                    'Major Label': 'MajorLabel',
                    'Brand Name': 'BrandName',
                    'Color Group': 'ColorGroup',
                    'Profitab. Segmt No.': 'ProfitabilitySegmentNo',
                    'Partner prof.segment': 'PartnerProfSegment',
                    'Partner subnumber': 'PartSubNumber',
                    'Subnumber': 'SubNumber',
                    'Plan/Act. Indicator': 'PlanActIndicator',
                    'Partner Profit Ctr': 'PartnerProfitCenter',
                    'Dye Ink': 'DyeInk',
                    'Profit Center': 'ProfitCenter',
                    'Product hierarchy': 'ProductHierarchy',
                    'Sender bus. process': 'SenderBusinessProcess',
                    'WBS Element': 'WBSElement',
                    'Currency of record': 'CurrencyOfRecord',
                    'Update status': 'UpdateStatus',
                    'Canceled document': 'CanceledDocument',
                    'Canceled doc. item': 'CanceledDocumentItem',
                    'Time created': 'TimeCreated',
                    'Sales Organization': 'SalesOrg',
                    'Sales employee': 'SalesEmployee',
                    'Distribution Channel': 'DistributionChannel',
                    'Cost of Sales - SD': 'CostOfSales',
                    'INPLANT - depreciat.': 'Inplant_Depreciation',
                    'Freight Charges': 'FreightCharges',
                    'MTS -Input var.': 'MTS_InputVar',
                    'MTS -Inp. prive var.': 'MTS_InputPriveVar',
                    'MTS -Lotsize var.': 'MTS_LotsizeVar',
                    'MTO -Fix.Freight Cst': 'MTO_FixFreightCost',
                    'MTO -Fix.Mater. Cst': 'MTO_FixMaterialCost',
                    'MTO -Vbl.Mater. Cst': 'MTO_VariableMaterialCost',
                    'MTO -Fix.Overh. Cst': 'MTO_FixOverheadCost',
                    'MTO -Vbl.Overh. Cst': 'MTO_VariableOverheadCost',
                    'MTO -Fix.Prod. Cst': 'MTO_FixProductionCost',
                    'MTS -Outp. price var': 'MTS_OutputPriceVar',
                    'MTO -Vbl.Prod. Cst': 'MTO_VariableProductionCost',
                    'INPLANT - other exp.': 'Inplant_OtherExpenses',
                    'INPLANT - payroll': 'Inplant_Payroll',
                    'MTS -Quantity var.': 'MTS_QuantityVar',
                    'MTS -Remaining var.': 'MTS_RemainingVar',
                    'MTS -Res. usage var.': 'MTS_ResUsageVar',
                    'MTS -Fix.Freight Cst': 'MTS_FixFreightCost',
                    'MTS - Fix. mat. cost': 'MTS_FixMaterialCost',
                    'MTS - Vbl. mat. cost': 'MTS_VariableMaterialCost',
                    'MTS -Fix.Overh. Cst': 'MTS_FixOverheadCost',
                    'MTS -Vbl.Overh. Cst': 'MTS_VarialbleOverheadCost',
                    'MTS -Fix.Prod. Cst': 'MTS_FixProductionCost',
                    'MTS -Vbl.Prod. Cst': 'MTS_VariableProductionCost',
                    'Goods Issue Date': 'GoodsIssueDate',
                    'National Account Mgr': 'NationalAccountManager',
                    'Product Line': 'ProductLine',
                    'VP Sales': 'VPSales',
                    'Prod Line Sls Mgr': 'ProductLineSalesManager',
                    'Field Sales Mgr': 'FieldSalesManager'
                }
                table_name = "KE24_import"
                work_on_the_file(ws, duty_key, duty, converters_dict, rename_dict, table_name, conx, curs)
                pass
            case "zaq":
                converters_dict = {
                    'Material': str,
                    'Description': str,
                    'Name': str,
                    'BillingDoc': str,
                    'Invoice Qty': str,
                    'UoM': str,
                    'Unit Price': str,
                    'Invoice Sales': str,
                    'Curr.': str,
                    'Batch': str,
                    'GM (%)': str,
                    'Prof': str,
                    'PTrm': str,
                    'Curr..1': str,
                    'Cost':str,
                    'Can': str,
                    'Bill':str,
                    'Item': str,
                    'Tax amount': str,
                    'Curr..2': str,
                    'Dv': str,
                    'ShPt': str,
                    'Sold to': str,
                    
                    'Sales doc.': float,                    
                    
                    'Billing date': datetime.date 
                }
                rename_dict = {
                    "Sales doc.":"SalesDoc"
                }
                table_name = "ZAQCODMI9_import"
                work_on_the_file(ws, duty_key, duty, converters_dict, rename_dict, table_name, conx, curs)
            case "oo":
                # SAP transaction ZSDORDER
                converters_dict = {
                    "CustomerNumber": float,
                    "Ship_to": float,
                    "ValueInvoiced": float,

                    "SalesOrderDate": datetime,
                    "RequestedDate": datetime ,
                    "PartialShipmentDate": datetime ,
                    "InvoiceDate": datetime,
                    "DeliveryDate": datetime,
                    "ImportDate": datetime,

                    "CustomerName": str,
                    "Country": str,
                    "Plant": str,
                    "SalesOrderNumber": str,
                    "StoreLocation": str,
                    "OrderType": str,
                    "ProductNumber": str,
                    "ProductName": str,
                    "QtyOrdered_unit": str,
                    "QtyOpen_unit": str,
                    "QtyPartialShipped_unit": str,
                    "CustomerPONumber": str,
                    "LineType": str,
                    "InvoiceNumber": str,
                    "DocumentCurrency": str,
                    "QtyInvoiced_unit": str,
                    
                    "ItemLineNumber": int,
                    "DaysLate": int,
                    "QtyOrdered": int,
                    "QtyOpen": int,
                    "QtyPartialShipped": int,
                    "LeadTime": int,
                    "DeliveryNumber": int,
                    "QtyInvoiced": int
                }
                rename_dict = {
                    'Sold-to':'CustomerNumber',
                    'Ship-to':'Ship_to',
                    'Customer Name':'CustomerName',
                    'Cty':'Country',
                    'Sales Doc#':'SalesOrderNumber',
                    'SOStLoc':'StoreLocation',
                    'Item':'ItemLineNumber',
                    'Sa Ty':'OrderType',
                    'Order Date':'SalesOrderDate',
                    'Req. dt':'RequestedDate',
                    'PL. GI Dt':'PartialShipmentDate',
                    'Days late':'DaysLate',
                    'Material':'ProductNumber',
                    'Material Description':'ProductName',
                    'Ordered Qty':'QtyOrdered',
                    'Unit':'QtyOrdered_unit',
                    'Open Order Qty':'QtyOpen',
                    'Unit.1':'QtyOpen_unit',
                    'GI Qty':'QtyPartialShipped', 
                    'Unit.3':'QtyPartialShipped_unit', 
                    'Cust PO #':'CustomerPONumber', 
                    'Lead time':'LeadTime'
                }
                table_name = "Orders"
                work_on_the_file(ws, duty_key, duty, converters_dict, rename_dict, table_name, conx, curs)
            case "oh":
                # SAP transaction ZSDORDHIST - need?
                converters_dict = {
                    "CustomerNumber": float,
                    "Ship_to": float,
                    "ValueInvoiced": float,

                    "SalesOrderDate": datetime,
                    "RequestedDate": datetime ,
                    "PartialShipmentDate": datetime ,
                    "InvoiceDate": datetime,
                    "DeliveryDate": datetime,
                    "ImportDate": datetime,

                    "CustomerName": str,
                    "Country": str,
                    "Plant": str,
                    "SalesOrderNumber": str,
                    "StoreLocation": str,
                    "OrderType": str,
                    "ProductNumber": str,
                    "ProductName": str,
                    "QtyOrdered_unit": str,
                    "QtyOpen_unit": str,
                    "QtyPartialShipped_unit": str,
                    "CustomerPONumber": str,
                    "LineType": str,
                    "InvoiceNumber": str,
                    "DocumentCurrency": str,
                    "QtyInvoiced_unit": str,
                    
                    "ItemLineNumber": int,
                    "DaysLate": int,
                    "QtyOrdered": int,
                    "QtyOpen": int,
                    "QtyPartialShipped": int,
                    "LeadTime": int,
                    "DeliveryNumber": int,
                    "QtyInvoiced": int
                }
                rename_dict = {
                    'Sold-to':'CustomerNumber',
                    'Ship-to':'Ship_to',
                    'Customer Name':'CustomerName',
                    'Cty':'Country',
                    'Sales Doc#':'SalesOrderNumber',
                    'SOStLoc':'StoreLocation',
                    'Item':'ItemLineNumber',
                    'Sa Ty':'OrderType',
                    'Order Date':'SalesOrderDate',
                    'Req. dt':'RequestedDate',
                    'PL. GI Dt':'PartialShipmentDate',
                    'Days late':'DaysLate',
                    'Material':'ProductNumber',
                    'Material Description':'ProductName',
                    'Ordered Qty':'QtyOrdered',
                    'Unit':'QtyOrdered_unit',
                    'Open Order Qty':'QtyOpen',
                    'Unit.1':'QtyOpen_unit',
                    'GI Qty':'QtyPartialShipped', 
                    'Unit.3':'QtyPartialShipped_unit', 
                    'Cust PO #':'CustomerPONumber', 
                    'Lead time':'LeadTime'
                }
                table_name = "Orders"
                work_on_the_file(ws, duty_key, duty, converters_dict, rename_dict, table_name, conx, curs)
                pass
            case "oit":
                # SAP transaction FBL5N - Open Items
                converters_dict = {
                    "Document Date": datetime.date,
                    "Net due date": datetime.date,
                    "Arrears after net due date": float,
                    "Amount in doc. curr.": float,
                    "Document currency":str,
                    "Document type": str,
                    # "Account": int,
                    "Document Number": str,
                    "Billing Document": str,
                    "Term of Payment": str,
                    "Invoice reference": str,
                    "Payment date": datetime.date,
                    "Debit/Credit ind": str
                }
                
                rename_dict = {
                    'Document Date':'DocumentDate',
                    'Net due date':'NetDueDate',
                    'Arrears after net due date':'Arrears',
                    'Amount in doc. curr.':'AmountInDocCurr',
                    'Document currency':'DocCurr',
                    'Document Type':'DocType',
                    'Account':'CustomerNumber',
                    'Document Number':'DocNumber',
                    'Billing Document':'InvoiceNumber',
                    'Terms of Payment':'PaymentTerms',
                    'Invoice reference':'InvoiceRef',
                    'Payment date':'PaymentDate',
                    'Debit/Credit ind':'DebCred'
                    }
                drop_list = [
                    'Net due date symbol',
                    'Arrears for discount 1',
                    'Baseline Payment Dte',
                    'Payment Block',
                    'Due net'
                ]
                table_name = "FBL5N_open_import"
                work_on_the_file(ws, duty_key, duty, converters_dict, rename_dict, table_name, conx, curs, drop_list)
            case "arr":
                # SAP Transaction FBL5N - All Items
                converters_dict = {
                    "Document Date": datetime.date,
                    "Net due date": datetime.date,
                    "Arrears after net due date": float,
                    "Amount in doc. curr.": float,
                    "Document currency":str,
                    "Document type": str,
                    # "Account": int,
                    "Document Number": str,
                    "Billing Document": str,
                    "Term of Payment": str,
                    "Invoice reference": str,
                    "Payment date": datetime.date,
                    "Debit/Credit ind": str
                }
                rename_dict = {
                    'Document Date':'DocumentDate',
                    'Net due date':'NetDueDate',
                    'Arrears after net due date':'Arrears',
                    'Amount in doc. curr.':'AmountInDocCurr',
                    'Document currency':'DocCurr',
                    'Document Type':'DocType',
                    'Account':'CustomerNumber',
                    'Document Number':'DocNumber',
                    'Billing Document':'InvoiceNumber',
                    'Terms of Payment':'PaymentTerms',
                    'Invoice reference':'InvoiceRef',
                    'Payment date':'PaymentDate',
                    'Debit/Credit ind':'DebCred'
                    }
                drop_list = [
                    'Net due date symbol',
                    'Arrears for discount 1',
                    'Baseline Payment Dte',
                    'Payment Block',
                    'Due net'
                ]
                table_name = "FBL5N_arr_import"
                work_on_the_file(ws, duty_key, duty, converters_dict, rename_dict, table_name, conx, curs, drop_list)
            case "prl":
                # SAP Transaction XXXXX - Customer Prices
                converters_dict = {
                    "ID": int,
                    "CustomerID": int,
                    "CustomerNumber": int,
                    "CustomerName": str, 
                    "ProductID": int,
                    "ProductNumber": str,
                    "ProductName": str,
                    "Price": float,
                    "Per": int,
                    "UoM": str,
                    "Volume_From": int,
                    "Volume_To": int,
                    "Valid_From": datetime,
                    "Valid_To": datetime,
                    "Currency": str,
                    "Importdate": datetime
                }
                rename_dict = {
                    'Customer':'CustomerNumber',
                    'Customer Name':'CustomerName',
                    'Material':'ProductNumber',
                    'Material Description':'ProductName',
                    'Scale Qty From': 'Volume_From',
                    'Scale Qty To':'Volume_To',
                    'Curr':'Currency',
                    'Start Date':'Valid_From',
                    'End Date':'Valid_To'
                }
                table_name = "Prices"
                work_on_the_file(ws, duty_key, duty, converters_dict, rename_dict, table_name, conx, curs)
    # Here store procedure are evaluated, and run if necessary
    if stored_proc == True:
        if len(duties) > 0:
            ws.send("Execution of store procedures ...")
        for duty in duties:
            if duties[duty] != "":
                match duty:
                    case "ke30":
                        run_stored(ws, "spDoKE30Import", curs, conx)
                    case "ke24":
                        run_stored(ws, "spDoKE24Import", curs, conx)
                    case "zaq":
                        run_stored(ws, "spDoZAQCODMI9Import", curs, conx)
                        run_stored(ws, "spBudForAlignment", curs, conx)
                        run_stored(ws, "spBudForDetails_FillSales", curs, conx)
                    case "oo":
                        pass
                    case "oh":
                        pass
                    case "oit":
                        pass
                    case "arr":
                        pass
                    case "prl":
                        pass

def run_stored(ws, sp_name, curs, conx):
    ws.send("Executing " + sp_name)
    curs.execute(sp_name)
    conx.commit()
    ws.send("..." + sp_name + " done")    

def grind_the_file(ws, duty_key, tab_name, connection, cursor, sql_statement, dataframe):
    # This function calculates chunk size of the dataframe,
    # iterate through each chunk, writing in the appropriate table, which name is passed in
    
    ws.send(duty_key + "***------- PROCESSING THE FILE -----")
    start_time = time.time()
    df_length = len(dataframe)
    if df_length > 19999:
        chunk_size = 4000
    elif df_length > 14999:
        chunk_size = 3000
    elif df_length > 9999:
        chunk_size = 2000
    elif df_length > 7499:
        chunk_size = 1500
    elif df_length > 4999:
        chunk_size = 1000
    else:
        chunk_size = 500
    
    # Determination of how many rounds
    if df_length % chunk_size > 0:
        iterations = int(df_length / chunk_size) + 1
    else:
        iterations = int(df_length / chunk_size)
    ws.send(duty_key + "***executing " + duty_key + " in " + str(iterations) + " iterations...")

    # Iterate over chunks
    for iteration in range(iterations):
        lower_limit = iteration * chunk_size
        upper_limit = (iteration * chunk_size) + (chunk_size - 1)
        if upper_limit >= df_length - 1: upper_limit = df_length - 1
        ws.send(duty_key + "***section " + str(iteration) + " - from " + str(lower_limit) + " to " + str(upper_limit) )
        chunk_df = dataframe.iloc[lower_limit:upper_limit + 1]
        cursor.fast_executemany = True
        start_time = time.time()
        # Must implement the one_field_at_a_time insert on the chunc to see if
        config = ConfigParser()
        config.read('config.ini')
        one_column_per_time = config.getboolean('DEFAULT', 'one_column_at_a_time')
        # one_column_per_time = config["DEFAULT"]["one_column_at_a_time"]
        
        ########################################################################
        # This section is adding one column at a time to check if one field is
        # giving too long insertion time
        ########################################################################
        if one_column_per_time == True:
            ws.send(duty_key + "***start one_column_per_time process")
            # Don't pollute the chunck df
            chunk_df_copy = chunk_df     
            fields_and_time_dict = {}
            # Create a temporary disposable dataframe 
            disposable_df=pd.DataFrame()
            # Cycle through columns
            index = 0
            total = len(chunk_df_copy.columns)
            for column in range(len(chunk_df_copy.columns)):
                index +=1
                cursor.execute("DELETE FROM " + tab_name)
                chunk_df_copy = chunk_df.iloc[:,column:column+1]
                col_name = chunk_df_copy.columns[0]
                sql_statement_per_column = SQL_statement_fabricator(tab_name, chunk_df_copy.columns.to_list())
                # ws.send("SQL Statement per column: " + sql_statement_per_column)

                # sql_statement_per_rows = SQL_statment_maker(table_name, df_temporary, "--> SQL stmt done 4 col :" + str(col+1) + " " + col_name, one_liner = True)
                # if df_temporary[col_name].dtype == '<M8[ns]':
                #     df_temporary[col_name] = df_temporary[col_name].apply(lambda x: x.date())

                time_at_start = time.time()
                try:
                    cursor.executemany(sql_statement_per_column, chunk_df_copy.values.tolist())
                except pyodbc.Error as err:
                    message = "Error with column: " + col_name + "<br>" + str(err) + "<br>"
                    message += "SQL statement <br>" + sql_statement_per_column + "<br>"
                    message += "values: " + str(chunk_df_copy.values.tolist())
                    ws.send(duty_key + "***" + message)
                time_at_finish = time.time()
                time_lapsed = time_at_finish - time_at_start
                fields_and_time_dict[col_name] = time_lapsed
                ws.send(duty_key + "***" + str(index) + "/" + str(total) + " " + col_name + "<br>...time lasped: {:0.2f}".format(time_lapsed) + " sec.")
            ws.send(duty_key + "***end of the one_column_per_time process")
        ##########################################################################


        # one filed is slower than others - this is a debug strategy
        try:
            cursor.executemany(sql_statement, chunk_df.values.tolist())
            connection.commit()
        except pyodbc.ProgrammingError as err:
            ws.send("*******************************************")
            ws.send(str(err))

        end_time = time.time()
        duration = end_time - start_time
        ws.send(duty_key + "***section " + str(iteration) + " done in " + str(round(duration, 2)) + " sec        @ " + str(round(chunk_size / duration, 2)) + " rec/sec")
    ws.send (duty_key + "***Finished with table: " + tab_name)

def read_the_file(ws, duty_key, duty, converters_dict, rename_dict, drop_list, tablename):
    # read_the_file
    # Reads the Excel file, creates a dataframe, and build the SQL statement
    # It returns both the dataframe and the SQL statement
    
    oggi = datetime.datetime.now()
    oggi = oggi.strftime("%Y%m%d-%H%M%S") # 20201120-203456
    ws.send(duty_key + "***Reading file " + duty + "<br>" + "...adjusting data types")
    df = pd.read_excel(duty, thousands='.', decimal=',', dtype=converters_dict, parse_dates=True)
    # ws.send(df.columns.to_list())
    ws.send(duty_key + "***Renaming fields ...")
    df.rename(columns=rename_dict, inplace=True)
    # ws.send(df.columns.to_list())
    match duty_key:
        case "ke30":
            df = df.replace(np.nan, '')
            df['Importtimestamp'] = oggi
            # df["YearMonth"] = (df["Fiscal Year"].astype(str) + df["Period"].astype(str).str.zfill(2)).astype(int)
            df["YearMonth"] = (df['Fiscal Year'].astype(int) * 100 + df['Period'].astype(int)).astype(str)
            df = df.replace(np.nan, '')
        case "ke24":
            df = df.replace(np.nan, '')
            df["CreatedOn"] = df['CreatedOn'].dt.date
            df['PostingDate'] = df['PostingDate'].dt.date
            df['InvoiceDate'] = df['InvoiceDate'].dt.date
            df['GoodsIssueDate'] = df['GoodsIssueDate'].dt.date
            df["Date"] = df.apply(lambda x: datetime.datetime.combine(x['Date'], x["Time"]).strftime("%Y-%m-%d %H:%M:%S"), axis=1)
            df["YearMonth"] = (df["Year"].astype(str) + df["Period"].astype(str).str.zfill(2)).astype(int)
        case "zaq":
            df["SalesDoc"].astype('Int64')
            df["Sold to"].astype('Int64')
            df["Billing date"] = df['Billing date'].apply(lambda x: x.strftime("%Y-%m-%d") if not pd.isna(x) else x)
            # Get unique values of UoM
            # Get unique values of Curr.
            # Get MAX values between the 2
            # retract dataframe
            num_max_uom = df['UoM'].nunique()
            num_max_curr = df['Curr.'].nunique()
            max_unique = max(num_max_curr, num_max_uom)
            df = df.head(len(df) - max_unique)            
            # df = df.replace(np.nan, '')
        case "oo":
            # Columns T V and X to use as a measure to cut tail
            # df = df.replace(np.nan, '')
            df.drop({'Transit Time', 'Open Del Qty', 'Unit.2', 'In Stock', 'Equipment'}, axis='columns', inplace=True)
            # df = df.iloc[:-4]
            df.loc[:,"ImportDate"] = datetime.datetime.now()
            df['LineType'] = 'OO'
            df = df[df["Plant"].notnull()]
            df["SalesOrderDate"] = df['SalesOrderDate'].apply(lambda x: x.strftime("%Y-%m-%d") if not pd.isna(x) else x)
            df["RequestedDate"] = df['RequestedDate'].apply(lambda x: x.strftime("%Y-%m-%d") if not pd.isna(x) else x)
            df["PartialShipmentDate"] = df['PartialShipmentDate'].apply(lambda x: x.strftime("%Y-%m-%d") if not pd.isna(x) else x)
            df["ImportDate"] = df['ImportDate'].apply(lambda x: x.strftime("%Y-%m-%d") if not pd.isna(x) else x)
            df['CustomerNumber'] = df['CustomerNumber'].fillna(df['Ship_to'])
            df['CustomerNumber'] = np.where(df['CustomerNumber'] == '', df['Ship_to'], df['CustomerNumber'])
        case "oh":
            pass
        case "oit" | "arr":
            df.drop(drop_list, axis='columns', inplace=True)
            # df.drop ({'Net due date symbol', 'Arrears for discount 1', 'Baseline Payment Dte', 'Payment Block', 'Due net'}, axis='columns', inplace=True)
            rows_to_retract = df['DocCurr'].nunique()
            df=df.iloc[:-rows_to_retract]
            df['DocumentDate'] = df['DocumentDate'].dt.date
            df['NetDueDate'] = df['NetDueDate'].dt.date
            df['PaymentDate'] = df['PaymentDate'].dt.date
            df['Arrears'] = df['Arrears'].fillna(0).astype(int)
        case "prl":
            df.drop(columns=['SOrg', 'Dv', 'CTyp'], axis=1, inplace=True)
            df['ImportDate'] = datetime.datetime.now()
    ws.send(duty_key + "***" + duty_key + ": " + str(len(df)) + " records - dataframe created")
    ws.send(duty_key + "***there are " + str(len(df.columns)) + " columns")
    sql_full = SQL_statement_fabricator(tablename, df.columns.to_list())
    # ws.send(sql_full)
    return df, sql_full

def truncate_table(ws, conx, curs, tablename, duty_key=""):
    ws.send(duty_key + "***Cleaning ...")
    if duty_key == "oo":
        sqlstatement = "DELETE FROM " + tablename + " WHERE [LineType] = 'OO'"
    if duty_key == "oh":
        sqlstatement = "DELETE FROM " + tablename + " WHERE [LineType] = 'OH'"
    else:
        sqlstatement = "TRUNCATE TABLE " + tablename
    curs.execute(sqlstatement)
    conx.commit()
    ws.send(duty_key + "***Cleaned table " + tablename)

def SQL_statement_fabricator(table_name, list_of_columns):
    sql_insert = "INSERT INTO " + table_name
    sql_fields = "([" + "], [".join(list_of_columns) + "])"
    sql_value = "VALUES"
    sql_questionmarks = "(" + ("?, " * len(list_of_columns))[:-2] + ")"
    sql_statement = sql_insert + sql_fields + sql_value + sql_questionmarks
    return sql_statement

def work_on_the_file(ws, duty_key, duty, converters_dict, rename_dict, table_name, conx, curs, drop_list = []):
    # This function reads the Excel file, applying the coverting dictionary and renaming dictonary
    # Export the dataframe in Excel format if setting is True
    # Clean the table in the database
    # Launch the grind_the_file function to iterate over the dataframe and write in the database
    
    # Read file into dataframe and make SQL statement
    df, sqlstatement = read_the_file(ws, duty_key, duty, converters_dict, rename_dict, drop_list, table_name)
        
    # Export - if needing to export an excel file for verification - with timestamp
    config = ConfigParser()
    config.read('config.ini')
    if config.getboolean('DEFAULT', 'export_excel_dataframe') == True:
        df.to_excel("./output_dataframe_" + duty_key + "_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".xlsx")

    # Cleaning table
    if duty_key == "oo":
        truncate_table(ws, conx, curs, table_name, duty_key="oo")
    elif duty_key == "oh":
        truncate_table(ws, conx, curs, table_name, duty_key="oh")
    else:
        truncate_table(ws, conx, curs, table_name)

    # Function to execute database work
    # need the duty_key to decide what to do
    # need the SQL statement
    # need the dataframe
    # need to know if store procedure must be run or not (boolean)
    grind_the_file(ws, duty_key, table_name, conx, curs, sqlstatement, df)