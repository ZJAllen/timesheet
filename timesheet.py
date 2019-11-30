from datetime import datetime, timedelta
import calendar
# import appex
# import ui
import os


class Filenames():
    timesheet = 'timesheet.txt'
    monday = 'monday.txt'
    tuesday = 'tuesday.txt'
    wednesday = 'wednesday.txt'
    thursday = 'thursday.txt'
    friday = 'friday.txt'


# Create insance of Filenames class
files = Filenames()


class Clock():
    timeIn = None
    timeOut = None
    lunch = 0
    
    currentWeekday = ''
    currentDate = ''
    monday = 0
    tuesday = 0
    wednesday = 0
    thursday = 0
    friday = 0

    def setDayMinutes(self, day, mins):
        if day == 'monday':
            self.monday = mins
        if day == 'tuesday':
            self.tuesday = mins
        if day == 'wednesday':
            self.wednesday = mins
        if day == 'thursday':
            self.thursday = mins
        if day == 'friday':
            self.friday = mins

    def getWeekTotal(self):
        return self.monday + self.tuesday + self.wednesday + self.thursday + self.friday


# Create instance of Clock class
clock = Clock()


### Function Definitions ###


# Gets current total week time from all individual time sheets.
def getTotalWeekTime(today_int):
    for i in range(today_int, -1, -1):
        weekday = calendar.day_name[i].lower()
        
        with open(f'{weekday}.txt', 'r') as f:
            dayMinutes = int(f.readlines()[-1].strip().replace('Total: ',''))

        clock.setDayMinutes(weekday, dayMinutes)

    return clock.getWeekTotal()


# Convert clock in and out times into hours and minutes worked
def parseWorkTime():
    workDuration = clock.timeOut - clock.timeIn - timedelta(minutes=clock.lunch)
    
    workHours = int(workDuration.seconds/3600)
    workMinutes = int((workDuration.seconds/60) - (workHours*60))

    workDurationMinutes = (workHours * 60) + workMinutes

    return workDurationMinutes, workHours, workMinutes


# Reset the clock in/out time at the end of the day.
# This is used for pseudo-error checking
def resetTime():
    clock.timeIn = None
    clock.timeOut = None


def resetWeek():
    clock.monday = 0
    clock.tuesday = 0
    clock.wednesday = 0
    clock.thursday = 0
    clock.friday = 0

    for i in range(0, 4, 1):
        weekday = calendar.day_name[i].lower()
        os.remove(f'{weekday}.txt')


def writeToFile(filename, msg):
    with open(filename, 'a+') as f:
        f.write(msg)
        f.write('\n')


def getFileName(day_int):
    return f'{calendar.day_name[day_int].lower()}.txt'


def getLastLine(filename):
    with open(filename, 'r') as f:
        lastLine = f.readlines()[-1].strip()

    return lastLine


def existClockIn():
    try:
        weekday = datetime.now().weekday()
        # weekday = datetime(2019, 12, 6, 7, 30).weekday()
        with open(f'{getFileName(weekday)}', 'r') as f:
            f.readlines()[0]
        return True
    except:
        return False


def clockIn():
    # clock.timeIn = datetime(2019, 12, 6, 7, 30)
    clock.timeIn = datetime.now()

    clock.currentWeekday = calendar.day_name[clock.timeIn.weekday()]
    clock.currentDate = f'{clock.timeIn.month}/{clock.timeIn.day}/{clock.timeIn.year}'
    writeToFile(files.timesheet, f'{clock.currentWeekday} {clock.currentDate}')

    clockString = f'Clock In: {clock.timeIn.hour}:{clock.timeIn.minute}'
    writeToFile(files.timesheet, clockString)
    writeToFile(getFileName(clock.timeIn.weekday()), clockString)

    return clockString


def getClockInTime():
    weekday = datetime.now().weekday()
    # weekday = datetime(2019, 12, 6, 7, 30).weekday()
    clockTime = getLastLine(getFileName(weekday)).replace('Clock In: ', '').split(':')
    year = datetime.now().year
    # year = 2019
    month = datetime.now().month
    # month = 12
    day = datetime.now().day
    # day = 2
    hour = int(clockTime[0])
    minute = int(clockTime[1])
    clock.timeIn = datetime(year, month, day, hour, minute)
    clock.currentWeekday = calendar.day_name[clock.timeIn.weekday()]


def clockOut():
    clock.timeOut = datetime.now()
    # clock.timeOut = datetime(2019, 12, 6, 16, 15)
    clockString = f'Clock Out: {clock.timeOut.hour}:{clock.timeOut.minute}'
    writeToFile(files.timesheet, clockString)
    writeToFile(getFileName(clock.timeOut.weekday()), clockString)
    
    (totalMinutes, workHours, workMinutes) = parseWorkTime()
    writeToFile(files.timesheet, f'Total: {int(totalMinutes/60)}:{int(totalMinutes%60)}')
    writeToFile(getFileName(clock.timeOut.weekday()), f'Total: {totalMinutes}')

    #clock.setDayMinutes(clock.currentWeekday.lower(), totalMinutes)
    weekTotal = getTotalWeekTime(clock.timeOut.weekday())
    writeToFile(files.timesheet, f'Total Week Time: {int(weekTotal/60)}:{int(weekTotal%60)}\n')

    if clock.timeOut.weekday() == 4:
        resetWeek()

    resetTime()

    return clockString


def processClock(msg):
    if msg == 'in':
        if not existClockIn():
            clockString = clockIn()
        else:
            clockString = 'You are already clocked in!'
    
    if msg == 'out':
        if (clock.timeIn is not None) and (clock.timeOut is None):
            clockString = clockOut()

        elif existClockIn():
            getClockInTime()
            clockString = clockOut()
            
        else:
            clockString = 'You are not yet clocked in!'

    return clockString



def main():
    print(processClock('in'))
    print(processClock('out'))

if __name__ == '__main__':
    main()