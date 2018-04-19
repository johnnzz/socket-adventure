import socket


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
        self.rooms = { "0": { "name": "The Foyer",
                              "desc": "a grand foyer, all pink.",
                              "north": "3",
                              "south": False,
                              "east": "2",
                              "west": "1",
                              "things": [] },
                       "1": { "name": "The Kitchen",
                              "desc": "a large kitchen, dirty and gray.",
                              "north": False,
                              "south": False,
                              "east": "0",
                              "west": False,
                              "things": [] },
                       "2": { "name": "The Library",
                              "desc": "a musty library, with wooden floors.",
                              "north": False,
                              "south": False,
                              "east": False,
                              "west": "0",
                              "things": [] },
                       "3": { "name": "The Fountain",
                              "desc": "a grand fountain, broken and dry.",
                              "north": False,
                              "south": "0",
                              "east": False,
                              "west": False,
                              "things": [] },
                               }

    def connect(self):
        self.socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
            socket.IPPROTO_TCP)

        # hack to figure out my outgoing ip address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        self.myaddr = s.getsockname()[0]
        s.close()

        address = ('0.0.0.0', self.port)
        self.socket.bind(address)
        self.socket.listen(1)

        self.client_connection, address = self.socket.accept()

        print("server running at {} on {}".format(self.myaddr, self.port))

    def room_description(self, room_number):
        """
        For any room_number in 0, 1, 2, 3, return a string that "describes" that
        room.

        Ex: `self.room_number(1)` yields "Brown wallpaper covers the walls, bathing
        the room in warm light reflected from the half-drawn curtains."

        :param room_number: int
        :return: str
        """

        # TODO: YOUR CODE HERE

        return 'You are in {name}.  You see {desc}'.format(**self.rooms[str(room_number)])

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

        # TODO: YOUR CODE HERE

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

        # TODO: YOUR CODE HERE
        direction = argument[0]
        new_room = self.rooms[self.room][direction]

        if new_room:
            self.room = new_room
            self.output_buffer = self.room_description(self.room)
        else:
            self.output_buffer = "Ouch!  You run into a wall."

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

        # TODO: YOUR CODE HERE
        self.output_buffer = 'You say, "{}".'.format(argument)

    def quit(self, argument):
        """
        Quits the client from the server.
        
        Turns `self.done` to True and puts "Goodbye!" onto the output buffer.
        
        Ignore the argument.
        
        :param argument: str
        :return: None
        """

        # TODO: YOUR CODE HERE
        self.output_buffer = "I'm sorry, I can't do that Dave."

    def route(self):
        """
        Examines `self.input_buffer` to perform the correct action (move, quit, or
        say) on behalf of the client.
        
        For example, if the input buffer contains "say Is anybody here?" then `route`
        should invoke `self.say("Is anybody here?")`. If the input buffer contains
        "move north", then `route` should invoke `self.move("north")`.
        
        :return: None
        """
        command = self.input_buffer.split(" ")[0]
        arguments = self.input_buffer.split(" ")[1:]

        print("DEBUG", command, arguments)

        # TODO: YOUR CODE HERE
        try:
            { "quit": self.quit,
              "move": self.move,
              "say": self.say,
              "look": self.look,
              "debug": self.debug,
              "quit": self.quit,
            }.get(command)(arguments)
        except Exception as err:
            self.usage(err)

    def usage(self, extra=""):
        self.output_buffer = "doof! {}".format(extra)

    def look(self, argument):
        self.output_buffer = self.room_description(self.room)

    def debug(self, argument):
        print("DEBUG",self.room)

    def push_output(self):
        """
        Sends the contents of the output buffer to the client.
        
        This method should prepend "OK! " to the output before sending it.
        
        :return: None 
        """

        # TODO: YOUR CODE HERE
        self.client_connection.sendall(("OK! " + self.output_buffer).encode("utf-8"))

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

        self.client_connection.close()
        self.socket.close()
