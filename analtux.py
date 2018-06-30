#!/usr/bin/env python3

# Copyright (c) 2018 BSDForen.de
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS ``AS IS'' AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
# SUCH DAMAGE.

# ----

import argparse
import configparser
import logging
import logging.handlers
import os
import random
import signal
import sys
import time

import irc.bot
import pymysql

# ----

class Analtux(irc.bot.SingleServerIRCBot):
    def __init__(self, mysql, server, port, chans, nick, passwd):
        """
        Constructs a new IRC bot object.
        
        @param mysql: MySQL connections
        @param server: IRC server
        @param port: The IRC servers ports
        @param chans: List of channels to join
        @param nick: The bots nick
        @param passwd: The password used to auth at services
        """
        self.chans = chans.split(',')
        self.nick = nick
        self.passwd = passwd

        logger.info("Connecting to IRC server at " + server)

        irc.bot.SingleServerIRCBot.__init__(self, [(server, int(port))], nick, nick)


    def on_kick(self, con, val):
        """
        We were kicked.

        @param con: Connection
        @param val: Reason
        """
        chan = val.target
        reason = val.arguments[0].strip()

        logger.info("Kicked from {}, reason: {} Rejoining...".format(chan, reason))

        con.join(chan)


    def on_nicknameinuse(self, con, val):
        """
        Our nick is already in use.

        @param con: Connection
        @param val: Error string
        """
        logger.info("Nick {} is already in use. Ghosting...".format(self.nick))

        con.nick("{}{}".format(self.nick, random.randint(100, 999)))
        con.privmsg("nickserv", "ghost {} {}".format(self.nick, self.passwd))

        logger.info("Chaning nick to " + self.nick)

        con.nick(self.nick)

        logger.info("Authenticating to services")

        con.privmsg("nickserv", "identify {}".format(self.passwd))


    def on_welcome(self, con, val):
        """
        After the irc send it's welcome string
        
        @param con: Connection object
        @param val: Welcome string
        """
        logger.info("The server welcome string is: " + val.arguments[0].strip())
        logger.info("Authenticating to services")

        con.privmsg("nickserv", "identify {}".format(self.passwd))

        for chan in self.chans:
            logger.info("Joining " + chan)

            con.join(chan)


    def on_pubmsg(self, con, val):
        """
        We received a public message

        @param con: Connect object
        @param val: Message
        """
        chan = val.target
        msg = val.arguments[0].strip().split(' ', 1)
        action = msg[0].lower()
        user = val.source.split('!', 1)[0]

        if action == "!info":
            if len(msg) == 1:
                # The user send us just '!info', so we're
                # answering with a random info string.
                logger.info(user + " requested a random info string")

                con.privmsg(chan, mysql.getrandominfo())
            elif len(msg) == 2:
                # The user send us '!info key', so we're
                # answering with a info strings for 'key'.
                key = msg[1].strip()

                logger.info(user + " requested all info strings for " + key)

                for info in mysql.getinfo(key):
                    con.privmsg(chan, info)
                    time.sleep(0.25)
        elif action == "!learn":
            # Check for syntax correctness
            error = False

            if len(msg) != 2:
                error = True
            else:
                learn = msg[1].split('=', 1)
                
                if len(learn) != 2:
                    error = True
                else:
                    key = learn[0].strip()
                    text = learn[1].strip()

                    if len(key) == 0:
                        error = True
                    elif len(text) == 0:
                        error = True

            # Mkay, now the magic
            if error:
                con.privmsg(chan, 'try: "!learn foo = bar"')
            else:
                logger.info("{} wants to learn {} = {}".format(user, key, text))

                mysql.learn(chan, user, key, text)
                con.privmsg(chan, "Okay, learned {} = {}".format(key, text))
        elif action == "!forget":
            # Check for syntax correctness
            error = False
            fullinfo = False

            if len(msg) != 2:
                error = True
            else:
                # What kind of action was requested?
                if msg[1].find('=') == -1:
                    fullinfo = True
                    key = msg[1].strip()

                    if len(key) == 0:
                        error = True
                else:
                    forget = msg[1].split('=', 1)

                    if len(forget) != 2:
                        error = True
                    else:
                        key = forget[0].strip()
                        text = forget[1].strip()

                        if len(key) == 0:
                            error = True
                        elif len(text) == 0:
                            error = True

            # Mkay, now the magic
            if error:
                con.privmsg(chan, 'try: "!forget foo = bar" or "!forget foo"')
            else:
                if fullinfo:
                    logger.info("{} wants to forget everything we know {}".format(user, key))
                    mysql.forgetall(key)
                    con.privmsg(chan, "forgot everything i knew about " + key)
                else:
                    logger.info("{} wants to forget {} = {}".format(user, key, text))
                    mysql.forget(key, text)
                    con.privmsg(chan, "forgot {} = {}".format(key, text))


class MySQL:
    def __init__(self, server, port, user, passwd, db):
        """
        Constructs a new MySQL database connection. 

        @param server: Server to connect to
        @param port: The servers TCP port
        @param user: Database user
        @param passwd: Database password
        @param db: Database to use
        """
        logger.info("Connecting to MySQL database at " + server)

        self.con = pymysql.connect(host=server, port=int(port), user=user, passwd=passwd, db=db)

        logger.info("Connection successfull")


    def close(self):
        """ Closes the database connection. """
        if self.con is not None:
            logger.info("Closing connection to MySQL database")

            self.con.close()
            self.con = None


    def getinfo(self, key):
        """
        Returns all info strings for the given key.

        @param key: Key to retrive info strings for
        """
        self.con.ping(reconnect=True)
        cur = self.con.cursor()
        cur.execute("SELECT * FROM factoids WHERE factoid_key = '{}';".format(key))
        ret = cur.fetchall()
        cur.close()

        if ret is None or not ret:
            return ["Huh? No idea."]
        else:
            text = ret[0][1]
            first = True
            fulltext = []

            for line in ret:
                thistext = "{} [{} {}]".format(line[2], line[3],
                        time.strftime('%Y-%m-%d', line[5].timetuple()))

                if len(text) + len(thistext) >= 400:
                    # Maximum length, we'll need a new string
                    fulltext.append(text)
                    text = thistext
                else:
                    # Length is still okay
                    if first:
                        text = text + " = "
                        first = False
                    else:
                        text = text + " || "

                    text = text + thistext

            fulltext.append(text)
            return fulltext


    def getrandominfo(self):
        """ Returns a random info string. """
        self.con.ping(reconnect=True)
        cur = self.con.cursor()
        cur.execute('SELECT * FROM factoids ORDER BY RAND() LIMIT 1;')
        ret = cur.fetchone()
        cur.close()

        if ret is None:
            logger.info("Database returned None")

            return "Couldn't fetch info from database. Sorry."
        else:
            return "{} = {} [{} {}]".format(ret[1], ret[2], ret[3], 
                    time.strftime('%Y-%m-%d', ret[5].timetuple()))


    def forget(self, key, text):
        """
        Forgets one info string.

        @param key: Key were the info string is located
        @param text: Text to forget
        """
        self.con.ping(reconnect=True)
        cur = self.con.cursor()
        cur.execute("DELETE FROM factoids WHERE factoid_key = '{}' AND factoid_value = '{}';"
                .format(key, text))
        cur.close()
        self.con.commit()


    def forgetall(self, key):
        """
        Removes all info strings for 'key'.

        @param key: key to remove
        """
        self.con.ping(reconnect=True)
        cur = self.con.cursor()
        cur.execute("DELETE FROM factoids WHERE factoid_key = '{}';".format(key))
        cur.close()
        self.con.commit()


    def learn(self, chan, user, key, text):
        """
        Adds a new info to the database.

        @param chan: Channel were the learing was requested
        @param user: User that requested the learn
        @param key: Key to learn
        @param text: Text to learn
        """
        self.con.ping(reconnect=True)
        cur = self.con.cursor()
        cur.execute("INSERT INTO factoids (factoid_key, factoid_value, factoid_author, factoid_channel, " +
                "factoid_timestamp, factoid_locked) VALUES  ('{}', '{}', '{}', '{}', NOW(), '0');"
                .format(key, text, user, chan))
        cur.close()
        self.con.commit()


# ----

def error(msg):
    """
    Prints an error message and exists.

    @param msg: Message to print.
    """
    if logger is not None:
        logger.info("ERROR: " + msg)
    else:
        print("ERROR: " + msg, file=sys.stderr)

    if mysql is not None:
        mysql.close()

    if analtux is not None():
        analtux.die("I'll be back!")

    sys.exit(1)


def signalhandler(signal, frame):
    """ A simple signal handler. Quits the application. """
    logger.info("Received signal {}. Shutting down...".format(signal))

    if mysql is not None:
        mysql.close()

    if analtux is not None():
        analtux.die("I'll be back!")

    sys.exit(0)

# ----

def main():
    """
    A.N.A.L.T.U.X. (Artificial Networked Android Limited to Troubleshooting
    and Ultimate Xenocide) is a simple IRC bot, written for ##bsdforen.de on
    Freenode.
    """
    # Register signal handler
    signal.signal(signal.SIGINT, signalhandler)
    signal.signal(signal.SIGTERM, signalhandler)

    # ----

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="A.N.A.L.T.U.X. IRC Bot")
    parser.add_argument('-c', dest='cfg', type=str, required=True, help="Config file")
    parser.add_argument('-l', dest='log', type=str, required=True, help="Log directory")

    args = parser.parse_args()

    # ----

    # Create logger
    try:
        logfile = os.path.join(args.log, 'analtux.log')
        outfile = logging.handlers.TimedRotatingFileHandler(logfile, encoding='UTF-8', when='midnight', backupCount=8)
        outstdout = logging.StreamHandler(sys.stdout)

        logging.basicConfig(format='%(asctime)s: %(message)s', level=logging.INFO, handlers=[outfile, outstdout])

        global logger
        logger = logging.getLogger('analtux')
    except Exception as e:
        error("Couldn't create logger: " + str(e))

    # ----

    # Parse configuration
    logger.info("Parsing configuration file " + args.cfg)

    config = configparser.ConfigParser()

    try:
        with open(args.cfg, 'r') as cfg:
            config.read_file(cfg)
    except Exception as e:
        error("Couldn't read config file: " + str(e))

    # ----

    try:
        global mysql
        mysql = MySQL(config['mysql']['server'], config['mysql']['port'], config['mysql']['user'],
                config['mysql']['passwd'], config['mysql']['database']) 
    except Exception as e:
        error("Couldn't connect to MySQL database: " + str(e))

    # ----

    global analtux
    analtux = Analtux(mysql, config['irc']['server'], config['irc']['port'], config['irc']['chans'],
            config['irc']['nick'], config['irc']['passwd'])
    analtux.start()

# ----

if __name__ == "__main__":
    main()

# ----

# vim: tw=120
