import pandas as pd
import sys

#csv files
employee_file="zenvy_employees.csv"
attendance_file="zenvy_attendance.csv"
old_payroll_file="zenvy_payroll.csv"
output_file="generated_payroll_report.csv"

PF_RATE=0.10
BASE_TAX_RATE=0.05
HIGH_TAX_RATE=0.08
OVERTIME_RATE=200
BONUS_AMOUNT=1000


#helper functions
def load_csv(file_path):
    try:
        df = pd.read_csv(file_path)
        print(f"Loaded {file_path} ({len(df)} records)")
        return df
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
        sys.exit()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        sys.exit()


def validate_columns(df, required_columns, file_name):
    for col in required_columns:
        if col not in df.columns:
            print(f"Column '{col}' missing in {file_name}")
            sys.exit()


def safe_numeric(series, column_name):
    return pd.to_numeric(series, errors='coerce').fillna(0)


#loading files
employees=load_csv(employee_file)
attendance=load_csv(attendance_file)
old_payroll=load_csv(old_payroll_file)

#validating required columns
validate_columns(employees,
                 ["employee_id", "employee_name", "department", "base_salary"],
                 employee_file)

validate_columns(attendance,
                 ["employee_id", "working_days", "present_days", "overtime_hours"],
                 attendance_file)

validate_columns(old_payroll,
                 ["employee_id", "net_salary"],
                 old_payroll_file)

#merging data
try:
    data=pd.merge(employees, attendance, on="employee_id", how="inner")
    print(f"Loaded data successfully ({len(data)} employees)")
except Exception as e:
    print("Error merging data:", e)
    sys.exit()

#data cleaning
data["base_salary"]=safe_numeric(data["base_salary"], "base_salary")
data["working_days"]=safe_numeric(data["working_days"], "working_days")
data["present_days"]=safe_numeric(data["present_days"], "present_days")
data["overtime_hours"]=safe_numeric(data["overtime_hours"], "overtime_hours")

#Remove invalid working days
data = data[data["working_days"]>0]

#Adjust invalid attendance
data.loc[data["present_days"]>data["working_days"],"present_days"]=data["working_days"]

#payroll calculations
data["salary_per_day"]=data["base_salary"]/data["working_days"]
data["attendance_salary"]=data["salary_per_day"]*data["present_days"]
data["overtime_salary"]=data["overtime_hours"]*OVERTIME_RATE

#Bonus logic
data["bonus"]=data["present_days"].apply(lambda x:BONUS_AMOUNT if x>20 else 0)

data["gross_salary"]=data["attendance_salary"]+data["overtime_salary"]+data["bonus"]

#Tax slab logic
data["tax"]=data["gross_salary"].apply(
    lambda x:x*HIGH_TAX_RATE if x>60000 else x*BASE_TAX_RATE
)

data["pf"]=data["gross_salary"]*PF_RATE

data["total_deductions"]=data["tax"]+data["pf"]
data["net_salary"]=data["gross_salary"]-data["total_deductions"]

#Round values
data["gross_salary"]=data["gross_salary"].round(2)
data["net_salary"]=data["net_salary"].round(2)
data["total_deductions"]=data["total_deductions"].round(2)

#payroll validation
comparison=pd.merge(
    data[["employee_id", "net_salary"]],
    old_payroll[["employee_id", "net_salary"]],
    on="employee_id",
    how="left",
    suffixes=("_new", "_old")
)

comparison["difference"]=comparison["net_salary_new"]-comparison["net_salary_old"]

changed_records=comparison[comparison["difference"]!=0]

print(f"Payroll validation completed")
print(f"Changed salary records: {len(changed_records)}")

#summary report
print("\nPayroll Summary Report:")
print("Total Employees Processed :",len(data))
print("Total Gross Salary        :",round(data["gross_salary"].sum(),2))
print("Total Net Salary          :",round(data["net_salary"].sum(),2))
print("Total Tax Collected       :",round(data["tax"].sum(),2))
print("Total PF Collected        :",round(data["pf"].sum(),2))
print("Highest Salary            :",round(data["net_salary"].max(),2))
print("Lowest Salary             :",round(data["net_salary"].min(),2))
print("Average Salary            :",round(data["net_salary"].mean(),2))

#final output
final_payroll=data[
    [
        "employee_id",
        "employee_name",
        "department",
        "gross_salary",
        "total_deductions",
        "net_salary"
    ]
]

try:
    final_payroll.to_csv(output_file,index=False)
    print(f"\nFinal payroll report saved as '{output_file}'")
except Exception as e:
    print("Error saving payroll file:",e)

print("\nPayroll Processing Completed Successfully")