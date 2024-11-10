from model.Vaccine import Vaccine
from model.Caregiver import Caregiver
from model.Patient import Patient
from util.Util import Util
from db.ConnectionManager import ConnectionManager
import pymssql
import datetime
import re


'''
objects to keep track of the currently logged-in user
Note: it is always true that at most one of currentCaregiver and currentPatient is not null
        since only one user can be logged-in at a time
'''
current_patient = None

current_caregiver = None


def create_patient(tokens):
    # create_patient <username> <password>
    # check 1: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if (len(tokens) != 3):
        print("Failed to create user.")
        return

    username = tokens[1]
    password = tokens[2]

    # check 2: check if the username has been taken already
    if username_exists_patient(username):
        print("Username taken, try again!")
        return

    salt = Util.generate_salt()
    hash = Util.generate_hash(password, salt)

    # create the patient
    patient = Patient(username, salt=salt, hash=hash)

    # save to patient information to our database
    try:
        patient.save_to_db()
    except pymssql.Error as e:
        print("Failed to create user.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Failed to create user.")
        print(e)
        return
    print("Created user ",  username)


def username_exists_patient(username):
    cm = ConnectionManager()
    conn = cm.create_connection()

    select_username = "SELECT * FROM Patients WHERE Username = %s"
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute(select_username, username)
        #  returns false if the cursor is not before the first record or if there are no rows in the ResultSet.
        for row in cursor:
            return row['Username'] is not None
    except pymssql.Error as e:
        print("Error occurred when checking username")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when checking username")
        print("Error:", e)
    finally:
        cm.close_connection()
    return False


def create_caregiver(tokens):
    # create_caregiver <username> <password>
    # check 1: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Failed to create user.")
        return

    username = tokens[1]
    password = tokens[2]
    # check 2: check if the username has been taken already
    if username_exists_caregiver(username):
        print("Username taken, try again!")
        return

    salt = Util.generate_salt()
    hash = Util.generate_hash(password, salt)

    # create the caregiver
    caregiver = Caregiver(username, salt=salt, hash=hash)

    # save to caregiver information to our database
    try:
        caregiver.save_to_db()
    except pymssql.Error as e:
        print("Failed to create user.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Failed to create user.")
        print(e)
        return
    print("Created user ", username)


def username_exists_caregiver(username):
    cm = ConnectionManager()
    conn = cm.create_connection()

    select_username = "SELECT * FROM Caregivers WHERE Username = %s"
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute(select_username, username)
        #  returns false if the cursor is not before the first record or if there are no rows in the ResultSet.
        for row in cursor:
            return row['Username'] is not None
    except pymssql.Error as e:
        print("Error occurred when checking username")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when checking username")
        print("Error:", e)
    finally:
        cm.close_connection()
    return False


def login_patient(tokens):
    # login_patient <username> <password>
    # check 1: if someone's already logged-in, they need to log out first
    global current_patient
    if current_patient is not None or current_caregiver is not None:
        print("User already logged in.")
        return

    # check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Login failed.")
        return

    username = tokens[1]
    password = tokens[2]

    patient = None
    try:
        patient = Patient(username, password=password).get()
    except pymssql.Error as e:
        print("Login failed.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Login failed.")
        print(e)
        return

    if patient is None:
        print("Login failed.")
        return
    else:
        current_patient = patient
        print("Logged in as ", username)


def login_caregiver(tokens):
    # login_caregiver <username> <password>
    # check 1: if someone's already logged-in, they need to log out first
    global current_caregiver
    if current_caregiver is not None or current_patient is not None:
        print("User already logged in.")
        return

    # check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Login failed.")
        return

    username = tokens[1]
    password = tokens[2]

    caregiver = None
    try:
        caregiver = Caregiver(username, password=password).get()
    except pymssql.Error as e:
        print("Login failed.")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Login failed.")
        print("Error:", e)
        return

    # check if the login was successful
    if caregiver is None:
        print("Login failed.")
    else:
        print("Logged in as: " + username)
        current_caregiver = caregiver


def search_caregiver_schedule(tokens):
    #  search_caregiver_schedule <date>
    #  check 1: check if the current logged-in user is a patient or a caregiver
    if current_caregiver is None and current_patient is None:
        print("Please login first!")
        return
    
    # check 2: the length for tokens need to be exactly 2 to include all information (with the operation name)
    if len(tokens) != 2:
        print("Please input the right arguments.")
        return

    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor()

    date_tokens = tokens[1].split("-")
    month = int(date_tokens[0])
    day = int(date_tokens[1])
    year = int(date_tokens[2])
    d = datetime.datetime(year, month, day)

    get_available_dates = "SELECT Time, Username FROM Availabilities WHERE Time = %s ORDER BY Username"
    get_vaccines = "SELECT Name, Doses FROM Vaccines"
    try:
        cursor.execute(get_available_dates, d)
        caregiver_rows = cursor.fetchall()

        cursor.execute(get_vaccines)
        vaccine_rows = cursor.fetchall()

        if not caregiver_rows: # no caregivers available
            print("There are no appointments available on", tokens[1])
            return
        
        vaccine_doses = vaccine_rows[0][1]
        if vaccine_doses == 0 or vaccine_doses < 0: # no vaccines available
            print("Not enough available doses!")
            return

        print("There is", len(caregiver_rows), "caregiver(s) available on", tokens[1], ":")
        for row in caregiver_rows:
            print("Caregiver:", row[1])
        
        print("There is",len(vaccine_rows), "vaccine(s) available:")
        for row in vaccine_rows:
            print("Vaccine:", row[0])
            print("Doses Left:", row[1])
        conn.commit()
    except pymssql.Error as e: # error handling for database errors
        print("Please try again!")
        print("Db-Error:", e)
        quit()
    except ValueError as e: # error handling for invalid date
        print("Please try again!")
        print("Error:", e)
        return
    except Exception as e: # error handling for other exceptions
        print("Please try again!")
        print("Error:", e)
        return
    finally:
        cm.close_connection()


def reserve(tokens):
    #  reserve <date> <vaccine>
    #  check 1: check if the current logged-in user is a patient
    global current_patient
    if current_caregiver is None and current_patient is None:
        print("Please login first!")
        return
    
    if current_patient is None:
        print("Please login as a patient first!")
        return

    # check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Please try again!")
        return
    
    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor()

    date = tokens[1]
    date_tokens = date.split("-")
    month = int(date_tokens[0])
    day = int(date_tokens[1])
    year = int(date_tokens[2])

    vaccine_name = tokens[2]
    
     # check for caregiver availability
    d = datetime.datetime(year, month, day)
    available_caregiver = get_available_caregiver(d)
    if available_caregiver == None:
        return
    # check for vaccine availability
    get_vaccine = "SELECT Name, Doses FROM Vaccines WHERE Name = %s"
        
    try:
        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor()
        cursor.execute(get_vaccine, (vaccine_name))
        doses = cursor.fetchone()
        
    except pymssql.Error as e:
        print("pymssql error")
        print("Db-Error:", e)
        quit()
    
    except Exception as e:
        print("Error occurred when making reservation")
        print("Error:", e)
        return
    if doses == None:
        print("This facility does not carry that brand of vaccines. Please try again!")
        return
    elif doses[1] == 0:
        print("Not enough available doses!")
        return

    # get appointment ID
    apID = get_apID()     

    print(f"Appointment ID: {apID}, Caregiver username: {available_caregiver}")

    # update caregiver availability

    # update appointments
    add_appointment = "INSERT INTO Appointments VALUES (%s, %s, %s, %s, %s)"

    try:
        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor()
        cursor.execute(add_appointment, (apID, available_caregiver, current_patient.username, d, vaccine_name))
        conn.commit()
    except pymssql.Error:
        raise
    finally:
        cm.close_connection()

    # update vaccines

    # create the vaccine
    named_vaccine = Vaccine(vaccine_name, 0)
    
    try:
        named_vaccine.get()
        named_vaccine.available_doses
        named_vaccine.decrease_available_doses(1)
    except pymssql.Error as e:
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when decreasing doses")
        print("Error:", e)
        return

    pass


def get_available_caregiver(d):

    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor()
    
    # find available caregivers
    available_caregiver = "SELECT Username FROM Availabilities WHERE Time = (%s) ORDER BY Username"

    try:
        cursor.execute(available_caregiver, (d))
        caregiver_username = cursor.fetchone()
    except pymssql.Error:
        raise    
    finally:
        cm.close_connection()
    if caregiver_username == None:
        print("No Caregiver is available!")
        return
    else:
        return caregiver_username[0]


def get_apID():

    get_last_apID = "SELECT MAX(apID) FROM Appointments"
    try:
        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor()
        cursor.execute(get_last_apID)
        last_apID = cursor.fetchone()[0]
        if last_apID == None:
            apID = 1    
        else: 
            apID = last_apID + 1
    except pymssql.Error:
        raise    
    finally:
        cm.close_connection()
    return apID


def upload_availability(tokens):

    global current_caregiver
    if current_caregiver is None:
        print("Please login as a caregiver first!")
        return

    if len(tokens) != 2:
        print("Please try again!")
        return

    date = tokens[1]
    # assume input is hyphenated in the format mm-dd-yyyy
    date_tokens = date.split("-")
    month = int(date_tokens[0])
    day = int(date_tokens[1])
    year = int(date_tokens[2])
    try:
        d = datetime.datetime(year, month, day)
        current_caregiver.upload_availability(d)
    except pymssql.Error as e:
        print("Upload Availability Failed")
        print("Db-Error:", e)
        quit()
    except ValueError:
        print("Please enter a valid date!")
        return
    except Exception as e:
        print("Error occurred when uploading availability")
        print("Error:", e)
        return
    print("Availability uploaded!")


def cancel(tokens):
    """
    Extra Credit
    """
    #  cancel <appointment_id>
    global current_caregiver
    global current_patient
    
    if current_patient is None and current_caregiver is None:
        print("Please log in!")
        return

    # check 2: the length for tokens need to be exactly 2 
    if len(tokens) != 2:
        print("Please try again!")
        return 
    
    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor(as_dict=True)

    delete = "DELETE FROM Appointments WHERE apID = %s"

    try:
        apID = tokens[1]

        cursor.execute(delete, apID)

        conn.commit()
    except:
        print("Please try again!")
        return
    print("Appointment", apID, "has been cancelled.")


def add_doses(tokens):
    #  add_doses <vaccine> <number>
    #  check 1: check if the current logged-in user is a caregiver
    global current_caregiver
    if current_caregiver is None:
        print("Please login as a caregiver first!")
        return

    #  check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Please try again!")
        return

    vaccine_name = tokens[1]
    doses = int(tokens[2])
    vaccine = None
    try:
        vaccine = Vaccine(vaccine_name, doses).get()
    except pymssql.Error as e:
        print("Error occurred when adding doses")
        print("Db-Error:", e)
        quit()
    except Exception as e:
        print("Error occurred when adding doses")
        print("Error:", e)
        return

    # if the vaccine is not found in the database, add a new (vaccine, doses) entry.
    # else, update the existing entry by adding the new doses
    if vaccine is None:
        vaccine = Vaccine(vaccine_name, doses)
        try:
            vaccine.save_to_db()
        except pymssql.Error as e:
            print("Error occurred when adding doses")
            print("Db-Error:", e)
            quit()
        except Exception as e:
            print("Error occurred when adding doses")
            print("Error:", e)
            return
    else:
        # if the vaccine is not null, meaning that the vaccine already exists in our table
        try:
            vaccine.increase_available_doses(doses)
        except pymssql.Error as e:
            print("Error occurred when adding doses")
            print("Db-Error:", e)
            quit()
        except Exception as e:
            print("Error occurred when adding doses")
            print("Error:", e)
            return
    print("Doses updated!")


def show_appointments(tokens):
    # show_appointments
    global current_caregiver
    global current_patient
    if current_caregiver is None and current_patient is None:
        print("Please login first!")
        return

    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor(as_dict=True)

    get_patient_appointment = "SELECT apID, Time, cUsername, pUsername, Name FROM Appointments WHERE pUsername = %s  ORDER BY apID"
    get_caregiver_appointment = "SELECT apID, Time, cUsername, pUsername, Name FROM Appointments WHERE cUsername = %s  ORDER BY apID"

    try:
        if current_patient is not None: # if the current user is a patient
            cursor.execute(get_patient_appointment, current_patient.username)
            appointment_rows = cursor.fetchall()
            for i in range(0, len(appointment_rows)):
                print(f"Appointment ID: {appointment_rows[i]['apID']}, Vaccine name: {appointment_rows[i]['Name']}," +
                f" Appointment Time: {appointment_rows[i]['Time']}, Caregiver Username: {appointment_rows[i]['cUsername']}")
        
        if current_caregiver is not None: # if the current user is a caregiver
            cursor.execute(get_caregiver_appointment, current_caregiver.username)
            appointment_rows = cursor.fetchall()
            for i in range(0, len(appointment_rows)):
                print(f"Appointment ID: {appointment_rows[i]['apID']}, Vaccine name: {appointment_rows[i]['Name']}," +
                f" Appointment Time: {appointment_rows[i]['Time']}, Patient Username: {appointment_rows[i]['pUsername']}")
    except pymssql.Error as e:
        print("Upload Availability Failed")
        print("Db-Error:", e)
        quit()
    except ValueError:
        print("Please enter a valid date!")
        return
    except Exception as e:
        print("Error occurred when uploading availability")
        print("Error:", e)
        return
    finally:
        cm.close_connection()


def logout(tokens):
    # logout
    global current_caregiver
    global current_patient

    try: 
        if current_caregiver is None and current_patient is None:
            print("Please login first!")
            return
        else: 
            current_caregiver = None
            current_patient = None
            print("Successfully logged out!")
            start()
    except Exception as e:
        print("Please try again!")
        print("Error:", e)
        return
    

def start():
    stop = False
    print()
    print(" *** Please enter one of the following commands *** ")
    print("> create_patient <username> <password>")  # //TODO: implement create_patient (Part 1)
    print("> create_caregiver <username> <password>")
    print("> login_patient <username> <password>")  # // TODO: implement login_patient (Part 1)
    print("> login_caregiver <username> <password>")
    print("> search_caregiver_schedule <date>")  # // TODO: implement search_caregiver_schedule (Part 2)
    print("> reserve <date> <vaccine>")  # // TODO: implement reserve (Part 2)
    print("> upload_availability <date>")
    print("> cancel <appointment_id>")  # // TODO: implement cancel (extra credit)
    print("> add_doses <vaccine> <number>")
    print("> show_appointments")  # // TODO: implement show_appointments (Part 2)
    print("> logout")  # // TODO: implement logout (Part 2)
    print("> Quit")
    print()
    while not stop:
        response = ""
        print("> ", end='')

        try:
            response = str(input())
        except ValueError:
            print("Please try again!")
            break

        response = response.lower()
        tokens = response.split(" ")
        if len(tokens) == 0:
            ValueError("Please try again!")
            continue
        operation = tokens[0]
        if operation == "create_patient":
            create_patient(tokens)
        elif operation == "create_caregiver":
            create_caregiver(tokens)
        elif operation == "login_patient":
            login_patient(tokens)
        elif operation == "login_caregiver":
            login_caregiver(tokens)
        elif operation == "search_caregiver_schedule":
            search_caregiver_schedule(tokens)
        elif operation == "reserve":
            reserve(tokens)
        elif operation == "upload_availability":
            upload_availability(tokens)
        elif operation == "cancel":
            cancel(tokens)
        elif operation == "add_doses":
            add_doses(tokens)
        elif operation == "show_appointments":
            show_appointments(tokens)
        elif operation == "logout":
            logout(tokens)
        elif operation == "quit":
            print("Bye!")
            stop = True
        else:
            print("Invalid operation name!")


if __name__ == "__main__":
    '''
    // pre-define the three types of authorized vaccines
    // note: it's a poor practice to hard-code these values, but we will do this ]
    // for the simplicity of this assignment
    // and then construct a map of vaccineName -> vaccineObject
    '''

    # start command line
    print()
    print("Welcome to the COVID-19 Vaccine Reservation Scheduling Application!")

    start()
