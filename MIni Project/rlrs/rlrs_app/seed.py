"""Demo data. Fake .test addresses only: never put real student emails here."""
from . import service


def seed(conn):
    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]:
        return False
    admin = service.register_user(conn, "Admin User", "admin@lab.test", "admin123", "Admin")
    inch = service.register_user(conn, "Lab In-charge", "incharge@lab.test", "incharge123", "LabInCharge")
    service.register_user(conn, "Student One", "student1@lab.test", "student123", "Student")
    service.register_user(conn, "Student Two", "student2@lab.test", "student123", "Student")
    conn.execute("INSERT INTO labs(name,incharge_id) VALUES('Electronics Lab',?)", (inch["id"],))
    conn.execute("INSERT INTO labs(name,incharge_id) VALUES('Fabrication Lab',?)", (inch["id"],))
    for lab, name, type_, desc, approval in [
        (1, "Digital Oscilloscope", "Instrument", "4-channel, 200 MHz", 0),
        (1, "Logic Analyzer", "Instrument", "16-channel", 0),
        (2, "3D Printer", "Fabrication", "FDM printer, needs approval", 1),
    ]:
        conn.execute("INSERT INTO equipment(lab_id,name,type,description,requires_approval) VALUES(?,?,?,?,?)", (lab, name, type_, desc, approval))
    return True
