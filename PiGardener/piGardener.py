from datetime import datetime
from yahoo_weather import get_weather

import time
import getpass
import mysql.connector
import RPi.GPIO as GPIO

def begin_watering():
    GPIO.setmode(GPIO.BCM)

    # setup the output pin and initialize it
    GPIO.setup(2, GPIO.OUT)
    GPIO.output(2, GPIO.HIGH)
    
    # turn the output pin on
    try:
        GPIO.output(2, GPIO.LOW)
        print("Motor On")
    
    # Interrupt Handler
    except KeyboardInterrupt:
        print ("Unknown error")
        # Reset GPIO settings
        GPIO.cleanup()

def stop_watering():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(2, GPIO.OUT)
    GPIO.output(2, GPIO.HIGH)
    print("Motor Off")
    GPIO.cleanup()

def fetch_readings():
    GPIO.setmode(GPIO.BCM)
    
    #Fetch Temperature and Humidity
    (temp, humidity) = get_weather("Bloomington, IN")

    #Fetch Soil Moisture
    GPIO.setup(3,GPIO.IN)
    moisture = GPIO.input(3)

    #Is there Sunlight
    GPIO.setup(4,GPIO.IN)
    light = GPIO.input(4)

    return (temp, humidity, moisture, light)

def monitor(username, pwd, host, dbname):
    #Connection setup
    conn = mysql.connector.connect(user=username,
                                   password=pwd,
                                   host=host,
                                   database=dbname,
                                   buffered=True)
    cur = conn.cursor()
    inner_cur = conn.cursor()

    #Check the schedules for any pending tasks
    schedule_query = """
            select schedule_id, user_name, task_name, notes, task_type, duration, schedule_type
              from SCHEDULES 
            where upper(schedule_type) = 'ONETIME'
            union
            select schedule_id, user_name, task_name, notes, task_type, duration, schedule_type
              from SCHEDULES 
            where upper(schedule_type) != 'ONETIME'
              and curdate() between IFNULL(start_date, curdate()) and IFNULL(end_date, curdate())
              and abs(time_to_sec(CURTIME())-(60*60*4)-time_to_sec(start_time))/60 <= 1;"""
    cur.execute(schedule_query)
    for (sid, uname, task, notes, ttype, duration, stype) in cur:
        print("User", str(uname), "has a task", task, "for duration", duration)

        #insert tasks in pending state
        rec_tasks_query = """insert into TASKS (schedule_id,user_name,task_type,task_name,notes,creation_time,status,duration)
                          values (%(schedule_id)s, %(user_name)s, %(task_type)s, %(task_name)s, %(notes)s, %(creation_time)s, %(status)s, %(duration)s)"""
        one_tasks_query = """insert into TASKS (user_name,task_type,task_name,notes,creation_time,status,duration)
                          values (%(user_name)s, %(task_type)s, %(task_name)s, %(notes)s, %(creation_time)s, %(status)s, %(duration)s)"""
        task_dict = {
            'schedule_id': sid,
            'user_name': uname,
            'task_type': ttype,
            'task_name': task,
            'notes': notes,
            'creation_time': datetime.now(),
            'status': 'PENDING',
            'duration': duration
        }
        if stype.upper() == 'ONETIME':
            del task_dict['schedule_id']
            print(task_dict)
            inner_cur.execute(one_tasks_query, task_dict)
        else:
            inner_cur.execute(rec_tasks_query, task_dict)
        last_insert_id = inner_cur.lastrowid
        #Start Watering
        begin_watering()

        time.sleep(duration)

        #Stop Watering
        stop_watering()

        #Update the status in task to Completed
        print('Updating the Task to Completed '+str(last_insert_id))
        inner_cur.execute("update TASKS set status = 'COMPLETED' where task_id = "+str(last_insert_id))
        if stype.upper() == 'ONETIME':
            print('Deleting the Schedule '+str(sid))
            inner_cur.execute("delete from SCHEDULES where schedule_id = "+str(sid))
    #Collect the temperature, moisture and humidity readings
    (temp_reading, humidity_reading, moisture_reading, sunlight_reading) = fetch_readings()

    # Insert the readings
    readings_query = """insert into READINGS (rtimestamp,temperature,humidity,moisture,sunlight)
                      values (%(time_stamp)s, %(temp)s, %(humidity)s, %(moisture)s, %(light)s)"""
    reading_dict = {
        'time_stamp': datetime.now(),
        'temp': temp_reading,
        'humidity': humidity_reading,
        'moisture': moisture_reading,
        'light': sunlight_reading,
    }
    cur.execute(readings_query, reading_dict)

    # Make sure data is committed to database
    conn.commit()

    #close all connections before program end
    cur.close()
    inner_cur.close()
    conn.close()
    
# __MAIN__
UNAME = input('User Name : ')
PWD = getpass.getpass('Password : ')
HOST = input('Host: ')
DBNAME = input('Instance Name: ')

while True:
    start_time = time.time()
    monitor(UNAME, PWD, HOST, DBNAME)
    end_time = time.time()
    print('Monitoring completed in '+str(end_time - start_time))
    time_diff = 60-(time.time() - start_time)
    print('Sleeping for '+str(time_diff)+' seconds');
    if(time_diff > 0):
        time.sleep(time_diff)
