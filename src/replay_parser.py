import json
from time import sleep
from tkinter import messagebox, END

import src.constants as constants
from src.query import Query
from src.query_manager import QueryManager
from src.query_parse_exception import QueryParseException


def extract_frames(replay_json: dict, player_info: list) -> list:
    """
    Searches for all the positions the actors have ever been in during the game, and returns the
    relevant information in multiple frames.
    The structure of a frame:
    {
        time: frame time offset,
        ball: {
            x: ball position on x axis,
            y: ball position on y axis
        }
    }

    Note: The ids cannot be precomputed as they change when a goal is scored.
    """
    extracted_frames = []
    id_ball = -1
    id_players = []
    for _ in player_info:
        id_players.append(-1)
    for frame in replay_json[constants.FRAMES]:
        # add the frame time and an empty dictionary for the players
        extracted_frame = {
            constants.FRAME_TIME: frame[constants.TIME],
            constants.FRAME_PLAYER: {},
        }

        # go through all the actors in the current frame
        for actor_update in frame[constants.ACTOR_UPDATES]:
            # parse the ball position, if the current actor is the ball
            if id_ball != -1 and int(actor_update.get(constants.ID, -1) == id_ball) or \
                    actor_update.get(constants.CLASS_NAME, "") == constants.BALL_CLASS_NAME:
                id_ball = actor_update.get(constants.ID, -1)
                ball_position = actor_update[constants.ACTOR_STATE][constants.POSITION]
                extracted_frame[constants.FRAME_BALL] = {
                    constants.FRAME_X: ball_position[constants.AXIS_X],
                    constants.FRAME_Y: ball_position[constants.AXIS_Y],
                }

            # parse the player position, if the current actor is a car
            player_index = 1
            for id_player in id_players:
                if id_player != -1 and int(actor_update.get(constants.ID, -1) == id_player) \
                        or actor_update.get(constants.CLASS_NAME, "") == constants.PLAYER_CAR_CLASS_NAME \
                        and player_info[player_index - 1][constants.STORED_PLAYER_ID] \
                        == actor_update[constants.PLAYER_INFO_REFERENCE][constants.ACTOR_ID]:
                    id_players[player_index - 1] = actor_update.get(constants.ID, -1)
                    if actor_update.get(constants.ACTOR_STATE, None) is not None:
                        player_position = actor_update[constants.ACTOR_STATE][constants.POSITION]
                        extracted_frame[constants.FRAME_PLAYER][str(player_index)] = {
                            constants.FRAME_X: player_position[constants.AXIS_X],
                            constants.FRAME_Y: player_position[constants.AXIS_Y],
                        }
                player_index += 1

        # append the extracted frame
        extracted_frames.append(extracted_frame)

    # return all the parsed frames
    return extracted_frames


def extract_player_info(first_frame: dict) -> list:
    """
    Extracts the players' information (their ids, names, teams etc. from the first frame).
    """
    team_actor_ids = [-1, -1]
    # we first search for the team ids
    for actor_update in first_frame[constants.ACTOR_UPDATES]:
        # team 1
        if actor_update.get(constants.TYPE_NAME, "") == constants.TEAM_1_TYPE_NAME:
            team_actor_ids[0] = actor_update[constants.ID]
        # team 2
        if actor_update.get(constants.TYPE_NAME, "") == constants.TEAM_2_TYPE_NAME:
            team_actor_ids[1] = actor_update[constants.ID]

    # then we search for the player information
    players = []
    for actor_update in first_frame[constants.ACTOR_UPDATES]:
        if actor_update.get(constants.CLASS_NAME, "") == constants.PLAYER_INFO_CLASS_NAME:
            player_team_id = actor_update[constants.PLAYER_INFO_PLAYER_TEAM][constants.ACTOR_ID]
            if player_team_id == team_actor_ids[0]:
                player_team_id = constants.STORED_PLAYER_TEAM_1
            else:
                player_team_id = constants.STORED_PLAYER_TEAM_2
            players.append({
                constants.STORED_PLAYER_ID: actor_update[constants.ID],
                constants.STORED_PLAYER_NAME: actor_update[constants.PLAYER_INFO_PLAYER_NAME],
                constants.STORED_PLAYER_TEAM: player_team_id,
            })

    # and we return the players as a list of dicts
    return players


def find_min_and_max_of_field(extracted_frames) -> (dict, dict):
    """
    Finds the minimum and maximum positions of the ball, on all the three axis, given the extracted frames.
    """
    min_position = {constants.FRAME_X: float('inf'), constants.FRAME_Y: float('inf')}
    max_position = {constants.FRAME_X: float('-inf'), constants.FRAME_Y: float('-inf')}

    for frame in extracted_frames:
        for axis in [constants.FRAME_X, constants.FRAME_Y]:
            if int(frame[constants.FRAME_BALL][axis]) < min_position[axis]:
                min_position[axis] = frame[constants.FRAME_BALL][axis]
            if int(frame[constants.POSITION][axis]) > max_position[axis]:
                max_position[axis] = frame[constants.FRAME_BALL][axis]

    return min_position, max_position


def read_replay_to_string(file_name: str) -> str:
    """
    Given a file name as a string, it reads the replay in json format from the file, and returns
    it as a string, formatted and indented.
    """
    f = open(file_name, "r")
    formatted_string_json = json.dumps(json.loads(f.readline()), indent=2)
    f.close()
    return formatted_string_json


def read_replay_to_json(file_name: str) -> json:
    """
    Given a file name as a string, it reads the replay in json format and returns the json.
    """
    f = open(file_name, "r")
    replay_json = json.loads(f.readline())
    f.close()
    return replay_json


def position_to_screen_coord(position: dict) -> dict:
    return {
        constants.FRAME_X: (position[constants.FRAME_X] - constants.MIN_X) * constants.SCALE + constants.OFFSET_X,
        constants.FRAME_Y: (position[constants.FRAME_Y] - constants.MIN_Y) * constants.SCALE + constants.OFFSET_Y,
    }


def replay_extracted_frames(extracted_frames, main_frame):
    # query index, we store it here so we have it for reference in the parsing error popup
    query_index = 1
    try:
        # disable the start button and the input query text area while the replay is running
        main_frame.start_button.config(state="disabled")
        main_frame.query_input.config(state="disabled")

        # create our user queries by parsing the text area content, and create a query manager as well
        user_queries = []
        user_queries_text = main_frame.query_input.get("1.0", END).strip()
        for user_query_text in user_queries_text.split("\n\n"):
            user_queries.append(Query(user_query_text))
            query_index += 1
        query_manager = QueryManager(main_frame)
        for query in user_queries:
            query_manager.add_query(query)

        # go through every frame of the objects
        for frame_index in range(0, len(extracted_frames) - 1):
            # move the ball on the screen
            if constants.FRAME_BALL in extracted_frames[frame_index]:
                main_frame.move_ball(position_to_screen_coord(extracted_frames[frame_index][constants.FRAME_BALL]))

            # move the players on the screen
            main_frame.move_players(extracted_frames[frame_index][constants.FRAME_PLAYER])

            # parse the current message
            query_manager.add_message(extracted_frames[frame_index])

            # wait between frames, for the difference of time between them
            sleep(extracted_frames[frame_index + 1][constants.FRAME_TIME]
                  - extracted_frames[frame_index][constants.FRAME_TIME])

            # update the timer as well to reflect the time passed since the game started
            main_frame.set_time(extracted_frames[frame_index + 1][constants.FRAME_TIME])
    except QueryParseException as exception:
        # if a query could not be parsed, display it as a popup message with the error itself
        messagebox.showwarning("Input query #" + str(query_index) + " format error", str(exception))
    finally:
        # regardless of the queries being parsed or not, enable the start button and the query input as
        # the replay finishes
        main_frame.start_button.config(state="normal")
        main_frame.query_input.config(state="normal")

        # move the ball back to the center of the screen (first frame's position)
        main_frame.move_ball(position_to_screen_coord(extracted_frames[0][constants.FRAME_BALL]))

        # move the players back to the first frame's position
        main_frame.move_players(extracted_frames[0][constants.FRAME_PLAYER])

        # reset the timer to 00:00
        main_frame.set_time(0)

        # clear the query output
        main_frame.query_output.config(state="normal")
        main_frame.query_output.delete('1.0', END)
        main_frame.query_output.config(state="disabled")
