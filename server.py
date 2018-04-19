import socket
try:
    from chatterbot import ChatBot
except Exception as err:
    print("To get full functionality, do a 'pip install chatterbot'")

class Server(object):
    """
    An adventure game socket server
    
    An instance's methods share the following variables:
    
    * self.socket: a "bound" server socket, as produced by socket.bind()
    * self.client_connection: a "connection" socket as produced by socket.accept()
    * self.input_buffer: a string that has been read from the connected client and
      has yet to be acted upon.
    * self.output_buffer: a string that should be sent to the connected client; for
      testing purposes this string should NOT end in a newline character. When
      writing to the output_buffer, DON'T concatenate: just overwrite.
    * self.room: one of 0, 1, 2, 3. This signifies which "room" the client is in,
      according to the following map:
      
                                     3                      N
                                     |                      ^
                                 1 - 0 - 2                  |
                                 
    When a client connects, they are greeted with a welcome message. And then they can
    move through the connected rooms. For example, on connection:
    
    OK! Welcome to Realms of Venture! This room has brown wall paper!  (S)
    move north                                                         (C)
    OK! This room has white wallpaper.                                 (S)
    say Hello? Is anyone here?                                         (C)
    OK! You say, "Hello? Is anyone here?"                              (S)
    move south                                                         (C)
    OK! This room has brown wall paper!                                (S)
    move west                                                          (C)
    OK! This room has a green floor!                                   (S)
    quit                                                               (C)
    OK! Goodbye!                                                       (S)
    
    Note that we've annotated server and client messages with *(S)* and *(C)*, but
    these won't actually appear in server/client communication. Also, you'll be
    free to develop any room descriptions you like: the only requirement is that
    each room have a unique description.
    """

    game_name = "Realms of Venture"

    def __init__(self, port=50000):
        self.input_buffer = ""
        self.output_buffer = ""
        self.done = False
        self.socket = None
        self.client_connection = None
        self.port = port
        self.room = "0"
        self.lit_candle = False
        self.dark_count = 4
        self.objects = { "candle": "2", "pebble": "3", "scroll": "4" }
        self.rooms = { "0": { "name": "Foyer",
                              "desc": "a grand foyer, all pink",
                              "north": "3",
                              "south": False,
                              "east": "2",
                              "west": "1",
                              "dark": False },
                       "1": { "name": "Kitchen",
                              "desc": "a large kitchen, dirty and gray",
                              "north": False,
                              "south": False,
                              "east": "0",
                              "west": False,
                              "dark": True },
                       "2": { "name": "Library",
                              "desc": "a musty library, with wooden floors",
                              "north": False,
                              "south": False,
                              "east": False,
                              "west": "0",
                              "dark": False },
                       "3": { "name": "Fountain",
                              "desc": "a grand fountain, broken and dry",
                              "north": False,
                              "south": "0",
                              "east": False,
                              "west": False,
                              "dark": False },
                       "4": { "name": "Cave",
                              "desc": "a dark cave with paintings on the walls",
                              "north": False,
                              "south": False,
                              "east": False,
                              "west": False,
                              "dark": True }
                               }

        # hack to figure out my outgoing ip address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        self.myaddr = s.getsockname()[0]
        s.close()

        try:
            self.chatbot = ChatBot(
                'Adventure Venture',
                trainer='chatterbot.trainers.ChatterBotCorpusTrainer'
            )

            # Train based on the english corpus
            self.chatbot.train("chatterbot.corpus.english")
        except Exception as err:
            # we've already complained, get over it
            pass

        # announce address/port
        print("Server IP address is {} on port {}".format(self.myaddr, self.port))


    def connect(self):
        """
        start accepting connections
        """
        self.socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
            socket.IPPROTO_TCP)
        self.socket.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR, 1)

        address = ('0.0.0.0', self.port)
        self.socket.bind(address)
        self.socket.listen(1)

        self.client_connection, address = self.socket.accept()

        print("Server: listening!")


    def room_description(self, room_number):
        """
        For any room_number in 0, 1, 2, 3, return a string that "describes" that
        room.

        Ex: `self.room_number(1)` yields "Brown wallpaper covers the walls, bathing
        the room in warm light reflected from the half-drawn curtains."

        :param room_number: int
        :return: str
        """

        # in case we decide to switch to descriptive room identifiers, let's 
        # consider room_number a string
        room_number = str(room_number)

        # report the room name
        room_info = '\n\nYou are in the {name}.'.format(**self.rooms[room_number])

        # is it dark?
        if self.rooms[room_number]["dark"]:
            room_info += '  It is dark'
            if self.lit_candle:
                room_info += ' but the candle lights the way.'
            else:
                room_info += '.'

        # add the room desc
        room_info += '  You see {desc}.'.format(**self.rooms[room_number])

        # add the objects that are present
        stuff = self.get_inv(room_number)
        if stuff:
            room_info += "\n\nThe following items are present: {}.".format(", ".join(stuff))

        # add directionals
        paths = []
        for i in ["north", "south", "east", "west"]:
            if self.rooms[self.room][i]:
                paths.append(i)
        if paths:
            # because it bugs me
            room_info += "\n\n"
            if len(paths) == 1:
                room_info += "A path lies to the {}.".format(", ".join(paths))
            else:
                room_info += "Paths lie to the {}.".format(", ".join(paths))
        else:
            room_info += "\n\nThere are no obvious exits."

        # cuz: whitespace!
        room_info += "\n"

        return room_info


    def greet(self):
        """
        Welcome a client to the game.
        
        Puts a welcome message and the description of the client's current room into
        the output buffer.
        
        :return: None 
        """
        self.output_buffer = "Welcome to {}! {}".format(
            self.game_name,
            self.room_description(self.room)
        )


    def get_input(self):
        """
        Retrieve input from the client_connection. Store at most 32 characters of
        this input into the input_buffer.
        
        This is a BLOCKING call. It should not return until there is some input from
        the client to receive.
         
        :return: None 
        """

        # get info 
        self.input_buffer = self.client_connection.recv(32).decode()


    def move(self, argument):
        """
        Moves the client from one room to another.
        
        Examines the argument, which should be one of:
        
        * "north"
        * "south"
        * "east"
        * "west"
        
        "Moves" the client into a new room by adjusting self.room to reflect the
        number of the room that the client has moved into.
        
        Puts the room description (see `self.room_description`) for the new room
        into "self.output_buffer".
        
        :param argument: str
        :return: None
        """

        # in which direction do they wish to move
        if argument:
            direction = argument[0]

            # what room is in that direction
            try:
                new_room = self.rooms[self.room][direction]
                # if there is no room in the desired direction, the path will be false
                if new_room:
                    self.room = new_room
                    self.output_buffer = self.room_description(self.room)
                else:
                    self.output_buffer = "\n\nOuch!  You ran into a wall!\n"
            except Exception as err:
                new_room = False
                self.output_buffer = "\n\nYou narrowly avoid stepping in a tar pit!\n"


    def teleport(self, argument):
        """
        magic!
        """
        if argument:
            where = argument[0]
            try:
                self.room = where
                self.room_description(self.room)
                self.output_buffer += "\n\nA cloud of smoke dissipates.\n"
            except KeyError:
                self.output_buffer = "\n\nPoof!  You teleport into a rock!\n"
                self.output_buffer += "Goodbye!\n"
                self.done = True
        else:
            self.output_buffer = "\n\nTricks are for rabbits!\n"


    def say(self, argument):
        """
        Lets the client speak by putting their utterance into the output buffer.
        
        For example:
        `self.say("Is there anybody here?")`
        would put
        `You say, "Is there anybody here?"`
        into the output buffer.
        
        :param argument: str
        :return: None
        """
        try:
            simon_sez = self.chatbot.get_response(self.input_buffer)
            self.output_buffer = "\n\n{}\n".format(simon_sez)
        except Exception as err:
            self.output_buffer = '\n\nYou say, "{}".  (wabba wabba, whee, wok!)\n'.format(" ".join(argument))


    def exit(self, argument):
        self.quit(argument)


    def quit(self, argument):
        """
        Quits the client from the server.
        
        Turns `self.done` to True and puts "Goodbye!" onto the output buffer.
        
        Ignore the argument.
        
        :param argument: str
        :return: None
        """

        self.done = True
        self.output_buffer = "\n\nIf you must!  (Goodbye!)\n"


    def route(self):
        """
        Examines `self.input_buffer` to perform the correct action (move, quit, or
        say) on behalf of the client.
        
        For example, if the input buffer contains "say Is anybody here?" then `route`
        should invoke `self.say("Is anybody here?")`. If the input buffer contains
        "move north", then `route` should invoke `self.move("north")`.
        
        :return: None
        """

        # break up the input into a command and argument(s)
        command = self.input_buffer.split(" ")[0]
        arguments = self.input_buffer.split(" ")[1:]

        # very meta
        try:
            { "quit": self.quit,
              "move": self.move,
              "teleport": self.teleport,
              "say": self.say,
              "look": self.look,
              "debug": self.debug,
              "quit": self.quit,
              "inventory": self.inventory,
              "light": self.light,
              "get": self.get,
              "drop": self.drop,
              "help": self.help,
              "go": self.go,
              "north": self.north,
              "south": self.south,
              "west": self.west,
              "east": self.east,
            }.get(command)(arguments)
        except TypeError:
            # bad command
            self.output_buffer = "\n\n{}!????  Adjust your Babblefish!\n".format(self.input_buffer)
        except Exception as err:
            # bad programmer
            self.output_buffer = "\n\nFrozzle, Frozzle, --{}--, when {}!\n".format(err,self.input_buffer)

        if not self.done:
            # if we are in a dark room without a lit candle, count down for grue
            if self.rooms[str(self.room)]["dark"] and not self.lit_candle:
                if self.dark_count <= 2:
                    self.output_buffer += "\nYou are likely to be eaten by a grue!\n"
                if self.dark_count <= 0:
                    self.output_buffer = "\n\nYou have been eaten by a grue!!!\n"
                    self.output_buffer += "Goodbye!\n"
                    self.done = True
                self.dark_count -= 1
            else:
                # reset the grue counter
                self.dark_count = 4

    def go(self, argument):
        self.move(argument)

    def north(self, argument):
        self.move(["north"])

    def south(self, argument):
        self.move(["south"])

    def east(self, argument):
        self.move(["east"])

    def west(self, argument):
        self.move(["west"])

    def get_inv(self, query):
        """
        utility function to return objects in a room per person
        """
        inv = []
        for object in self.objects:
            owner = self.objects[object]
            if owner == query:
                inv.append(object)
        return inv


    def inventory(self, argument):
        """
        display player inventory
        """
        inv = self.get_inv("player")
        if inv:
            self.output_buffer = "\n\nYour magic bag contains: {}\n".format(", ".join(inv))
            if "candle" in inv:
                if self.lit_candle:
                    self.output_buffer += "The candle throws a dim, flickering light on the walls.\n"
                else:
                    self.output_buffer += "The candle is unlit.\n"
        else:
            self.output_buffer = "\n\nYour magic bag is empty.  :-(\n"


    def light(self, argument):
        """
        light the candle
        """
        requested_object = argument[0]
        avail_objects = self.get_inv("player")
        if requested_object == "candle":
            self.lit_candle = True
            self.output_buffer = "\n\nThe candle flickers to life.\n"
        else:
            self.output_buffer = "\n\nYou can't light a {}, silly!\n".format(" ".join(argument))


    def get(self, argument):
        """
        get an object
        """
        requested_object = argument[0]
        avail_objects = self.get_inv(self.room)
        if requested_object in avail_objects:
            self.objects[requested_object]="player"
            self.output_buffer = "\n\nYou put the {} in your magic bag.\n".format(requested_object)
        else:
            self.output_buffer = "\n\nNice try, bozo!\n"


    def drop(self, argument):
        """
        drop an object
        """
        requested_object = argument[0]
        avail_objects = self.get_inv("player")
        if requested_object in avail_objects:
            self.objects[requested_object]=str(self.room)
            self.output_buffer = "\n\nYou drop the {} like a limp mackerel.\n".format(requested_object)
            if requested_object == "candle":
                self.lit_candle = False
                self.output_buffer += "The candle goes out.\n"
        else:
            self.output_buffer = "\n\nYou fail to conjure a {} from thin air.\n".format(requested_object)


    def look(self, argument):
        """
        see what's around
        """
        self.output_buffer = self.room_description(self.room)


    def help(self, argument):
        """
        take pitty(ish)
        """
        if not argument:
            self.output_buffer = "\n\nWhat's the magic word?!\n"
        else:
            if argument[0] == "please":
                self.output_buffer = "\n\nTry an action/subject pair, like 'move south', or just an action, like 'look'.\n"
            else:
                self.output_buffer = "\n\nI can't hear you!\n"


    def debug(self, argument):
        """
        see what's what
        """
        info = "\n"
        info += "\nDEBUG addr: {}".format(self.myaddr)
        info += "\nDEBUG port: {}".format(self.port)
        info += "\nDEBUG room: {}".format(self.room)
        info += "\nDEBUG done: {}".format(self.done)
        info += "\nDEBUG lit_candle: {}".format(self.lit_candle)
        info += "\nDEBUG dark_count: {}".format(self.dark_count)
        info += "\nDEBUG objects: {}".format(self.objects)
        info += "\nDEBUG rooms: {}\n".format(self.rooms)
        self.output_buffer = info


    def push_output(self):
        """
        Sends the contents of the output buffer to the client.
        
        This method should prepend "OK! " to the output before sending it.
        
        :return: None 
        """
        self.client_connection.sendall(("OK!  " + self.output_buffer).encode("utf-8"))


    def serve(self):
        self.connect()
        self.greet()
        self.push_output()

        while not self.done:
            self.input_buffer = ""
            self.output_buffer = ""
            self.get_input()
            self.route()
            self.push_output()

        print("Server: goodbye!")
        self.client_connection.close()
        self.socket.close()
