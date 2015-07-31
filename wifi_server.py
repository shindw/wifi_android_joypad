from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
from SocketServer import ThreadingMixIn
import threading
import argparse
import re
import cgi
import sys,os
import RPi.GPIO as gpio
import time
import logging

path = os.path.dirname(os.path.realpath(__file__))
if not os.path.exists(path+'/log'):
    os.makedirs(path+'/log')
logging.basicConfig(filename=path+'/log/joystick.log', format='%(asctime)s %(levelname)s: %(message)s', datefmt='%Y/%m/%d %H:%M:%S', filemode='a', level=logging.INFO)

#Motor 1 GPIO Pin
IC1_A = 27
IC1_B = 22

#Motor 2 GPIO Pin
IC2_A = 17
IC2_B = 23

gpio.setmode(gpio.BCM)

#Motor Pin Setup
gpio.setup(IC1_A, gpio.OUT)
gpio.setup(IC1_B, gpio.OUT)
gpio.setup(IC2_A, gpio.OUT)
gpio.setup(IC2_B, gpio.OUT)

IS_PRINT_LOG = True

def LOG(level, message):
    if level is 'info':
        logging.info(message)
    if level is 'error':
        logging.error(message)
    if level is 'debug':
        logging.debug(message)
    if IS_PRINT_LOG:
        print(message)

class LocalData(object):
	records = {}

class HTTPRequestHandler(BaseHTTPRequestHandler):
	def do_POST(self):
		#print(self.path)
		if None != re.search('/setrc/*', self.path):

			self.parsingData(self.path)

			ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
			if ctype == 'application/x-www-form-urlencoded':
				length = int(self.headers.getheader('content-length'))
				data = cgi.parse_qs(self.rfile.read(length), keep_blank_values=1)
				recordID = self.path.split('/')[-1]
				LocalData.records[recordID] = data

				print "record %s is added successfully" % recordID
			else:
				data = {}

			self.send_response(200)
			self.end_headers()
		else:
			self.send_response(403)
			self.send_header('Content-Type', 'application/x-www-form-urlencoded')
			self.end_headers()

		return

	def do_GET(self):
                print(self.path)
		if None != re.search('/getrc/*', self.path):
			recordID = self.path.split('/')[-1]
			if LocalData.records.has_key(recordID):
				self.send_response(200)
				self.send_header('Content-Type', 'application/x-www-form-urlencoded')
				self.end_headers()
				self.wfile.write(LocalData.records[recordID])
			else:
				self.send_response(400, 'Bad Request: record does not exist')
				self.send_header('Content-Type', 'application/x-www-form-urlencoded')
				self.end_headers()
		else:
			self.send_response(403)
			self.send_header('Content-Type', 'application/x-www-form-urlencoded')
			self.end_headers()

		return

	def parsingData(self, data):
		data = data.replace("/setrc/", "").split(',')
		print(len(data))
		leftDist = int(data[0])
		leftAngle = int(data[1])
		rightDist = int(data[2])
		rightAngle = int(data[3])

        	if ( leftDist >= 5 and (leftAngle<9 or leftAngle>27)):
			forword()
		elif ( leftDist >= 5 and (leftAngle>9 and leftAngle<27)):
			backword()
		elif ( leftDist < 5 ):
			stopFB()

		if ( rightDist >= 5 and rightAngle<36/2):
			turnLeft()
		elif ( rightDist >= 5 and rightAngle>= 36/2):
			turnRight()
		elif ( rightDist < 5 ):
			stopLR()

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
	allow_reuse_address = True

	def shutdown(self):
		self.socket.close()
		HTTPServer.shutdown(self)

class SimpleHttpServer():
	def __init__(self, ip, port):
		self.server = ThreadedHTTPServer((ip,port), HTTPRequestHandler)

	def start(self):
		self.server_thread = threading.Thread(target=self.server.serve_forever)
		self.server_thread.daemon = True
		self.server_thread.start()

	def waitForThread(self):
		self.server_thread.join()

	def addRecord(self, recordID, jsonEncodedRecord):
		LocalData.records[recordID] = jsonEncodedRecord

	def stop(self):
		self.server.shutdown()
		self.waitForThread()

def forword():
    LOG('info','GPIO Forward')
    gpio.output(IC2_A, gpio.LOW)
    gpio.output(IC2_B, gpio.HIGH)

def backword():
    LOG('info','GPIO Backward')
    gpio.output(IC2_A, gpio.HIGH)
    gpio.output(IC2_B, gpio.LOW)

def turnLeft():
    LOG('info','GPIO Turn Left')
    gpio.output(IC1_A, gpio.HIGH)
    gpio.output(IC1_B, gpio.LOW)

def turnRight():
    LOG('info','GPIO Turn Right')
    gpio.output(IC1_A, gpio.LOW)
    gpio.output(IC1_B, gpio.HIGH)

def stopFB():
    LOG('info','GPIO Stop Back Wheel')
    gpio.output(IC2_A, gpio.LOW)
    gpio.output(IC2_B, gpio.LOW)

def stopLR():
    LOG('info','GPIO Front Wheel Zero')
    gpio.output(IC1_A, gpio.LOW)
    gpio.output(IC1_B, gpio.LOW)

if __name__=='__main__':
	parser = argparse.ArgumentParser(description='HTTP Server')
	parser.add_argument('port', type=int, help='Listening port for HTTP Server')
	parser.add_argument('ip', help='HTTP Server IP')
	args = parser.parse_args()

	server = SimpleHttpServer(args.ip, args.port)
	print 'HTTP Server Running...........'
	server.start()
	server.waitForThread()
