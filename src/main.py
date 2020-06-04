from threading import Thread
from tkinter import Tk, Canvas, Frame, BOTH, Label, Button, INSERT
from tkinter.scrolledtext import ScrolledText

import src.constants as constants
import src.replay_parser as replay_parser
from src.query import Query

# This is the file that will be parsed as a replay by the application and displayed;
# In the 'replaysJson' folder, there are a lot of replays to choose from.
PATH_TO_JSON = "../replaysJson/example.json"


class MainFrame(Frame):
    def __init__(self):
        super().__init__()

        # canvas reference init
        self.canvas = None

        # components reference init
        self.timer_label = None
        self.start_button = None
        self.query_tutorial = None
        self.query_input = None
        self.query_output = None
        self.query_tutorial_label = None
        self.query_input_label = None
        self.query_output_label = None

        # replay objects init
        self.replay_json = replay_parser.read_replay_to_json(PATH_TO_JSON)
        self.player_info = replay_parser.extract_player_info(self.replay_json[constants.FRAMES][0])
        self.extracted_frames = replay_parser.extract_frames(self.replay_json, self.player_info)
        self.ball_object = None
        self.player_objects = []
        self.player_text_objects = []
        for _ in self.player_info:
            self.player_objects.append(None)
            self.player_text_objects.append(None)

        # UI drawing
        self.init_ui()

    def handle_start_button(self):
        thread = Thread(target=replay_parser.replay_extracted_frames, args=(self.extracted_frames, self))
        thread.start()

    def move_ball(self, new_position):
        if self.ball_object is not None:
            self.canvas.delete(self.ball_object)
        self.ball_object = self.canvas.create_oval(new_position[constants.FRAME_Y] - 8,
                                                   new_position[constants.FRAME_X] - 8,
                                                   new_position[constants.FRAME_Y] + 8,
                                                   new_position[constants.FRAME_X] + 8,
                                                   outline='red', fill='darkGreen')

    def move_players(self, player_positions):
        for i in range(0, len(self.player_objects)):
            # player index
            player_index = str(i + 1)

            # move to the next player if this player is not found in this frame
            if player_positions.get(player_index, None) is None:
                continue

            # delete the current player object if it exists, since we create a new one
            if self.player_objects[i] is not None:
                self.canvas.delete(self.player_objects[i])
            if self.player_text_objects[i] is not None:
                self.canvas.delete(self.player_text_objects[i])

            # player color
            if self.player_info[i][constants.STORED_PLAYER_TEAM] == constants.STORED_PLAYER_TEAM_1:
                player_fill = "orange"
            else:
                player_fill = "blue"

            # player position
            player_position = replay_parser.position_to_screen_coord(player_positions[player_index])

            # draw the player rectangle
            self.player_objects[i] = self.canvas.create_rectangle(player_position[constants.FRAME_Y] - 16,
                                                                  player_position[constants.FRAME_X] - 16,
                                                                  player_position[constants.FRAME_Y] + 16,
                                                                  player_position[constants.FRAME_X] + 16,
                                                                  outline='red', fill=player_fill)

            # draw the player text over the rectangle
            self.player_text_objects[i] = self.canvas.create_text(player_position[constants.FRAME_Y],
                                                                  player_position[constants.FRAME_X],
                                                                  font=("Helvetica", 28), text=player_index,
                                                                  fill="white")

    def set_time(self, new_time):
        minutes = round(new_time) // 60
        seconds = round(new_time) % 60
        time = ""
        if minutes < 10:
            time += "0"
        time += str(minutes)
        time += ":"
        if seconds < 10:
            time += "0"
        time += str(seconds)
        self.timer_label['text'] = time

    def init_ui(self):
        # canvas init
        self.master.title("RL Replay Analyzer")
        self.pack(fill=BOTH, expand=1)
        self.canvas = Canvas(self)

        # rectangle around the field
        bounding_box = [0, 0, 0, 0]
        bounding_box[0] = constants.OFFSET_X
        bounding_box[1] = constants.OFFSET_Y
        bounding_box[2] = bounding_box[0] + constants.SCALED_LENGTH_Y
        bounding_box[3] = bounding_box[1] + constants.SCALED_LENGTH_X
        self.canvas.create_rectangle(*bounding_box)

        # calculate the values of the midfield
        middle_x = (bounding_box[0] + bounding_box[2]) / 2
        middle_y = (bounding_box[1] + bounding_box[3]) / 2

        # mid line
        self.canvas.create_line(middle_x, bounding_box[1], middle_x, bounding_box[3])

        # circle around the middle
        self.canvas.create_oval(middle_x - 80, middle_y - 80, middle_x + 80, middle_y + 80)

        # left goal
        self.canvas.create_rectangle(bounding_box[0] - 5, middle_y - 80,
                                     bounding_box[0] + 5, middle_y + 80,
                                     fill='orange')

        # right goal
        self.canvas.create_rectangle(bounding_box[2] - 5, middle_y - 80,
                                     bounding_box[2] + 5, middle_y + 80,
                                     fill='blue')

        # ball placing in the position from the first frame
        ball_position = replay_parser.position_to_screen_coord(self.extracted_frames[0][constants.FRAME_BALL])
        self.move_ball(ball_position)

        # player placing in the position from the first frame
        self.move_players(self.extracted_frames[0][constants.FRAME_PLAYER])

        # timer
        self.timer_label = Label(self.master, text="00:00", font=("Helvetica", 30))
        self.timer_label.place(x=1300, y=20, anchor='ne')

        # query tutorial scrollable text area & label
        self.query_tutorial_label = Label(self.master, text="How to build a query:")
        self.query_tutorial_label.place(x=1388, y=100, anchor='e')
        self.query_tutorial = ScrolledText(self.master, undo=True, wrap='word', height=28, width=36)
        self.query_tutorial.place(x=1580, y=340, anchor='e')
        self.query_tutorial.insert(INSERT, Query.TUTORIAL_TEXT)
        self.query_tutorial.config(state="disabled")

        # query input scrollable text area & label
        self.query_input_label = Label(self.master, text="Your queries (separated by a blank line):")
        self.query_input_label.place(x=1103, y=100, anchor='e')
        self.query_input = ScrolledText(self.master, undo=True, wrap='word', height=16, width=41)
        self.query_input.place(x=1240, y=245, anchor='e')
        self.query_input.insert(INSERT, Query.INITIAL_QUERIES)

        # query output scrollable text area & label
        self.query_output_label = Label(self.master, text="Queries' output:")
        self.query_output_label.place(x=978, y=395, anchor='e')
        self.query_output = ScrolledText(self.master, undo=True, wrap='word', height=16, width=41,
                                         state="disabled")
        self.query_output.place(x=1240, y=538, anchor='e')

        # start button
        self.start_button = Button(self.master, text="Start replay",
                                   command=self.handle_start_button,
                                   font=("Helvetica", 30), width=13)
        self.start_button.place(x=1580, y=670, anchor='se')

        self.canvas.pack(fill=BOTH, expand=1)


def main():
    # dump frames to file
    # f = open("frameExampleJson.txt", "w")
    # f.write(json.dumps(result["Frames"][0], indent=2))
    # f.close()

    # print min/max
    # min_pos, max_pos = replay_parser.find_min_and_max_of_field(extracted_frames)
    # print(str(min_pos) + " " + str(max_pos))

    root = Tk()
    main_frame = MainFrame()
    root.geometry("1600x700")
    root.resizable(False, False)
    root.mainloop()


if __name__ == '__main__':
    main()
