from datetime import datetime, timedelta
import calendar
# import appex
# import ui
# import os


class Clock():
    timeIn = None
    timeOut = None
    lunch = 0
    
    currentWeekday = ''
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

# Define filename
filename = 'timesheet.txt'


### Function Definitions ###


# Get date of the end of the week, which corresponds to the dropdown
# to select the current timesheet
def getEndOfPayWeek(clockIn):
    daysUntilSaturday = timedelta((12 - clockIn.weekday()) % 7)
    nextSaturday = clockIn + daysUntilSaturday

    weekEndingDate = f"{nextSaturday.month}/{nextSaturday.day}/{nextSaturday.year}"

    return weekEndingDate


# Select current timecard from dropdown on home screen
def selectTimeCard(browser, weekEndingDate):
    timeCardWeekId = "WeekEnding1"
    timeCardDropdown = Select(browser.find_element_by_id(timeCardWeekId))
    timeCardDropdown.select_by_value(weekEndingDate)

    return browser


# Gets current total week time from timecard in browser.
# TODO: add support to get time from database, to compare?
def getTotalWeekTime(browser):
    totalWeekHoursId = "repStandardTimecards_ctl00_StandardTime_repTimetotals_ctl01_StandardTimeRowTotal_TotalHoursControl_HoursTextBox"
    totalWeekMinutesId = "repStandardTimecards_ctl00_StandardTime_repTimetotals_ctl01_StandardTimeRowTotal_TotalHoursControl_MinutesTextBox"

    totalWeekHours = int(browser.find_element_by_id(totalWeekHoursId).get_attribute("value"))
    totalWeekMinutes = int(browser.find_element_by_id(totalWeekMinutesId).get_attribute("value"))

    return totalWeekHours, totalWeekMinutes


# Convert clock in and out times into hours and minutes worked
def parseWorkTime():
    workDuration = clock.timeOut - clock.timeIn - timedelta(minutes=clock.lunch)
    
    workHours = int(workDuration.seconds/3600)
    workMinutes = int((workDuration.seconds/60) - (workHours*60))

    workDurationMinutes = (workHours * 60) + workMinutes

    return workDurationMinutes, workHours, workMinutes


# Determine if in OT (or if today's time puts us in OT),
# and divide hours/minutes accordingly
def allocateTime(browser, todayHours, todayMinutes):
    # Call getTotalWeekTime function
    totalWeekHours, totalWeekMinutes = getTotalWeekTime(browser)

    totalTimeHours = ((todayHours * 60) + (totalWeekHours * 60) + todayMinutes + totalWeekMinutes) / 60

    if totalTimeHours > 40:
        overTimeTotalMinutes = round((totalTimeHours - 40) * 60)
        overTimeMinutes = overTimeTotalMinutes % 60
        overTimeHours = int((overTimeTotalMinutes - overTimeMinutes) / 60)

        todayTotalMinutes = (todayHours * 60) + todayMinutes
        todayRegularTimeMinutes = todayTotalMinutes - overTimeTotalMinutes
        regularTimeMinutes = todayRegularTimeMinutes % 60
        regularTimeHours = int((todayRegularTimeMinutes - regularTimeMinutes)/60)

    else:
        regularTimeHours = todayHours
        regularTimeMinutes = todayMinutes
        overTimeHours = 0
        overTimeMinutes = 0

    return regularTimeHours, regularTimeMinutes, overTimeHours, overTimeMinutes


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


'''
Clock In
    Log clock in time (database?)
Clock Out
    Pull clock in time, flag if it doesn't exist (how?)
    Log clock out time (database?)
Calculate total time (hours and minutes)
    Check if total weekly time >40 hours
        If so, start adding hours/minutes to OT
        If hours >=40 and minutes >0, move hours to OT
            Start populating only OT
Log total time in hours, minutes (in database?)

Log in to time and expense
Select current time sheet
    based on date of week end (week starts on Sunday, ends on Saturday)
Log time in hours and minutes
Click save

If end of week
    submit timesheet
'''


def logTime(clockIn, todayHours, todayMinutes):
    browser = startBrowser()
    browser = logIn(browser)

    weekEndingDate = getEndOfPayWeek(clockIn)

    browser = selectTimeCard(browser, weekEndingDate)

    regHours, regMins, OTHours, OTMins = allocateTime(browser, todayHours, todayMinutes)
    print(f"Reg: {regHours}:{regMins}, OT: {OTHours}:{OTMins}")

    assignHours(browser, clockIn.weekday(), regHours, regMins, OTHours, OTMins)

    browser = saveData(browser)

    # If it's Friday, submit timesheet
    if calendar.day_name[clockIn.weekday()] == "Friday":
        browser = submitTimecard(browser)

    browser.close()


def writeToFile(msg):
    with open(filename, 'a+') as f:
        f.write(msg)
        f.write('\n')


def getLastLine():
    with open(filename, 'r') as f:
        lastLine = f.readlines()[-1].strip()

    return lastLine


def existClockIn(lastLine):
    if lastLine.find('Clock In: ') != -1:
        return True
    else:
        return False


def getClockInTime(lastLine):
    clockTime = lastLine.replace('Clock In: ', '').split(':')
    #year = datetime.now().year
    year = 2019
    # month = datetime.now().month
    month = 11
    #day = datetime.now().day
    day = 25
    hour = int(clockTime[0])
    minute = int(clockTime[1])
    clock.timeIn = datetime(year, month, day, hour, minute)
    clock.currentWeekday = calendar.day_name[clock.timeIn.weekday()]


def clockOut():
    clock.timeOut = datetime(2019, 11, 25, 16, 15)
    clockString = f'Clock Out: {clock.timeOut.hour}:{clock.timeOut.minute}'
    writeToFile(clockString)
    
    (totalMinutes, workHours, workMinutes) = parseWorkTime()
    clock.setDayMinutes(clock.currentWeekday.lower(), totalMinutes)
    weekTotal = clock.getWeekTotal()
    writeToFile(f'Total Week Time: {int(weekTotal/60)}:{int(weekTotal%60)}')
    writeToFile('\n')

    return clockString


def processClock(msg):
    if msg == 'in':
        if clock.timeIn is None:
            clock.timeIn = datetime(2019, 11, 25, 7, 30)
            clock.currentWeekday = calendar.day_name[clock.timeIn.weekday()]
            writeToFile(f'{clock.currentWeekday} {clock.timeIn.month}/{clock.timeIn.day}/{clock.timeIn.year}')
            clockString = f'Clock In: {clock.timeIn.hour}:{clock.timeIn.minute}'
            writeToFile(clockString)
        else:
            clockString = 'You are already clocked in!'
    
    if msg == 'out':
        if (clock.timeIn is not None) and (clock.timeOut is None):
            clockString = clockOut()

        elif existClockIn(getLastLine()):
            getClockInTime(getLastLine())
            clockString = clockOut()
            
        else:
            clockString = 'You are not yet clocked in!'

    return clockString



def main():
    print(processClock('in'))
    print(processClock('out'))

if __name__ == '__main__':
    main()