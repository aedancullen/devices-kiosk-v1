
from pygamefb import pygameFramebuffer
import pygame
import MySQLdb
import time
import datetime
import sys
import select
import RPi.GPIO as gpio
import subprocess

#Chromebook system version 1

imageDir = '/home/pi/chromebooks/graphics/'
gpio.setmode(gpio.BCM)
gpio.setup(7, gpio.IN)

pygame.mixer.init()
ding = pygame.mixer.Sound("ding.wav")
buzzer = pygame.mixer.Sound("buzzer.wav")


def loadImage(name):
        #print '\tloading image', name, '...'
        image = pygame.image.load(imageDir + name + '.png')
        return pygame.transform.smoothscale(image,(pygame.display.Info().current_w, pygame.display.Info().current_h))

def displayImage(img):
        display.screen.blit(img, (0,0))
        pygame.display.update()

def executeSQL(conn, sql, params):
        cursor = conn.cursor()
        cursor.execute(sql, params)
        ret = cursor.fetchall()
        cursor.close()
        return ret

def connect():
        db = None
        count = 0
        while not db:
                if count >= 2:
                        displayImage(loading)
                try:
                        db = MySQLdb.connect(host="127.0.0.1", db="chromebooks", user="root", passwd="halibrary131", connect_timeout=1)
                except:
                        count += 1
                        for event in pygame.event.get():
                                if event.type == pygame.KEYDOWN:
                                        if event.key == pygame.K_ESCAPE:
                                                pygame.quit()
                                                sys.exit()
        return db

def processSignout(conn, studentID, studentName):
        displayImage(signout)
        gotValidChromebook = False
        while not gotValidChromebook:
                #print 'Waiting for chromebook to be scanned now'
                input = getPygameInput()
                #displayImage(loading)
                gotValidChromebook = executeSQL(conn, """SELECT * FROM Assignments WHERE ChromebookID=%s LIMIT 1""", (input,))
                if not gotValidChromebook:
                        #print 'User did not scan valid chromebook'
                        displayImage(problemchromebook)
        #print 'Registering chromebook signout'
        lastOut = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        executeSQL(conn, """UPDATE Assignments SET LastAssigneeID=AssigneeID, LastAssigneeName=AssigneeName, AssigneeID=NULL, AssigneeName=NULL, LastIn=%s WHERE ChromebookID=%s AND AssigneeID IS NOT NULL LIMIT 1""", (lastOut, input))
        executeSQL(conn, """UPDATE Assignments SET AssigneeID=%s, AssigneeName=%s, LastOut=%s WHERE ChromebookID=%s LIMIT 1""", (studentID, studentName[0][0], lastOut, input))
        # Log history (date, action, ChromebookID, StudentID)
        executeSQL(conn, """INSERT INTO History VALUES (%s, %s, %s, %s)""", (lastOut, 'Out', input, studentID))
        displayImage(signoutconfirm)

def processReturn(conn, chromebookID):
        #res = executeSQL(conn, """SELECT AssigneeID FROM Assignments WHERE ChromebookID=%s LIMIT 1""", (chromebookID,))
        #if res[0][0] == None:
        #    buzzer.play()
        lastIn = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        executeSQL(conn, """UPDATE Assignments SET LastAssigneeID=AssigneeID, LastAssigneeName=AssigneeName, AssigneeID=NULL, AssigneeName=NULL, LastIn=%s WHERE ChromebookID=%s AND AssigneeID IS NOT NULL LIMIT 1""", (lastIn, chromebookID,))
        #if not gpio.input(7): displayImage(_return)
        #while not gpio.input(7): time.sleep(0.01)
        # Log history (date, action, ChromebookID, StudentID)
        executeSQL(conn, """INSERT INTO History VALUES (%s, %s, %s, %s)""", (lastIn, 'In', chromebookID, ''))
        displayImage(returnconfirm)


def getPygameInput():
        input = ''
        start = time.time()
        exit = False
        while not exit:
                for event in pygame.event.get():
                        if event.type == pygame.KEYDOWN and time.time() >= start + 0.5:
                                if event.key == pygame.K_ESCAPE:
                                        pygame.quit()
                                        sys.exit()
                                elif event.key == pygame.K_RETURN:
                                        exit = True
                                else:
                                        try:
                                                input += chr(event.key)
                                        except: pass
                time.sleep(0.01)

        return input

def processStdinData():
        #print 'Getting input using pygame'
        input = ''
        start = time.time()
        shown = False
        exit = False
        while not exit:
                if time.time() > start + 3 and not shown:
                        shown = True
                        displayImage(welcome)
                        #print 'Displayed welcome image'
                for event in pygame.event.get():
                        if event.type == pygame.KEYDOWN and time.time() >= start + 0.5:
                                if event.key == pygame.K_ESCAPE:
                                        pygame.quit()
                                        sys.exit()
                                elif event.key == pygame.K_RETURN:
                                        exit = True
                                else:
                                        try:
                                                input += chr(event.key)
                                        except: pass
                time.sleep(0.01)

        if input == "systemexit":
                pygame.quit()
                sys.exit()
        elif input == "systemoff":
                pygame.quit()
                subprocess.call('sudo poweroff', shell=True);
        #print 'Input is', input
        #print 'Opening connection'
        #displayImage(loading)
        conn = connect()
        #print 'Checking Students table'
        result = executeSQL(conn, """SELECT StudentName FROM Students WHERE StudentID=%s LIMIT 1""", (input,))
        if result:
                #print 'Scanned ID is a student'
                processSignout(conn, input, result)
        else:
                #print 'Checking Assignments table'
                if executeSQL(conn, """SELECT * FROM Assignments WHERE ChromebookID=%s LIMIT 1""", (input,)):
                        #print 'Scanned ID is a chromebook'
                        processReturn(conn, input)
                else:
                        #print 'Problem, ID not recognized'
                        displayImage(problemwha)
        #print 'Closing connection'
        conn.commit()
        conn.close()

subprocess.call('killall fbi', shell=True)
#print 'Starting pygame...'
display = pygameFramebuffer()
pygame.mouse.set_visible(False)
#print 'Loading graphics...'
loading = loadImage('loading')
displayImage(loading)
#print 'Loading image has been displayed'
problemchromebook = loadImage('problemchromebook')
problemwha = loadImage('problemwha')
welcome = loadImage('welcome')
_return = loadImage('return')
signout = loadImage('signout')
returnconfirm = loadImage('returnconfirm')
signoutconfirm = loadImage('signoutconfirm')

#print 'Running initial connection check...'
conn = connect()
conn.close()
#print 'OK!'
#displayImage(welcome)

while True:
        #print 'Waiting for scanner input'
        processStdinData()
