import math
    
def is_numeric(s):
	try:
		float(s)
		return True
	except ValueError:
		return False

def intrep(number):
	if(number == float("inf")):
		return "Infinity"
	if(math.isnan(number)):
		return "NaN"
	if(number == int(number)):
		return int(number)
	# determine when to use scientific notation
	if abs(number) > 1000000000 or abs(number) < 0.0000001:
		return "%.10g" % number
	else:
		return "%.10f" % round(number, 10)

class RPN:
	
	def __init__(self):
		self.stack = []
		self.memory = 0 # for operations such as M-, M+
		self.message = "" # output being viewed
		self.verbose = False

	def send_input(self, inputstring):
		self.rpncalc(inputstring.split(" "));
		return
	
	def get_stacktop(self):
		if len(self.stack) == 0:
			return "The stack is empty."
		return str(intrep(self.stack[len(self.stack) - 1]))

	def rpncalc(self, queue):
		for elt in queue:
			# numbers
			if is_numeric(elt):
				self.stack.append(float(elt))
				if self.verbose == True:
					print "New stack:", self.stack
				
			# calculator buttons
			elif elt == "reset" or elt.upper() == "AC":
				del self.stack[0:len(self.stack)]
			elif (elt == "cancel" or elt.upper() == "C" or elt.upper() == "CE") and len(self.stack) >= 1:
				self.stack.pop() # and do nothing with it

			# self.memory operations
			elif (elt.upper() == "M-") and len(self.stack) >= 1:
				self.memory -= self.stack.pop()
				if self.verbose == True:
					print ("self.memory: %s" % intrep(self.memory))
			elif (elt.upper() == "M+") and len(self.stack) >= 1:
				self.memory += self.stack.pop()
				if self.verbose == True:
					print ("self.memory: %s" % intrep(self.memory))
			elif (elt.upper() == "MR") and len(self.stack) >= 1:
				self.message = "self.memory: %s" % intrep(self.memory)
			elif (elt.upper() == "MC") and len(self.stack) >= 1:
				self.memory = 0
				self.message = "self.memory has been cleared."


			# constants
			elif elt == "e":
				self.stack.append(math.e)
			elif elt == "p" or elt == "pi":
				self.stack.append(math.pi)


			# operators
			elif elt == "+":
				if len(self.stack) < 2:
					self.message = "Error: +: not enough items in stack!"
					break
				else:
					b = self.stack.pop()
					a = self.stack.pop()
					self.stack.append(a + b)
					self.message = ""
					if self.verbose == True:
						print ("Result of RPN +: %s" % self.stack[len(self.stack)-1])
						print "Remaining stack:", (self.stack)
					
			elif elt == "-":
				if len(self.stack) < 2:
					self.message = "Error: -: not enough items in stack!"
					break
				else:
					b = self.stack.pop()
					a = self.stack.pop()
					self.stack.append(a - b)
					self.message = ""
					if self.verbose == True:
						print ("Result of RPN -: %s" % self.stack[len(self.stack)-1])
						print "Remaining stack:", (self.stack)
					
			elif elt == "*":
				if len(self.stack) < 2:
					self.message = "Error: *: not enough items in stack!"
					break
				else:
					b = self.stack.pop()
					a = self.stack.pop()
					self.stack.append(a * b)
					self.message = ""
					if self.verbose == True:
						print ("Result of RPN *: %s" % self.stack[len(self.stack)-1])
						print "Remaining stack:", (self.stack)
					
			elif elt == "/":
				if len(self.stack) < 2:
					self.message = "Error: /: not enough items in stack!"
					break
				else:
					b = self.stack.pop()
					if(b == 0):
						self.message = "Error: %: attempting to divide by 0!"
						break
					a = self.stack.pop()
					self.stack.append(float(a) / float(b))
					self.message = ""
					if self.verbose == True:
						print ("Result of RPN /: %s" % self.stack[len(self.stack)-1])
						print "Remaining stack:", (self.stack)
					
			elif elt == "^" or elt == "**" or elt == "pwr":
				if len(self.stack) < 2:
					self.message = "Error: ^: not enough items in stack!"
				else:
					b = self.stack.pop()
					a = self.stack.pop()
					if(a == 0 and b <= 0 or a < 0 and b != int(b)):
						self.message = "Error: ^: invalid input!"
						break
					self.stack.append(a ** b)
					self.message = ""
					if self.verbose == True:
						print ("Result of RPN ^: %s" % self.stack[len(self.stack)-1])
						print "Remaining stack:", (self.stack)
					
			elif elt == "mod":
				if len(self.stack) < 2:
					self.message = "Error: mod: not enough items in stack!"
				else:
					b = self.stack.pop()
					if(b == 0):
						self.message = "Error: mod: attempting to take mod of 0!"
						break
					a = self.stack.pop()
					self.stack.append(a % b)
					self.message = ""
					if self.verbose == True:
						print ("Result of RPN mod: %s" % self.stack[len(self.stack)-1])
						print "Remaining stack:", (self.stack)
					
			elif elt == "sqr":
				if len(self.stack) < 1:
					self.message = "Error: sqr: not enough items in stack!"
				else:
					a = self.stack.pop()
					self.stack.append(a * a)
					self.message = ""
					if self.verbose == True:
						print ("Result of RPN sqr: %s" % self.stack[len(self.stack)-1])
						print "Remaining stack:", (self.stack)
					
			elif elt == "sqrt":
				if len(self.stack) < 1:
					self.message = "Error: sqrt: not enough items in stack!"
				else:
					a = self.stack.pop()
					if(a < 0):
						self.message = "Error: sqrt: input is negative!"
						break
					self.stack.append(math.sqrt(a))
					self.message = ""
					if self.verbose == True:
						print ("Result of RPN sqrt: %s" % self.stack[len(self.stack)-1])
						print "Remaining stack:", (self.stack)

			elif elt == "sin":
				if len(self.stack) < 1:
					self.message = "Error: sin: not enough items in stack!"
				else:
					a = self.stack.pop()
					self.stack.append(math.sin(a))
					self.message = ""
					if self.verbose == True:
						print ("Result of RPN sin: %s" % self.stack[len(self.stack)-1])
						print "Remaining stack:", (self.stack)

			elif elt == "cos":
				if len(self.stack) < 1:
					self.message = "Error: cos: not enough items in stack!"
				else:
					a = self.stack.pop()
					self.stack.append(math.cos(a))
					self.message = ""
					if self.verbose == True:
						print ("Result of RPN cos: %s" % self.stack[len(self.stack)-1])
						print "Remaining stack:", (self.stack)
					
		# don't do anything for other inputs
		#if(len(self.stack) < 1):
		#	self.message = ("The stack is empty.")
		#else:
		#	self.message = ("Result: %s" % intrep(self.stack[len(self.stack)-1]))

