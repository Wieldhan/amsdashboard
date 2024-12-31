import pyodbc

server = '10.10.10.105,1344'
database = 'AMS'
username = 'sa'
password = 'sa'
driver = 'ODBC Driver 17 for SQL Server'

connection = pyodbc.connect(
    f"DRIVER={{{driver}}};"
    f"SERVER={server};"
    f"DATABASE={database};"
    f"UID={username};"
    f"PWD={password};"
    f"Encrypt=no;"
    f"TrustServerCertificate=YES;"
)
print("Koneksi berhasil!")
