# Dragobot is (c) 2012-2013 Joe Zeng.
# coding: UTF-8 #
# This code is released under the MIT license.

import sys
import socket
import time
import datetime
import select
import random
import os.path
import string

from threading import Timer

import math
from random import randint

import rpn
from rpn import RPN

# Basic bot info

irc = socket.socket ( socket.AF_INET, socket.SOCK_STREAM )
msgbuf = ""
PACKSIZE = 512

basenick = "Dragobot"
nickname = basenick

username = "dragobot"
realname = "Dragobot"
operatorname = "Dragonaire"

quitmsg = "Goodbye."

vfile = open("data/version", "r")
version = vfile.readline().strip()
str_bt = time.localtime(os.path.getmtime("dragobot.py"))
buildtime = "%d-%02d-%02d %d:%02d:%02d" % (str_bt[0], str_bt[1], str_bt[2], str_bt[3], str_bt[4], str_bt[5])

###############
# Function definitions
###############

def now():
	return datetime.datetime.now()

def timer():
	return time.time()

def logint(index): # logarithmic interpolation
	return math.log(1 + index) / math.log(2)

alphanumstring = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
alphastring = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
numstring = "0123456789"

################
# Class definitions et al.
################

class IRCMessage:
	def __init__(self):
		self.sender = ""
		self.senderhostname = ""
		self.msgtype = ""
		self.receiver = ""
		self.message = ""

		self.channel = ""
		self.reason = ""

def cleanmessage(line):
	output = ""
	for char in line:
		if ord(char) >= 32:
			output += char
	return output

def strippunc(line):
	output = ""
	for char in line:
		if char in alphanumstring or char == " ":
			output += char
	return output

def message(line):
	
	# message parser, converts a line into a message class

	msg = IRCMessage()

	# Every IRC message contains the following things:
		# sender ID (either nick!user@host or domain.name)
		# command

	# Split for these two things first.

	splitline = line.split(" ", 2)

	msg.sender = splitline[0][1:]

	if msg.sender.find("!") != -1:
		sendersplit = msg.sender.split("!", 1)
		msg.sender = sendersplit[0]
		msg.senderhostname = sendersplit[1]

	msg.msgtype = splitline[1]

	# Depending on the message type, parse the rest of the content.

	if msg.msgtype == "PRIVMSG":
		# Regular chat message
		content = splitline[2].split(" ", 1)
		msg.receiver = content[0]
		msg.message = content[1][1:]

		if msg.message[0] == "\x01" and msg.receiver.lower() == nickname.lower():
			ctcp = msg.message.strip("\x01").split(" ", 1)
			ctcptype = ctcp[0]
			if len(ctcp) > 1:
				ctcpcontent = ctcp[1]
				print "[%s] Received a CTCP %s from %s (%s):\n   %s" % (now(), ctcptype, msg.sender, msg.senderhostname, ctcpcontent)
			else:
				print "[%s] Received a CTCP %s from %s (%s)" % (now(), ctcptype, msg.sender, msg.senderhostname)
		
		elif msg.message[:7] == "\x01ACTION":
			# It's one of those /me messages.
			action = msg.message.strip("\x01").split(" ", 1)[1]
			print "[%s] %s (%s) performed an action:\n   %s %s" % (now(), msg.sender, msg.senderhostname, msg.sender, action)

		else:
			print "[%s] Received a message from %s (%s) to %s:\n   %s" % (now(), msg.sender, msg.senderhostname, msg.receiver, cleanmessage(msg.message))
	
	if msg.msgtype == "NOTICE":
		# Received a NOTICE.
		content = splitline[2].split(" ", 1)
		msg.receiver = content[0]
		msg.message = content[1][1:]
		print "[%s] Received a notice from %s (%s) to %s:\n   %s" % (now(), msg.sender, msg.senderhostname, msg.receiver, cleanmessage(msg.message))

	if msg.msgtype == "KICK":
		# Oh no, Dragobot has been kicked!
		content = splitline[2].split(" ", 2)
		msg.channel = content[0]
		msg.receiver = content[1]
		msg.reason = content[2][1:]
		print "[%s] %s (%s) has kicked %s from %s for the following reason: %s" % (now(), msg.sender, msg.senderhostname, msg.receiver, msg.channel, cleanmessage(msg.reason))

	if msg.msgtype.isdigit():
		content = splitline[2].split(" ", 1)
		msg.receiver = content[0]
		msg.message = content[1]
		# If the msgtype is 372, it's a motd; let those lines pass
		if msg.msgtype == "372":
			print cleanmessage(msg.message).strip(":-")
		else:
			print "[%s] Received a message with status code %s from %s (%s):\n   %s" % (now(), msg.msgtype, msg.sender, msg.senderhostname, cleanmessage(msg.message))

	return msg




##############
### Wrapper methods for IRC commands
##############

def send_message(receiver, message):
	irc.send("PRIVMSG " + receiver + " :" + message + "\r\n")

def send_notice(receiver, message):
	irc.send("NOTICE " + receiver + " :" + message + "\r\n")

def join_channel(channel):
	irc.send("JOIN #" + channel + "\r\n")

def perform_action(receiver, message):
	send_message(receiver, "\x01ACTION " + message + "\x01")

def list_users(channel):
	global msgbuf # I don't know why we need this, but we do.
	irc.send("NAMES #" + channel + "\r\n")

	userlist = []
	while True:
		msgbuf += irc.recv(PACKSIZE)
		while msgbuf.find("\r\n") != -1:
			msg = message(msgbuf.split("\r\n", 1)[0])
			msgbuf = msgbuf.split("\r\n", 1)[1]

			# now, process the message.
			if msg.msgtype == "353":
				# contains usernames.
				rawlist = msg.message.split(":")[1].rstrip()
				addlist = rawlist.split(" ")
				for a in range(len(addlist)):
					while addlist[a][0] in "+%@&~":
						addlist[a] = addlist[a][1:]
					userlist.append(addlist[a])
			if msg.msgtype == "366":
				userlist.remove(nickname)
				# We don't want Dragobot wrapping around himself, now do we.
				return userlist





#################
## Games that Dragobot can play
#################


# functions, et al.

def lettergrade(grade):
	if grade >= 100:
		return ["SSS", "Perfect!"]
	if grade >= 95:
		return ["SS", "Awesome!"]
	if grade >= 90:
		return ["S", "Excellent!"]
	if grade >= 80:
		return ["A", "Great job!"]
	if grade >= 70:
		return ["B", "Pretty good!"]
	if grade >= 55:
		return ["C", "Fairly decent."]
	if grade >= 40:
		return ["D", "Keep working at it."]
	if grade >= 20:
		return ["E", "Better luck next time."]
	if grade >= 0:
		return ["F", "Try a little harder next time."]
	if grade >= -25:
		return ["FF", "Try harder next time."]

	return ["FFF", "Try much harder next time."]

games = []



###############
# Game 1. Mastermind
###############

numberstring = "0123456789"

class MastermindGame:

	def __init__(self, player):
		self.player = player
		self.gametype = "mastermind"
		self.over = False

		self.number = ""
		self.score = 0
		self.turns = 0
		for i in range(4):
			self.number += numberstring[randint(0,9)]
		print ("New game of Mastermind started by " + player + " - number: " + self.number)
		send_message(player, "To play, type in a 4-digit number as a guess.")

	def sendInput(self, msg):
		if (msg.receiver == self.player and self.player[0] == "#" or msg.sender == self.player):

			inputs = msg.message
			if (len(inputs) != 4):
				# input is not correct length!
				return
			guess = []
			# interpret the input
			for a in range(4):
				if not ((inputs[a]) in numberstring):
					return
				else:
					guess += inputs[a]
			dispguess = "".join(guess)
			# We can take the input now
			self.turns += 1
			tempnumber = list(self.number)
			A = 0
			B = 0
			plus_score = 0
			# check for right numbers in the right position
			for a in range(4):
				if guess[a] == tempnumber[a]:
					A += 1
					plus_score += 100
					guess[a] = "X"
					tempnumber[a] = "X"
			# check for right numbers in the wrong position
			for a in range(4):
				for b in range(4):
					if guess[a] == tempnumber[b] and guess[a] != "X":
						B += 1
						plus_score += 50
						guess[a] = "X"
						tempnumber[b] = "X"
			if (A == 0 and B == 0):
				# plus_score = -400  # classic scoring
				plus_score = 0
			self.score += plus_score
			send_message(self.player, "%s. %s  %sA%sB  Score: %s (%s)" % (self.turns, dispguess, A, B, self.score, plus_score if plus_score <= 0 else "+"+str(plus_score)))
			# If we have 4A0B, it's a win
			if A == 4:
				bonus = (16 - self.turns) * 600 + 600
				self.score += bonus
				send_message(self.player, "You guessed it! | Bonus: %s | Final score: %s" % (bonus, self.score))
				self.over = True
				return
			if self.turns >= 16:
				# game over, too many turns
				send_message(self.player, "Game over! The answer was: %s" % (self.number))
				self.over = True


#################
# Game 2: Hangman / Wheel of Fortune
#################

# Scrabble letter score table
letterscoretable = [5, 30, 30, 20, 5, 40, 20, 40, 5, 80, 50, 10, 30, 10, 5, 30, 100, 10, 10, 10, 5, 40, 40, 80, 40, 100]
wordlist = []

# 5 for vowels, 10 * value in scrabble for consonants

def uniqueletters(word):
	usedletters = []
	output = 0
	for letter in word:
		if not(letter.upper() in usedletters):
			output += 1
			usedletters.append(letter.upper())
	return output



def hangmangrade(time, theword, hintmask, wrongs, maxwrongs, solved):
	grade = 100

	ung_let = 0
	letters = 0

	for a in range(len(theword)):
		if theword[a] in alphanumstring:
			letters += 1
		if hintmask[a] == "_" and theword[a] in alphanumstring:
			ung_let += 1
	
	if solved:
		grade += float(ung_let) / float(letters) * 50
	else:
		grade -= 20
		grade -= float(ung_let) / float(letters) * 20
	
	grade -= float(wrongs) / float(maxwrongs) * 70
	
	perftime = 60
	failtime = 300
	# perfect time = 60 seconds
	# -30% = 300 seconds
	grade -= logint( max(float(time - perftime), 0) / float(failtime - perftime) ) * 30

	print "Unguessed letters solved: %s/%s" % (ung_let, letters)
	print "Wrong guesses used: %s/%s" % (wrongs, maxwrongs)
	print "Time taken: %s seconds" % (time)
	print "Final grade: %s%%" % (grade)

	return min(grade, 100)



class HangmanGame:
	
	def __init__(self, player): 
		self.player = player
		self.gametype = "hangman"
		self.over = False
		
		self.theword = wordlist[randint(0, len(wordlist)-1)]
		while len(self.theword) < 4:
			self.theword = wordlist[randint(0, len(wordlist)-1)]

		self.score = 0
		self.guessedletters = []
		self.wrongguesses = 0
		self.maxwrongguesses = min(16, max(2, (21 - uniqueletters(self.theword))))

		self.guessmask = []
		for a in self.theword:
			if a in alphanumstring and not(a in numberstring):
				self.guessmask.append("_")
			elif a in numberstring:
				self.guessmask.append("#")
			else:
				self.guessmask.append(a)

		print ("New game of Hangman started by " + player + " - Word: " + self.theword)
		send_message(player, "Your word is: " + "".join(self.guessmask))

		# start the timer _after_ the message has been sent.
		self.starttime = timer()



	def guessLetter(self, letter):
		if not(letter in alphanumstring):
			send_message(self.player, "That's not a letter!")
			return
		if letter.upper() in self.guessedletters:
			send_message(self.player, "You already guessed that!")
			return

		self.guessedletters.append(letter.upper())
		correctletters = 0

		# Check each character to see if it is this letter
		for a in range(len(self.theword)):
			if self.theword[a].upper() == letter.upper():
				self.guessmask[a] = self.theword[a]
				correctletters += 1
		# If at least one of them match
		if correctletters > 0:
			if correctletters > 1:
				send_message(self.player, "There are %s %s's." % (correctletters, letter.upper()))
			else:
				send_message(self.player, "There is one %s." % letter.upper())
			send_message(self.player, "Your word is: " + "".join(self.guessmask))
			if "".join(self.guessmask).upper() == self.theword.upper():
				# you've guessed all the letters
				send_message(self.player, "You guessed all the letters! The answer was: %s" % (self.theword))
				
				finalgrade = hangmangrade(timer() - self.starttime, self.theword, self.guessmask, self.wrongguesses, self.maxwrongguesses, True)
				grade = lettergrade(finalgrade)  # the letter grade itself, and the flavour text
				send_message(self.player, "Your rank: %s - %s" % (grade[0], grade[1]))
				
				self.over = True

		else:
			self.wrongguesses += 1
			send_message(self.player, "No, no %s's. (Wrong guesses left: %s)" % (letter.upper(), (self.maxwrongguesses - self.wrongguesses)))
			if self.wrongguesses >= self.maxwrongguesses:
				send_message(self.player, "Game over! The answer was: %s" % (self.theword))

				finalgrade = hangmangrade(timer() - self.starttime, self.theword, self.guessmask, self.wrongguesses, self.maxwrongguesses, False)
				grade = lettergrade(finalgrade)  # the letter grade itself, and the flavour text
				send_message(self.player, "Your rank: %s - %s" % (grade[0], grade[1]))
				
				self.over = True


	def sendInput(self, msg):
		if (msg.receiver == self.player and self.player[0] == "#" or msg.sender == self.player):

			inputs = msg.message
			
			if len(inputs) == 1:
				guess = inputs[0]
				self.guessLetter(guess)

			if inputs[:8] == "!letter ":
				if len(inputs) < 9:
					send_message(self.player, "You didn't input a letter!")
					return
				if len(inputs) > 9:
					send_message(self.player, "Only one letter please!")
					return
				guess = inputs[8]
				self.guessLetter(guess)

			elif inputs[:7] == "!guess ":
				if len(inputs) < 8:
					send_message(self.player, "You didn't input a letter!")
					return
				if len(inputs) > 8:
					send_message(self.player, "Only one letter please!")
					return
				guess = inputs[7]
				self.guessLetter(guess)

			elif inputs[:2] == "! ":
				if inputs[2:].upper() == self.theword.upper():
					# the word has been guessed.
					send_message(self.player, "You got it. The answer was: %s" % (self.theword))
					
					finalgrade = hangmangrade(timer() - self.starttime, self.theword, self.guessmask, self.wrongguesses, self.maxwrongguesses, True)
					grade = lettergrade(finalgrade)  # the letter grade itself, and the flavour text
					send_message(self.player, "Your rank: %s - %s" % (grade[0], grade[1]))
					
					self.over = True
				else:
					send_message(self.player, "No, not quite.")
					self.wrongguesses += 1
					send_message(self.player, "Wrong guesses left: %s" % (self.maxwrongguesses - self.wrongguesses))
					if self.wrongguesses >= self.maxwrongguesses:
						send_message(self.player, "Game over! The answer was: %s" % (self.theword))
						
						finalgrade = hangmangrade(timer() - self.starttime, self.theword, self.guessmask, self.wrongguesses, self.maxwrongguesses, False)
						grade = lettergrade(finalgrade)  # the letter grade itself, and the flavour text
						send_message(self.player, "Your rank: %s - %s" % (grade[0], grade[1]))
						
						self.over = True
				
			elif inputs[:7] == "!solve ":
				if inputs[7:].upper() == self.theword.upper():
					# the word has been guessed.
					send_message(self.player, "You got it. The answer was: %s" % (self.theword))
					
					finalgrade = hangmangrade(timer() - self.starttime, self.theword, self.guessmask, self.wrongguesses, self.maxwrongguesses, True)
					grade = lettergrade(finalgrade)  # the letter grade itself, and the flavour text
					send_message(self.player, "Your rank: %s - %s" % (grade[0], grade[1]))
					
					self.over = True
				else:
					send_message(self.player, "No, not quite.")
					self.wrongguesses += 1
					send_message(self.player, "Wrong guesses left: %s" % (self.maxwrongguesses - self.wrongguesses))
					if self.wrongguesses >= self.maxwrongguesses:
						send_message(self.player, "Game over! The answer was: %s" % (self.theword))
						
						finalgrade = hangmangrade(timer() - self.starttime, self.theword, self.guessmask, self.wrongguesses, self.maxwrongguesses, False)
						grade = lettergrade(finalgrade)  # the letter grade itself, and the flavour text
						send_message(self.player, "Your rank: %s - %s" % (grade[0], grade[1]))
						
						self.over = True

			elif inputs == "!guessedletters" or inputs == "!guesses" or inputs == "!g":
				list.sort(self.guessedletters)
				outputstring = ""
				for a in self.guessedletters:
					outputstring += a + " "
				send_message(self.player, "You've guessed: " + outputstring + (" (%d wrong guesses left)" % (self.maxwrongguesses - self.wrongguesses)))


###############
# Game 3: Name That Pokémon.
##############@

pokemonlist = []
pokemonflavortexts = []
typelist = ["Normal", "Fighting", "Flying", "Poison", "Ground", "Rock", "Bug", "Ghost", "Steel", "Fire", "Water", "Grass", "Electric", "Psychic", "Ice", "Dragon", "Dark"]

repeats = []

class PokemonData:
	
	def __init__(self):
		self.ID = 0
		self.name = 0
		self.type1 = 0
		self.type2 = 0


def pokemongrade(time, hints):
	grade = 100

	perftime = 0
	failtime = 90

	# -50 at 1 minute, 30 seconds
	grade -= logint( max(float(time - perftime), 0) / float(failtime - perftime) ) * 50

	# -20 points per hint
	grade -= hints * 20

	print "Hints used: %s/3" % (hints)
	print "Time taken: %s seconds" % (time)
	print "Final grade: %s%%" % (grade)

	return grade
	
# Don't  the last (n) Pokémon.
REPEATLIMIT = 50

class NameThatPokemonGame:
	
	def __init__(self, player, rounds = 1):

		self.player = player
		self.gametype = "namethatpokemon"
		self.over = False

		self.thepokemon = ""
		self.theword = ""
		self.hintmask = ""
		self.totalhints = 0

		self.rounds = rounds
		if(rounds > 1):
			send_message(player, "Starting a game of Name That Pokémon with %d rounds." % (rounds))

		print ("New game of Name That Pokémon started by " + player + " - Word: " + self.theword)
		self.startGame(player)

	def startGame(self, player):

		global repeats

		# repeat avoidance code.
		pokemon = pokemonlist[randint(0, 648)]
		while pokemon in repeats:
			pokemon = pokemonlist[randint(0, 648)]
		repeats += [pokemon]
		if len(repeats) > REPEATLIMIT:
			repeats.pop(0)

		self.thepokemon = pokemon
		self.theword = pokemon.name
		self.hintmask = ["_"] * len(pokemon.name)
		self.totalhints = 0
		
		send_message(player, "This Pokémon's dex entry is: %s" % (pokemonflavortexts[pokemon.ID - 1 + 649 * randint(0, 1)]))
		# start the timer _after_ the message has been sent.
		self.starttime = timer()
		self.elapstimestart = self.starttime + 4

	def sendInput(self, msg):
		if (msg.receiver == self.player and self.player[0] == "#" or msg.sender == self.player):

			# strip punctuation and stuff
			if msg.message.translate(string.maketrans("",""), string.punctuation).lower() == self.theword.translate(string.maketrans("",""), string.punctuation).lower():
				# they got it
				finishtime = timer()
				finalgrade = pokemongrade(finishtime - self.elapstimestart, self.totalhints)
				
				send_message(self.player, "You got it, %s! The Pokémon's name was %s.%s" % (msg.sender, self.theword, ((" (%d rounds to go)" % (self.rounds - 1)) if (self.rounds > 1) else "")))
				grade = lettergrade(finalgrade)  # the letter grade itself, and the flavour text
				send_message(self.player, "Your rank: %s (%s) - %s" % (grade[0], "%.2f%%" % finalgrade, grade[1]))
				
				self.rounds -= 1
				if self.rounds <= 0:
					self.over = True
				else:
					self.startGame(self.player)

			elif msg.message.lower() == "!pokemonhint" or msg.message.lower() == "!ph":
				
				# Start the time from the moment a player uses a hint
				curtime = timer()
				if self.elapstimestart > curtime:
					self.elapstimestart = curtime

				self.totalhints += 1

				if self.totalhints == 1:
					type1 = typelist[self.thepokemon.type1]
					an = ""
					if type1[0].lower() in "aeiou":
						an = "n"
					type2 = ""
					if self.thepokemon.type2 != -1:
						type2 = "/" + typelist[self.thepokemon.type2]
					gen = 0
					if self.thepokemon.ID <= 151:
						gen = 1
					elif self.thepokemon.ID <= 251:
						gen = 2
					elif self.thepokemon.ID <= 386:
						gen = 3
					elif self.thepokemon.ID <= 493:
						gen = 4
					elif self.thepokemon.ID <= 649:
						gen = 5
					send_message(self.player, "This Pokémon is a%s %s%s-type Pokémon from Generation %s." % (an, type1, type2, gen))

				elif self.totalhints == 2:
					# reveal one letter
					char = randint(0, len(self.theword) - 1)
					while self.hintmask[char] != "_":
						char = randint(0, len(self.theword) - 1)
					self.hintmask[char] = self.theword[char]
					send_message(self.player, "This Pokémon's name: " + "".join(self.hintmask))

				elif self.totalhints == 3:
					# reveal half the letters in the name
					for a in range(len(self.theword) / 2):
						char = randint(0, len(self.theword) - 1)
						while self.hintmask[char] != "_":
							char = randint(0, len(self.theword) - 1)
						self.hintmask[char] = self.theword[char]
					send_message(self.player, "This Pokémon's name: " + "".join(self.hintmask))
				
				else:
					self.totalhints = 3
					send_message(self.player, "I can't give any more hints!")
					




#############
# Game 4: Deal or No Deal
#############

casevalues = [0.01, 1, 5, 10, 25, 50, 75, 100, 200, 300, 400, 500, 750, \
			  1000, 5000, 10000, 25000, 50000, 75000, 100000, 200000, 300000, 400000, 500000, 750000, 1000000]

midgame_biases = [-25, -20, -15, -12, -10, -8, -6, -5, -4, -3, -2, -1, 0, 0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25]
endgame_biases = [100, 50, 25, 15, 12, 10, 8, 6, 5, 4, 3, 2, 1, 0, -1, -2, -3, -4, -6, -10, -20, -30, -22, -12, 0, 15]

bias_jitter = 2.5

class DealOrNoDealGame:
	
	def __init__(self, player):
		self.player = player
		self.gametype = "dealornodeal"
		self.over = False

		self.cases = []
		for i in range(26):
			self.cases.append(i)
		random.shuffle(self.cases) # mix the case values around

		self.owncase = -1
		self.opencases = [False] * 26
		self.openvalues = [False] * 26

		self.choice = True
		self.dealing = False

		self.caseround = 1
		self.casestoopen = 6
		self.openedcases = 0
		self.deal = 0

		print ("New game of Deal Or No Deal started by " + player + ".")
		print ("Case values are:")
		for i in range(26):
			print ("%s. $%s" % (i + 1, casevalues[self.cases[i]]))
		send_message(self.player, "To start, choose a case for yourself.")

	def calc_deal_amt(self):

		# calculate the deal amount

		# How the Deal AI works:
		# Each case has an associated "bias". During each deal, the biases of all the unopened values are totalled.
		# The higher the bias, the higher the final deal will be.

		average = 0
		minval = 1000000
		maxval = 0

		totalmidbias = 0
		totalendbias = 0
	
		# Step 1. Calculate the average
		for a in range(26):
			if self.openvalues[a] == False:
				average += casevalues[a]
				totalmidbias += midgame_biases[a]
				totalendbias += endgame_biases[a]
				if casevalues[a] < minval:
					minval = casevalues[a]
				if casevalues[a] > maxval:
					maxval = casevalues[a]

		average /= (26 - self.openedcases)
		# weighted average of the midgame and endgame biases
		totalbias = (0.5 ** (9 - self.caseround)) * totalendbias + (1 - 0.5 ** (9 - self.caseround)) * totalmidbias 
		# add a bit of random jitter here. Plus or minus 2.5 to the bias.
		totalbias = totalbias - bias_jitter + random.random() * bias_jitter * 2

		# Step 2. Interpolation
			# Calculate the weighted average of the opened cases;
			# This approximates what the deal would be.
		firstdealamt = ((minval) * (26 - self.openedcases) + (average) * (self.openedcases)) / 26.0
		
		# Step 3. More interpolation
		seconddealamt = firstdealamt
		# It's not a smooth curve, but it's the best I can do. :/
		if totalbias < 0:
			interp_coeff = 1 / (1 + (-totalbias / 100.0))
			seconddealamt = (firstdealamt * interp_coeff) + (minval * (1 - interp_coeff))
		elif totalbias > 0:
			interp_coeff = 1 + (totalbias / 100.0) # This one is actually an exponent.
			seconddealamt = maxval - ((maxval - minval) * ((float(maxval - firstdealamt) / float(maxval - minval)) ** interp_coeff))

		finaldealamt = seconddealamt

		# Step 4: Aesthetic rounding
		# Can't have the banker offering $199,999, now, can we.
		roundeddealamt = 0
		if finaldealamt < 5:
			roundeddealamt = finaldealamt # Don't round values below $5.
		elif finaldealamt < 10:
			roundeddealamt = round(finaldealamt / 0.10) * 0.10
		elif finaldealamt < 100:
			roundeddealamt = round(finaldealamt)
		elif finaldealamt < 1000:
			roundeddealamt = round(finaldealamt / 10) * 10
		elif finaldealamt < 5000:
			roundeddealamt = round(finaldealamt / 50) * 50
		elif finaldealamt < 25000:
			roundeddealamt = round(finaldealamt / 100) * 100
		elif finaldealamt < 100000:
			roundeddealamt = round(finaldealamt / 500) * 500
		elif finaldealamt < 500000:
			roundeddealamt = round(finaldealamt / 1000) * 1000
		elif finaldealamt < 1000000:
			roundeddealamt = round(finaldealamt / 5000) * 5000

		return roundeddealamt

	def make_a_deal(self):
		self.dealing = True
		self.deal = self.calc_deal_amt()
		send_message(self.player, "The banker is willing to offer you $%.02f. !deal or !nodeal?" % self.deal)

	def print_remaining_cases(self):
		casesleft = ""
		for a in range(26):
			if self.opencases[a] == False and (self.caseround == 10 or a != self.owncase):
				casesleft += str(a + 1) + " "
		send_message(self.player, "Remaining cases: %s" % (casesleft))

	def print_remaining_values(self):
		valuesleft = ""
		for a in range(26):
			if self.openvalues[a] == False:
				valuesleft += "$" + str(casevalues[a]) + " "
		send_message(self.player, "Remaining values: %s" % (valuesleft))


	def sendInput(self, msg):
		if (msg.receiver == self.player and self.player[0] == "#" or msg.sender == self.player and self.player[0] != "#"):
			
			if self.choice == True: # choosing a case for yourself
				if msg.message[:6] == "!case ":
					if(msg.message[6:].isdigit()):
						casenum = int(msg.message[6:])
						if casenum > 26:
							send_message(self.player, "Please select a case number from 1 to 26.")
							return
						else:
							self.choice = False
							caseindex = casenum - 1
							self.owncase = caseindex
							print "Case %s selected, containing $%s." % (casenum, casevalues[self.cases[caseindex]])
							send_message(self.player, "Now, open 6 cases.")
							return

			if self.caseround == 10: # final round, stay or switch
				if msg.message[:6] == "!case ":
					othercase = -1
					for a in range(26):
						if self.opencases[a] == False and a != self.owncase:
							othercase = a
					if(msg.message[6:].isdigit()):
						casenum = int(msg.message[6:])
						caseindex = casenum - 1
						if caseindex == self.owncase:
							send_message(self.player, "You decided to keep your case. It contains $%s!" % (casevalues[self.cases[self.owncase]]))
							send_message(self.player, "The other case contained $%s." % (casevalues[self.cases[othercase]]))
							if casevalues[self.cases[self.owncase]] == 1000000:
								send_message(self.player, "Good job! Your case contained the $1,000,000.")
							self.over = True
							return
						elif caseindex == othercase:
							send_message(self.player, "You decided to switch cases. It contains $%s!" % (casevalues[self.cases[othercase]]))
							send_message(self.player, "Your original case contained $%s." % (casevalues[self.cases[self.owncase]]))
							if casevalues[self.cases[othercase]] == 1000000:
								send_message(self.player, "Good job! The other case contained the $1,000,000.")
							self.over = True
							return
						else:
							send_message(self.player, "Please select one of the two remaining cases.")
							return
				elif msg.message == "!casesleft":
					self.print_remaining_cases()
				elif msg.message == "!valuesleft":
					self.print_remaining_values()

			elif self.dealing == False: # still opening cases
				if msg.message[:6] == "!case ":
					if(msg.message[6:].isdigit()):
						casenum = int(msg.message[6:])
						if casenum > 26:
							send_message(self.player, "Please select a case number from 1 to 26.")
							return
						else:
							caseindex = casenum - 1
							if self.opencases[caseindex] == True:
								send_message(self.player, "You already opened that case!")
								return
							if caseindex == self.owncase:
								send_message(self.player, "You can't open your own case just yet!")
								return
							else:
								# open the case
								self.opencases[caseindex] = True
								self.openvalues[self.cases[caseindex]] = True
								self.casestoopen -= 1
								self.openedcases += 1
								send_message(self.player, "You open case %s, and it contains $%s! (%s case%s left to open)" % (casenum, casevalues[self.cases[caseindex]], self.casestoopen, "" if self.casestoopen == 1 else "s"))
								if self.casestoopen == 0:
									# deal time!
									self.make_a_deal()
				elif msg.message == "!casesleft":
					self.print_remaining_cases()
				elif msg.message == "!valuesleft":
					self.print_remaining_values()


			elif self.dealing == True: # deal or no deal?
				if msg.message == "!nodeal":
					self.dealing = False
					self.caseround += 1
					if self.caseround == 10: # final round
						othercase = -1
						for a in range(26):
							if self.opencases[a] == False and a != self.owncase:
								othercase = a
						send_message(self.player, "You're down to two cases now - your own case, case %s, and the last remaining case, case %s." % (self.owncase + 1, othercase + 1))
						send_message(self.player, "You can now open either one of them and take the prize in it.")
					else:
						self.casestoopen = max(7 - self.caseround, 1)
						send_message(self.player, "Good! Let's keep playing. Open %s case%s." % (self.casestoopen, "" if self.casestoopen == 1 else "s"))

				if msg.message == "!deal":
					send_message(self.player, "You made a deal with the banker for $%.02f! Your case contained $%s." % (self.deal, casevalues[self.cases[self.owncase]]))
					self.over = True
				elif msg.message == "!casesleft":
					self.print_remaining_cases()
				elif msg.message == "!valuesleft":
					self.print_remaining_values()
			
			
###############
# Game 5: Trivia
###############

trivia_maxhints = 3

trivia_hinterval = 15
trivia_timeup = 60

trivialist = []

def triviagrade(time, hints, answer):

	time = time + hints * trivia_hinterval;

	grade = 100 * (trivia_timeup - time) / trivia_timeup

	print "Hints used: %d/%d" % (hints, trivia_maxhints)
	print "Time taken: %d seconds" % (time)
	print "Final grade: %f%%" % (grade)

	return grade

def trivia_lettergrade(grade):
	if grade >= 90:
		return ["SS", "Awesome!"]
	if grade >= 80:
		return ["S", "Excellent!"]
	if grade >= 70:
		return ["A", "Great job!"]
	if grade >= 60:
		return ["B", "Pretty good!"]
	if grade >= 45:
		return ["C", "Fairly decent."]
	if grade >= 30:
		return ["D", "Keep working at it."]
	if grade >= 15:
		return ["E", "Better luck next time."]
	if grade >= 0:
		return ["F", "Try a little harder next time."]
	return ["FF", "Try harder next time."]

def usclen(string): # returns how many underscores there are.
	length = 0
	for char in string:
		if char == "_":
			length += 1
	return length

class TriviaQuestion:

	def __init__(self, question, answerstring):
		self.question = question
		self.answers = [answer.lower() for answer in answerstring.split("|")]

class TriviaGame:

	def __init__(self, player, rounds = 1):
		
		self.player = player
		self.gametype = "trivia"
		self.over = False
		
		self.rounds = rounds
		self.playedrounds = 0
		self.roundstarttime = timer()

		self.hintmask = []
		self.hintmasklength = 0
		self.hintanswer = ""
		self.hintsused = 0
		self.hinttimer = None
		self.timesuptimer = None

		self.startGame()
		print ("New game of trivia started by " + self.player + ".")
	
	def startGame(self):
		
		global trivialist
		self.playedrounds += 1
		self.hintsused = 0
		self.roundstarttime = timer()
		
		self.question = random.choice(trivialist)
		self.hintanswer = self.question.answers[0] # always use the first answer as the answer for giving hints
		self.hintmask = []
		for a in self.hintanswer:
			if a in alphanumstring:
				self.hintmask.append("_")
			else:
				self.hintmask.append(a)
		self.hintmasklength = usclen(self.hintmask)
		
		send_message(self.player, "Q. %d of %d: %s" % (self.playedrounds, self.rounds, self.question.question))

		if self.hinttimer:
			self.hinttimer.cancel()
		self.hinttimer = Timer(trivia_hinterval, self.giveHint, ())
		self.hinttimer.start()
		self.timesuptimer = Timer(trivia_timeup, self.timeUp, ())
		self.timesuptimer.start()
	
	def sendInput(self, msg):

		if msg.message.lower() in self.question.answers:

			# they got it
			finishtime = timer()
			finalgrade = triviagrade(finishtime - self.roundstarttime, self.hintsused, msg.message)

			send_message(self.player, "Correct, %s! Your rank: %s (%.2f%%)" % (msg.sender, trivia_lettergrade(finalgrade)[0], finalgrade))
			self.stop_timers()
			if self.playedrounds < self.rounds:
				self.startGame()
			else:
				self.over = True

		if msg.message == "!hint" or msg.message == "!h":
			self.giveHint("user")
			
		if msg.message == "!giveup" or msg.message == "!gu":
			send_message(self.player, "Oh, too bad! The answer was: %s   Your rank: FF (0.00%%)" % (self.question.answers[0]))
			self.stop_timers()
			if self.playedrounds < self.rounds:
				self.startGame()
			else:
				self.over = True
	
	def timeUp(self):
		send_message(self.player, "Time's up! The answer was: %s   Your rank: FF (0.00%%)" % (self.question.answers[0]))
		self.stop_timers()
		if self.playedrounds < self.rounds:
			self.startGame()
		else:
			self.over = True

	def giveHint(self, arg=""):
		global trivia_maxhints
		if arg == "user" and self.hintsused >= trivia_maxhints:
			send_message(self.player, "I can't give any more hints! Type !giveup to give up.")
		elif self.hintsused >= trivia_maxhints:
			return # Don't return the "I can't give any more hints" message on automated hints.
		else:
			# send a hint
			self.hintsused += 1

			self.hinttimer.cancel()
			self.hinttimer = Timer(trivia_hinterval, self.giveHint, ())
			self.hinttimer.start()
			
			# time since last hint counts as the "start time"
			self.roundstarttime = timer()
			
			self.timesuptimer.cancel()
			self.timesuptimer = Timer(trivia_timeup - trivia_hinterval * self.hintsused, self.timeUp, ())
			self.timesuptimer.start()

			if(self.hintsused > 1):
				for a in range((self.hintmasklength * (self.hintsused - 1) / trivia_maxhints) - (self.hintmasklength * (self.hintsused - 2) / trivia_maxhints)):
					char = randint(0, len(self.hintmask) - 1)
					while self.hintmask[char] != "_":
						char = randint(0, len(self.hintanswer) - 1)
					self.hintmask[char] = self.hintanswer[char]
			send_message(self.player, "Here's a hint: " + "".join(self.hintmask))
	
	def stop_timers(self):
		# cancel all the remaining hint timers
		self.hinttimer.cancel()
		self.timesuptimer.cancel()



#################
# Game 6: Higher or Lower
#################

cardvalues = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King", "ace"]

class HigherOrLowerGame:

	def __init__(self, player):
		self.player = player
		self.gametype = "higherorlower"
		self.over = False
		
		self.deck = []
		for i in range(52):
			self.deck.append(i / 4)
		random.shuffle(self.deck)
		self.curcard = 0
		print ("New game of Higher or Lower started by " + player + ".")
		print "Cards: ",
		for i in range(52):
			print self.deck[i],
		print
		send_message(self.player, "Your first card is a%s %s. !higher or !lower?" % ("n" if self.deck[0] == 12 or self.deck[0] == 6 else "", cardvalues[self.deck[0]]))


	def sendInput(self, msg):
		if (msg.receiver == self.player and self.player[0] == "#" or msg.sender == self.player):
			
			if msg.message == "!higher" or msg.message == "!h":
				while True:   # stupid lack of gotos in Python.
					self.curcard += 1
					send_message(self.player, "Your next card is a%s %s." % ("n" if self.deck[self.curcard] == 12 or self.deck[self.curcard] == 6 else "", cardvalues[self.deck[self.curcard]]))
					if self.deck[self.curcard] < self.deck[self.curcard - 1]:
						send_message(self.player, "Oh, sorry, it was lower! You successfully guessed %s cards." % self.curcard)
						self.over = True
						return
					elif self.deck[self.curcard] == self.deck[self.curcard - 1]:
						send_message(self.player, "It was the same value! We'll flip the next one over.")
						continue
					elif self.curcard == 51:
						send_message(self.player, "You went through the entire deck! That's incredible!")
						send_message(self.player, "You've actually _won_ the game.")
						self.over = True
						return
					else:
						break

			elif msg.message == "!lower" or msg.message == "!l":
				while True:   # stupid lack of gotos in Python.
					self.curcard += 1
					send_message(self.player, "Your next card is a%s %s." % ("n" if self.deck[self.curcard] == 12 else "", cardvalues[self.deck[self.curcard]]))
					if self.deck[self.curcard] > self.deck[self.curcard - 1]:
						send_message(self.player, "Oh, sorry, it was higher! You successfully guessed %s cards." % self.curcard)
						self.over = True
						return
					elif self.deck[self.curcard] == self.deck[self.curcard - 1]:
						send_message(self.player, "It was the same value! We'll flip the next one over.")
						continue
					elif self.curcard == 51:
						send_message(self.player, "You went through the entire deck! That's incredible!")
						send_message(self.player, "You've actually _won_ the game.")
						self.over = True
						return
					else:
						break


#################
# Game 7: 24
#################

class TwentyFourGame():
	
	def __init__(self, player):
		self.player = player
		self.gametype = "24"
		self.over = False
		
		self.deck = []
		for i in range(40):
			self.deck.append(i / 4 + 1)
		random.shuffle(self.deck)
		self.curcard = 0
		print ("New game of 24 started by " + player + ".")
		print "Cards: ",
		for i in range(40):
			print self.deck[i],
		print
		send_message(self.player, "Your numbers are: %d %d %d %d" % (self.deck[0], self.deck[1], self.deck[2], self.deck[3]))
		# Eventually have a guessing thing, but for now, just declare the game to be over as soon as it starts.
		self.over = True

	def sendInput(self, msg):
		return


#################
# Game 7.5: 163
#################

class OneSixtyThreeGame():
	
	def __init__(self, player):
		self.player = player
		self.gametype = "163"
		self.over = False
		
		self.deck = []
		for i in range(52):
			self.deck.append(i / 4 + 1)
		random.shuffle(self.deck)
		self.curcard = 0
		print ("New game of 163 started by " + player + ".")
		print "Cards: ",
		for i in range(52):
			print self.deck[i],
		print
		send_message(self.player, "Your numbers are: %d %d %d %d %d %d" % (self.deck[0], self.deck[1], self.deck[2], self.deck[3], self.deck[4], self.deck[5]))
		# Eventually have a guessing thing, but for now, just declare the game to be over as soon as it starts.
		self.over = True

	def sendInput(self, msg):
		return

###################################################
# Game 8: Apples to Apples / Cards Against Humanity
###################################################

red_cards = []
green_cards = []

white_cards = []
black_cards = []


class ApplesToApplesGame():
	
	def __init__(self, player, mode):
		global green_cards
		global red_cards

		self.player = player
		self.gametype = "apples"
		self.over = False
		
		print ("New game of Apples to Apples started by " + player + ".")
		
		if(mode == "apples"):
			self.categorycard = random.choice(green_cards)
			self.choicecards = random.sample(red_cards, 7)
		elif(mode == "cah"):
			self.categorycard = random.choice(black_cards)
			self.choicecards = random.sample(white_cards, 7)

		send_message(self.player, "The category is: %s" % self.categorycard)

		self.choicestring = "  ".join(self.choicecards)
		send_message(self.player, "The choices are: %s" % self.choicestring)

		self.over = True

	def sendInput(self, msg):
		return


		
		
		
######################
### RPN calculator
######################
		
_rpn = RPN()
		
		
		
##########################
### Memes, chat responses, et al.
##########################


def interp_action(action, performer, recipient):
	
	if ("slaps " + nickname) in action and "trout" in action:
		perform_action(recipient, "slaps %s with an even bigger trout" % (performer))
	if ("wraps around " + nickname) in action:
		perform_action(recipient, "kisses %s" % (performer))




def interp_chat(message):
	
	# determine whether to send ot a channel or to a private message first
	if message.receiver[0] == "#":
		recipient = message.receiver
	else:
		recipient = message.sender
	
	
	if "/quit I'm a total idiot" in message.message:
		send_message(recipient, "I'm a total idiot")
		
	
	rawmessage = strippunc(message.message).lower()



fuzzydegree = 5 # can only be 5 or 15

################
# CTCP commands
################

daytimewords = [" in the morning", "noon", " in the afternoon", " in the evening", " at night", "midnight"]
numberwords = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven"]
	# don't use twelve, just say "noon" or "midnight"

timewords = ["%s o'clock", "quarter past %s", "half past %s", "quarter to %s"]
fivewords = ["%s o'clock", "five past %s", "ten past %s", "quarter past %s", "twenty past %s", "twenty-five past %s", "half past %s", "twenty-five to %s", "twenty to %s", "quarter to %s", "ten to %s", "five to %s"]

approxwords = ["a bit before", "about", "a little after"]

def interp_ctcp(sender, message):

	# if the message is a CTCP ping
	if message == "PING":
		send_notice(sender, "\x01PING %d\x01\r\n" % ((timer() * 1000000) - 50000000000))
			# I have no idea why they want the time minus 50 billion.
			# I cannot figure this out for the love of me.

	# if the message is a CTCP version
	if message == "VERSION":
		send_notice(sender, "\x01VERSION Dragobot v.%s / Python 2.7.3\x01\r\n" % version)
	
	# CTCP TIME pranks.

	if message == "TIME":
		thetime = int((timer() * 1000000) * (16 ** 8) / 86400000000) % (16 ** 8)
		send_notice(sender, "The current time is %04x:%04x." % (thetime / 65536, thetime % 65536))
		send_notice(sender, "The time displayed is UTC time. If you would like an answer for my local time, please use CTCP LOCALTIME.")

	if message == "LOCALTIME":
		localtime = time.localtime()
		timetouse = localtime[3] * 3600 + localtime[4] * 60 + localtime[5]
		thetime = int((timetouse * 1000000) * (16 ** 8) / 86400000000) % (16 ** 8)
		send_notice(sender, "The current time is %04x:%04x." % (thetime / 65536, thetime % 65536))
		send_notice(sender, "If you would like a more human-readable answer, please use CTCP THETIME.")

	if message == "THETIME":
		thetime = time.localtime()

		hours = thetime[3]
		minutes = thetime[4] + float(thetime[5]) / 60.0
	
		if fuzzydegree == 15 and minutes > 37.5:
			hours = (hours + 1) % 24
		elif fuzzydegree == 5 and minutes > 32.5:
			hours = (hours + 1) % 24
		
		# Get the hour.
		if hours == 0: # twelve midnight
			daytime = daytimewords[5]
		elif hours < 4:
			daytime = daytimewords[0] # Can be 3 or 0 depending on cultural context.
		elif hours < 12:			  # In Chinese, for example, 1 AM is "1 at night".
			daytime = daytimewords[0]
		elif hours == 12: # twelve noon
			daytime = daytimewords[1]
		elif hours < 18:
			daytime = daytimewords[2]
		elif hours < 20:
			daytime = daytimewords[3]
		else:
			daytime = daytimewords[4]

		hours = hours % 12
		# Split the hour into 12 five-minute segments, each of them halfway between two clock numbers. 

		thehour = numberwords[hours]
		
		if fuzzydegree == 15:
			if hours == 0 and int(minutes + 7.5) % 60 / 15 == 0: # Don't use words for noon or midnight.
				thequarter = "%s"
			else:
				thequarter = timewords[(int(minutes + 7.5) % 60) / 15]
		elif fuzzydegree == 5:
			if hours == 0 and int(minutes + 2.5) % 60 / 5 == 0: # Don't use words for noon or midnight.
				thequarter = "%s"
			else:
				thequarter = fivewords[(int(minutes + 2.5) % 60) / 5]

		if fuzzydegree == 15:
			theadjustment = approxwords[(int(minutes + 7.5) % 15) / 5]
		elif fuzzydegree == 5:
			modminutes = int(minutes + 2.5) % 5 - 2
			if modminutes < -1:
				theadjustment = "a bit before"
			elif modminutes > 1:
				theadjustment = "a little after"
			else:
				theadjustment = "about"

		fuzzytime = "%s %s%s" % (theadjustment, thequarter % thehour, daytime)

		send_notice(sender, "It's %s where I am." % fuzzytime)
		send_notice(sender, "If you would like a more detailed answer, please use CTCP THEACTUALTIME. (Warning: May flood your client.)")
		
	if message == "THEACTUALTIME":

		# Spam lots of time data.

		epoch = timer()
		thetime = time.localtime(epoch)
		utctime = time.gmtime(epoch)
		thedatetime = datetime.datetime(*thetime[:6])

		months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
		weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
	
		# Date and time
		send_notice(sender, "The current time is %02d:%02d:%02d." % (thetime[3], thetime[4], thetime[5]))
		send_notice(sender, "The current date is %s, %s %s, %s." % (weekdays[thetime[6]], months[thetime[1] - 1], thetime[2], thetime[0]))

		# UTC time
		send_notice(sender, "The current UTC time is %02d:%02d:%02d." % (utctime[3], utctime[4], utctime[5]))

		# We need to add 1 hour to UTC because of BMT.
		send_notice(sender, "The current Swatch Internet time is @%03.02f." % (float(int(epoch * 1000) % 86400000 + 3600000) / 86400.0))

		# ISO dates 
		weekdate = thedatetime.isocalendar()
		send_notice(sender, "The current ISO 8601 week-numbering date is %d-W%02d-%d." % (weekdate[0], weekdate[1], weekdate[2]))
		send_notice(sender, "The current ISO 8601 ordinal date is %d-%d." % (thetime[0], thetime[7]))

		# Other dates
		send_notice(sender, "The current Julian Astronomical Date is %d." % (epoch / 86400.0 + 2440587.5))
		
		# Times!
		send_notice(sender, "The current Unix Epoch is %d." % (epoch))

		#octomatic = int((epoch * 1000000) * (8 ** 6) / 86400000000) % (8 ** 6)
		#send_notice(sender, "The current octomatic time is %02o.%02o.%02o." % (octomatic / 4096, (octomatic / 64) % 64, octomatic % 64))

		nextyear = datetime.datetime(thetime[0] + 1, 1, 1, thetime[8], 0, 0, 0, None)
		timetillnextyear = nextyear - thedatetime
		send_notice(sender, "There are %s until next year." % (timetillnextyear))
		
	if message == "HELP":
		# Do the same thing as !dragobot help
		helpfile = open("data/help/help.txt", "r")
		for line in helpfile:
			send_notice(sender, line)
	
	if message == "FINGER":
		send_notice(sender, "Dragobot has no fingers, silly!")
		
	if message == "USERINFO":
		send_notice(sender, "Dragobot is a bot in the shape of a Dragonair.")
	
	if message == "SOURCE":
		send_notice(sender, "SOURCE http://github.com/joezeng/dragobot/")
	
	if message == "CLIENTINFO":
		# List all possible CTCP commands.
		send_notice(sender, "CLIENTINFO FINGER HELP PING SOURCE TIME USERINFO VERSION")
	







################
# Commands for dragobot
################

# help message

def default_message(recipient):
	helpfile = open("data/help/dragobot.txt", "r")
	for line in helpfile:
		send_message(recipient, line)

def send_helpfile(openfile, recipient):
	helpfile = open(openfile, "r")
	for line in helpfile:
		send_message(recipient, line)

def parse_dragobot_command(message, sender, recipient):
	
	splitmsg1 = message.strip().split(" ", 1)
	command = splitmsg1[0]

	if command == "about":
		send_message(recipient, "Dragobot v.%s (last compiled: %s)" % (version, buildtime))
		send_message(recipient, "Dragobot, a Python IRC bot that plays games")
		send_message(recipient, "© 2012-2013 Joe Zeng, all rights reserved. http://joezeng.com/")

	elif command == "help":
		send_helpfile("data/help/help.txt", recipient)
	
	elif command == "gamehelp":
		if len(splitmsg1) == 1:
			helpfile = open("data/help/gamehelp.txt", "r")
			for line in helpfile:
				send_message(recipient, line)
		else:
		# help for games
			param = splitmsg1[1].strip("!")
			if param == "mastermind" or \
			param == "dealornodeal" or \
			param == "namethatpokemon" or \
			param == "hangman" or \
			param == "higherorlower":
				send_helpfile("data/help/gamehelp/%s.txt" % param, recipient)

	elif command == "commands":
		send_helpfile("data/help/commands.txt", recipient)
	
	elif command == "triggers":
		send_helpfile("data/help/triggers.txt", recipient)
		
	elif command == "triggerhelp":
		send_helpfile("data/help/triggerhelp.txt", recipient)

	elif command == "rpnhelp":
		send_helpfile("data/help/rpnhelp.txt", recipient)

	elif command == "rpnexample":
		send_helpfile("data/help/rpnexample.txt", recipient)

	elif command == "quit":
		if sender == operatorname:
			# quit completely
			irc.send ( "QUIT :" + quitmsg +"\r\n")
			sys.exit()
		else:
			send_message(recipient, "You can't make me leave!")
	
	else:
		default_message(recipient)


rpn163 = RPN()



###########################
# Message-processing code #
###########################

def interp_message(message):

	# determine whether to send to a channel or to a private message first
	if message.receiver[0] == "#":
		recipient = message.receiver
	else:
		recipient = message.sender

	# if the message is an action instead
	if message.message[:7] == "\x01ACTION":
		action = message.message[8:len(message.message)-1]
		interp_action(action, message.sender, recipient)
		return
	elif message.message[0] == "\x01":
		interp_ctcp(message.sender, message.message.strip("\x01"))

	command = message.message.split(" ", 1)

	# game trigger commands
	mastermind_triggers = ["!mastermind", "!mm"]
	if command[0] in mastermind_triggers:
		for game in games:
			if game.player == recipient and game.gametype == "mastermind":
				print (recipient + " already has a game in progress!")
				return
		games.append(MastermindGame(recipient))
		return

	hangman_triggers = ["!hangman", "!hm"]
	if command[0] in hangman_triggers:
		for game in games:
			if game.player == recipient and game.gametype == "hangman":
				print (recipient + " already has a game in progress!")
				return
		games.append(HangmanGame(recipient))
		return
	
	namethatpokemon_triggers = ["!namethatpokemon", "!ntp"]
	if command[0] in namethatpokemon_triggers:
		for game in games:
			if game.player == recipient and game.gametype == "namethatpokemon":
				if(len(command) > 1 and command[1] == "stop"):
					game.over = True
					send_message(recipient, "Game of Name That Pokémon stopped.")
				else:
					print (recipient + " already has a game in progress!")
				return
		if(len(command) > 1 and command[1].isdigit()):
			games.append(NameThatPokemonGame(recipient, int(command[1])))
		else:
			games.append(NameThatPokemonGame(recipient))
		return
	
	dealornodeal_triggers = ["!dealornodeal", "!dond"]
	if command[0] in dealornodeal_triggers:
		for game in games:
			if game.player == recipient and game.gametype == "dealornodeal":
				print (recipient + " already has a game in progress!")
				return
		games.append(DealOrNoDealGame(recipient))

	trivia_triggers = ["!trivia", "!tr"]
	if command[0] in trivia_triggers:
		for game in games:
			if game.player == recipient and game.gametype == "trivia":
				if(len(command) > 1 and command[1] == "stop"):
					game.over = True
					game.stop_timers()
					send_message(recipient, "Trivia has been stopped. Type !trivia to restart.")
				else:
					print (recipient + " already has a game in progress!")
				return
		if(len(command) > 1 and command[1].isdigit()):
			games.append(TriviaGame(recipient, int(command[1])))
		else:
			games.append(TriviaGame(recipient))
		return

	higherorlower_triggers = ["!higherorlower", "!hol"]
	if command[0] in higherorlower_triggers:
		for game in games:
			if game.player == recipient and game.gametype == "higherorlower":
				print (recipient + " already has a game in progress!")
				return
		games.append(HigherOrLowerGame(recipient))

	twentyfour_triggers = ["!twentyfour", "!24"]
	if command[0] in twentyfour_triggers:
		for game in games:
			if game.player == recipient and game.gametype == "24":
				print (recipient + " already has a game in progress!")
				return
		games.append(TwentyFourGame(recipient))
		
	onesixtythree_triggers = ["!onesixtythree", "!163"]
	if command[0] in onesixtythree_triggers:
		for game in games:
			if game.player == recipient and game.gametype == "163":
				print (recipient + " already has a game in progress!")
				return
		games.append(OneSixtyThreeGame(recipient))

	apples_triggers = ["!applestoapples", "!apples", "!ata"]
	if command[0] in apples_triggers:
		for game in games:
			if game.player == recipient and game.gametype == "apples":
				print (recipient + " already has a game in progress!")
				return
		games.append(ApplesToApplesGame(recipient, "apples"))

	# RPN tool
	if command[0] == "!rpn":
		if len(command) > 1:
			_rpn.rpncalc(command[1].split(" "))
			if(_rpn.message != ""):
				send_message(recipient, _rpn.message)
			else:
				send_message(recipient, "Result: " + _rpn.get_stacktop())
		else:
			_rpn.rpncalc([])
			if(_rpn.message != ""):
				send_message(recipient, _rpn.message)
			else:
				send_message(recipient, "Result: " + _rpn.get_stacktop())

	# the 163 solver uses RPN
	if command[0] == "!163solve":
		if len(command) > 1:
			rpn163.rpncalc(command[1].split(" "))
			if(rpn163.message != ""):
				send_message(recipient, rpn163.message)
			else:
				answer = rpn163.get_stacktop()
				send_message(recipient, "Result: " + answer)
				if(answer == "163"):
					send_message(recipient, "Congratulations, %s, you got it!" % message.sender)
				else:
					send_message(recipient, "Too bad, %s! Try again." % message.sender)
				rpn163.rpncalc("AC")
		else:
			send_message("Please type in an expression.")
		

	# generic help trigger
	if command[0] == "!help":
		send_message(recipient, "For help with Dragobot, type: !dragobot help")


	# dragobot command
	if command[0] == "!dragobot" or command[0] == "Dragobot!" or command[0] == "¡Dragobot!":
		if len(command) > 1 and command[0] == "!dragobot":
			parse_dragobot_command(command[1], message.sender, recipient)
			return
		else:
			default_message(recipient)
			return

	# random chat commands
	if command[0] == "!wrap":
		perform_action(recipient, "wraps around %s" % (message.sender))
		return
	elif command[0] == "?wrap":
		if(recipient[0] == "#"):
			userlist = list_users(recipient[1:])
			perform_action(recipient, "wraps around %s" % (random.choice(userlist)))
			return
		else:
			perform_action(recipient, "wraps around %s" % (recipient))
			return
	elif command[0] == "%wrap":
		if(recipient[0] == "#"):
			userlist = list_users(recipient[1:])
			if "Holt" in userlist:
				perform_action(recipient, "wraps around Holt")
		return

	interp_chat(message)
	for game in games:
		game.sendInput(message)







def interp(message):
	# call a different method depending on the message provided.
	if message.msgtype == "PRIVMSG":
		interp_message(message)





#####################
#####################
### MAIN RUN CODE ###
#####################
#####################

############
# Offline init procedures
############

# load the configuration
conffile = open("config/drago.conf", "r")
network = conffile.readline().strip()
port = int(conffile.readline().strip())
channels = conffile.readline().strip().split(" ")

# load the Hangman word list
print "Loading Hangman words...",
fin = open("data/csw.txt", "r")
for line in fin:
	wordlist.append(line.split(" ", 1)[0])
print str(len(wordlist)) + " words loaded."

# load the Pokemon stats list.
print "Loading Pokémon data...",
fin = open("data/pokemon.csv", "r")
for line in fin:
	data = line.split(",")
	pd = PokemonData()
	pd.ID = int(data[0])
	pd.name = data[1]
	pd.type1 = int(data[3])
	pd.type2 = int(data[4])
	pokemonlist.append(pd)
fin = open("data/pokemon_flavortexts.csv", "r")
for line in fin:
	data = line.split(",", 3)
	pokemonflavortexts.append(data[3])
print "done."

# load the trivia questions
print "Loading trivia questions...",
fin = open("data/trivia.txt", "r")
lines = fin.readlines()
for i in range(len(lines) / 2):
	q = TriviaQuestion(lines[i*2].strip(), lines[i*2+1].strip())
	trivialist.append(q)
print str(len(trivialist)) + " questions loaded."

# load the Apples To Apples cards
print "Loading Apples To Apples cards...",
fin = open("data/ata_green.txt", "r")
lines = fin.readlines()
for line in lines:
	green_cards.append(line.strip())
print str(len(green_cards)) + " green cards loaded.",
fin = open("data/ata_red.txt", "r")
lines = fin.readlines()
for line in lines:
	red_cards.append(line.strip())
print str(len(red_cards)) + " red cards loaded."

# load the Cards Against Humanity cards
print "Loading Cards Against Humanity cards...",
fin = open("data/cah_black.txt", "r")
lines = fin.readlines()
for line in lines:
	black_cards.append(line.strip())
print str(len(black_cards)) + " black cards loaded.",
fin = open("data/cah_white.txt", "r")
lines = fin.readlines()
for line in lines:
	white_cards.append(line.strip())
print str(len(white_cards)) + " white cards loaded."

############
# Network startup procedures
############

# network = "irc.systemnet.info"
# port = 6667

# channels = ["bottest", "bulbagarden", "pandemonium"]
#channels = ["bottest"]

# logon procedure

irc.connect ( ( network, port ) )

print "Connected to %s." % network

nicktries = 1 # number of tries to have a nickname

irc.send ( "NICK " + nickname + "\r\n" )
irc.send ( "USER " + username + " 8 * :" + realname + "\r\n" )

# At the logon, the following message exchange occurs:

# ping exchange (for UnrealIRCd)
# welcome message

while True:
	msgbuf += irc.recv(PACKSIZE)
	donefirstloop = False

	while True:
		if msgbuf.find("\r\n") == -1:
			break
		msgsplit = msgbuf.split("\r\n", 1)
		msg = msgsplit[0]
		msgbuf = msgsplit[1]

		# wait for the ping, then pong back
		if msg.find ( "PING" ) != -1:
			irc.send ( "PONG " + msg.split() [1] + "\r\n" )
				
		if msg[0] != ":":
			print cleanmessage(msg)
			continue

		procmsg = message(msg)
		# wait for the end of the /motd command
		if procmsg.msgtype == "376":
			donefirstloop = True
			break
		if procmsg.msgtype == "433":
			nicktries += 1
			nickname = "%s%s" % (basenick, nicktries)
			print ("Nickname already taken, trying %s..." % nickname)
			irc.send ( "NICK " + nickname + "\r\n" )

	if donefirstloop == True:
		break

irc.send ( "NICK " + nickname + "\r\n" )

irc.send ( "NICK " + nickname + "\r\n" )

# join all active channels
for channel in channels:
	join_channel(channel)

# send_message("#bottest", "Good morning, Dr. Chandra. This is HAL. I'm ready for my first lesson.\r\n")

# main loop of sending and processing messages

while True:
	msgbuf += irc.recv(PACKSIZE)
	while True:
		if msgbuf.find("\r\n") == -1:
			break
		else:
			msgsplit = msgbuf.split("\r\n", 1)
			msg = msgsplit[0]
			msgbuf = msgsplit[1]
			
		if msg[0] != ":":
			print cleanmessage(msg)
			# If the server is pinging us, ping back
			if msg.find ( "PING" ) != -1:
				print "Replied with a PONG."
				irc.send ( "PONG " + msg.split()[1] + "\r\n" )
				
		else:
			procmsg = message(msg)
			
			if procmsg.msgtype == "433":
				nicktries += 1
				nickname = "%s%s" % (basenick, nicktries)
				print ("Nickname already taken, trying %s..." % nickname)
				irc.send ( "NICK " + nickname + "\r\n" )
				
			interp(procmsg) # This is the line where all the fun happens.
			
	for game in games:
		if game.over:
			games.remove(game)
