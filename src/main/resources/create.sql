CREATE TABLE Caregivers (
    Username varchar(255),
    Salt BINARY(16),
    Hash BINARY(16),
    PRIMARY KEY (Username)
);

CREATE TABLE Availabilities (
    Time date,
    Adminstrator varchar(255) REFERENCES Caregivers(Username) NOT NULL,
    PRIMARY KEY (Time, Administrator)
);

CREATE TABLE Vaccines (
    Name varchar(255),
    Doses int,
    PRIMARY KEY (Name)
);

CREATE TABLE Patient (
    Username varchar(255),
    Salt BINARY(16),
    Hash BINARY(16),
    PRIMARY KEY (Username)
);

CREATE TABLE Appointments (
    apID int,
    Time date,
    cUsername varchar(255) REFERENCES Caregivers,
    pUsername varchar(255) REFERENCES Patients,
    Name varchar(255) REFERENCES Vaccines,
    PRIMARY KEY (apID)
);