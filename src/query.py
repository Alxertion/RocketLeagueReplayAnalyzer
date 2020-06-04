import re

from src import constants
from src.query_parse_exception import QueryParseException


class Query:
    """
    Query format:
        IF CONDITION
        FOR TIME_WINDOW
        THEN INSTRUCTION
        EVERY DELAY SECONDS

    CONDITION can be:
        a python-style condition, which can use predefined values as well as numbers / booleans / operators etc.:
            - ball.x (the ball's position on the X axis);
            - ball.y (the ball's position on the Y axis);
            - player.1.x;
            - player.1.y;
            - player.2.x;
            - ...
            - player.6.x;
            - player.6.y;
            - midfield.x (the position at the middle of the field on the X axis: 0);

    TIME_WINDOW can be:
        LAST x SECONDS (where 'x' is a number)
        LAST x ENTRIES (where 'x' is a number)

    INSTRUCTION can be:
        PRINT("string")

    DELAY can be:
        a number (2, 10, 0.5, etc)

    Examples of well-defined queries:
        IF ball.x < midfield.x
        FOR LAST 20 SECONDS
        THEN PRINT("Left team too defensive")
        EVERY 0.5 SECONDS
    """

    QUERY_IF = "if"
    QUERY_FOR = "for"
    QUERY_LAST = "last"
    QUERY_THEN = "then"
    QUERY_EVERY = "every"
    TIME_WINDOW_ENTRIES = "entries"
    TIME_WINDOW_SECONDS = "seconds"
    INSTRUCTION_PRINT = "print"
    PARSED_OPERAND_VALUES = [
        "ball.x",
        "ball.y",
        "player.1.x",
        "player.1.y",
        "player.2.x",
        "player.2.y",
        "player.3.x",
        "player.3.y",
        "player.4.x",
        "player.4.y",
        "player.5.x",
        "player.5.y",
        "player.6.x",
        "player.6.y",
    ]
    STATIC_OPERAND_VALUES = {
        "midfield.x": 0,
    }
    PLACEHOLDER = "PLACEHOLDER"

    CONDITION_CORRECT = "Correct"
    CONDITION_INCORRECT = "Incorrect"
    CONDITION_INCOMPLETE = "Incomplete"
    CONDITION_ERROR = "Error"

    TUTORIAL_TEXT = "QUERY FORMAT:\n" \
                    "  IF condition\n" \
                    "  FOR LAST x time_window\n" \
                    "  THEN PRINT(\"message\")\n" \
                    "  EVERY delay SECONDS\n" \
                    "\n" \
                    "TERMINOLOGY:\n" \
                    "- condition: a python-like condition which can use predefined operands, as well as " \
                    "numbers / booleans / operators etc;\n" \
                    "- predefined operands:\n" \
                    "  - ball.x;\n" \
                    "  - ball.y;\n" \
                    "  - player.1/2/3/4/5/6.x;\n" \
                    "  - player.1/2/3/4/5/6.y;\n" \
                    "  - midfield.x (0);\n" \
                    "- x: number\n" \
                    "- time_window: 'SECONDS' or 'ENTRIES'\n" \
                    "- message: a string printed when the condition is true 'FOR the LAST x SECONDS/ENTRIES'\n" \
                    "- delay: the message will be printed AT MOST every 'delay' seconds\n" \
                    "\n" \
                    "You can start multiple queries at once; separate them by a blank line.\n"

    INITIAL_QUERIES = "IF ball.x < midfield.x\n" \
                      "FOR LAST 2 SECONDS\n" \
                      "THEN PRINT(\"Left team defending\")\n" \
                      "EVERY 1 SECONDS\n" \
                      "\n" \
                      "IF ball.x > midfield.x\n" \
                      "FOR LAST 2 SECONDS\n" \
                      "THEN PRINT(\"Right team defending\")\n" \
                      "EVERY 1 SECONDS\n" \
                      "\n" \
                      "IF player.3.x > midfield.x and player.5.x > midfield.x and player.6.x > midfield.x\n" \
                      "FOR LAST 1 SECONDS\n" \
                      "THEN PRINT(\"Entire orange team is offensive\")\n" \
                      "EVERY 0.5 SECONDS"

    def __init__(self, query_string):
        self.query_string = query_string

        # init the query parameters
        self.condition = ""
        self.time_window_value = -1
        self.time_window_type = ""
        self.print_string = ""
        self.delay = -1

        # init the query evaluation variables
        self.fit_entries = 0
        self.first_entry_time = 0
        self.last_entry_time = 0
        self.last_print_time = 0

        # parse the query parameters' actual values from the given string
        self.parse_query()
        self.validate_parameters()
        self.invert_coordinates_in_condition()

    def parse_query(self):
        # lowercase everything, we don't use any capital letters
        # also trim it, as we don't need any whitespace at the beginning or the end
        self.query_string = self.query_string.lower().strip()

        # check if it starts with "IF ", otherwise raise parsing error
        if not self.query_string.startswith(Query.QUERY_IF + " "):
            raise QueryParseException("IF clause missing from the query.")

        # remove the beginning "IF " string
        self.query_string = self.query_string[len(Query.QUERY_IF + " "):]

        # extract the condition
        # first we search for the FOR clause
        for_clause_index = self.query_string.find(" " + self.QUERY_FOR + " ")
        if for_clause_index == -1:
            for_clause_index = self.query_string.find("\n" + self.QUERY_FOR + " ")
            if for_clause_index == -1:
                raise QueryParseException("FOR clause missing from the query.")

        # extract the condition (spans until the FOR clause is reached)
        self.condition = self.query_string[:for_clause_index]

        # extract the time window in the FOR clause
        # first we search for the THEN clause
        then_clause_index = self.query_string.find(" " + self.QUERY_THEN + " ")
        if then_clause_index == -1:
            then_clause_index = self.query_string.find("\n" + self.QUERY_THEN + " ")
            if then_clause_index == -1:
                raise QueryParseException("THEN clause missing from the query.")

        # extract the time window (spans until the THEN clause is reached)
        time_window_string = self.query_string[for_clause_index + 1:then_clause_index]
        if not time_window_string.startswith(Query.QUERY_FOR + " " + Query.QUERY_LAST + " "):
            raise QueryParseException("FOR clause must start with 'FOR LAST '.")

        # remove the beginning "FOR LAST " string
        time_window_string = time_window_string[len(Query.QUERY_FOR + " " + Query.QUERY_LAST + " "):]

        # extract the time window type
        time_window_type_index = re.search("(" + Query.TIME_WINDOW_ENTRIES + "|" + Query.TIME_WINDOW_SECONDS + ")",
                                           time_window_string)
        if time_window_type_index is None:
            raise QueryParseException("Time window type missing from the FOR clause.")
        time_window_type_index = time_window_type_index.start()
        self.time_window_type = time_window_string[time_window_type_index:].strip()

        # extract the time window value
        self.time_window_value = time_window_string[:time_window_type_index].strip()

        # we find the "EVERY" clause beginning
        every_clause_index = self.query_string.find(" " + self.QUERY_EVERY + " ")
        if every_clause_index == -1:
            every_clause_index = self.query_string.find("\n" + self.QUERY_EVERY + " ")
            if every_clause_index == -1:
                raise QueryParseException("EVERY clause missing from the query.")

        # check if the print instruction is present
        then_clause_string = self.query_string[then_clause_index:every_clause_index]
        print_index = then_clause_string.find(" " + Query.INSTRUCTION_PRINT + "(")
        if print_index == -1:
            raise QueryParseException("Print instruction missing from the THEN clause.")

        # extract the string from the print instruction
        self.print_string = then_clause_string[len('THEN PRINT("') + 1:-2]

        # extract the 'EVERY' clause (spans until the end of the message)
        every_clause_string = self.query_string[every_clause_index + 1:]
        if not every_clause_string.startswith(Query.QUERY_EVERY + " "):
            raise QueryParseException("EVERY clause must start with 'EVERY '.")

        # remove the beginning "FOR LAST " string
        every_clause_string = every_clause_string[len(Query.QUERY_EVERY + " "):]

        # remove the " SECONDS" at the end of the clause
        seconds_index = every_clause_string.find("seconds")
        if seconds_index == -1:
            raise QueryParseException("'SECONDS' keyword missing from the EVERY clause.")

        # extract the delay from the 'EVERY' clause
        self.delay = every_clause_string[:seconds_index].strip()

    @staticmethod
    def validate_number(value, exception_message):
        try:
            return float(value)
        except ValueError:
            raise QueryParseException(exception_message)

    def validate_parameters(self):
        self.time_window_value = Query.validate_number(self.time_window_value,
                                                       "Time window value (FOR) must be a number.")
        self.delay = Query.validate_number(self.delay,
                                           "DELAY (EVERY) must be a number.")

    def invert_coordinates(self, value):
        self.condition = self.condition.replace(value + ".x", Query.PLACEHOLDER)
        self.condition = self.condition.replace(value + ".y", value + ".x")
        self.condition = self.condition.replace(Query.PLACEHOLDER, value + ".y")

    def invert_coordinates_in_condition(self):
        """
        We must invert any coordinates (ball.x with ball.y), and so on,
        because the frames' coordinates are reversed.
        """
        self.invert_coordinates("ball")
        self.invert_coordinates("player.1")
        self.invert_coordinates("player.2")
        self.invert_coordinates("player.3")
        self.invert_coordinates("player.4")
        self.invert_coordinates("player.5")
        self.invert_coordinates("player.6")

    def evaluate_condition_for_message(self, message: dict):
        enhanced_condition = self.condition
        # replace all the static values in the condition
        for static_operand in Query.STATIC_OPERAND_VALUES.items():
            enhanced_condition = enhanced_condition.replace(static_operand[0], str(static_operand[1]))

        # replace all the parsed values in the condition (values found in the given message)
        for parsed_operand in Query.PARSED_OPERAND_VALUES:
            try:
                parsed_operand_value = message
                for operand_key in parsed_operand.split("."):
                    parsed_operand_value = parsed_operand_value[operand_key]
                enhanced_condition = enhanced_condition.replace(parsed_operand, str(parsed_operand_value))
            except KeyError:
                # if the operand is correct, but we can't find it in the message because there is
                # no update yet, we return it as incomplete
                if parsed_operand in self.condition:
                    return Query.CONDITION_INCOMPLETE

        try:
            # evaluate the condition without any builtins to prevent any injections
            if eval(enhanced_condition, {'__builtin__': None}):
                return Query.CONDITION_CORRECT
            else:
                return Query.CONDITION_INCORRECT
        except (SyntaxError, ZeroDivisionError, NameError, TypeError, KeyError):
            # return CONDITION_ERROR if the eval failed because of any issues; we will print a message
            # for the user to know that the query's condition is broken for this particular event
            return Query.CONDITION_ERROR

    def add_message(self, message: dict):
        # evaluate the query condition, based on the new message
        condition_result = self.evaluate_condition_for_message(message)

        # check if the condition can be evaluated or if it is syntactically incorrect
        if condition_result == Query.CONDITION_ERROR:
            return "Error evaluating query condition!"
        elif condition_result == Query.CONDITION_CORRECT:
            # if the condition is true, we update the query evaluation parameters and check if we should
            # print the message in the query's 'THEN' clause

            # update query evaluation parameters
            if self.fit_entries == 0:
                self.first_entry_time = message[constants.FRAME_TIME]
            self.last_entry_time = message[constants.FRAME_TIME]
            self.fit_entries += 1

            # check if we should print the message, according to the time window type, value and delay
            if self.time_window_type == Query.TIME_WINDOW_ENTRIES and self.fit_entries >= self.time_window_value or \
                    self.time_window_type == Query.TIME_WINDOW_SECONDS and \
                    self.last_entry_time - self.first_entry_time >= self.time_window_value and \
                    self.last_entry_time - self.last_print_time >= self.delay:
                self.last_print_time = self.last_entry_time
                return self.print_string
        elif condition_result == Query.CONDITION_INCOMPLETE:
            # if the condition is incomplete, we do not print anything, but don't reset the query parameters;
            # the query's state remains the same
            return None
        else:
            # if the condition is false, we do not print anything and reset the query evaluation parameters
            self.fit_entries = 0
            self.first_entry_time = 0
            self.last_entry_time = 0
            return None
