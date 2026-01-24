from openpyxl import Workbook
from openpyxl.worksheet.datavalidation import DataValidation

HEADERS = [
    "Activity Name",
    "Cluster",
    "Funder",
    "Planned Implementation Month",
    "Budget Amount",
    "Implementation Status",
    "Key Notes",
]

def generate_template(path, clusters, funders, statuses):
    wb = Workbook()
    ws = wb.active
    ws.append(HEADERS)

    ws.add_data_validation(DataValidation(
        type="list",
        formula1=f'"{",".join(clusters)}"',
        allow_blank=True
    ))

    ws.add_data_validation(DataValidation(
        type="list",
        formula1=f'"{",".join(funders)}"',
        allow_blank=True
    ))

    ws.add_data_validation(DataValidation(
        type="list",
        formula1=f'"{",".join(statuses)}"',
        allow_blank=True
    ))

    wb.save(path)
