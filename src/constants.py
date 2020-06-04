# Strings that indicate values in the replay json
FRAMES = "Frames"
ACTOR_UPDATES = "ActorUpdates"
CLASS_NAME = "ClassName"
TYPE_NAME = "TypeName"
POSITION = "Position"
TIME = "Time"
ID = "Id"
ACTOR_ID = "ActorId"
ACTOR_STATE = "TAGame.RBActor_TA:ReplicatedRBState"
PLAYER_INFO_PLAYER_NAME = "Engine.PlayerReplicationInfo:PlayerName"
PLAYER_INFO_PLAYER_TEAM = "Engine.PlayerReplicationInfo:Team"
PLAYER_INFO_REFERENCE = "Engine.Pawn:PlayerReplicationInfo"

# Class & Type names used when searching for a particular type of actor in a frame
BALL_CLASS_NAME = "TAGame.Ball_TA"
PLAYER_CAR_CLASS_NAME = "TAGame.Car_TA"
PLAYER_INFO_CLASS_NAME = "TAGame.PRI_TA"
TEAM_1_TYPE_NAME = "Archetypes.Teams.Team0"
TEAM_2_TYPE_NAME = "Archetypes.Teams.Team1"

# The axes string values, used in iterations for positions / rotations
AXIS_X = "X"
AXIS_Y = "Y"
AXIS_Z = "Z"
AXES = [AXIS_X, AXIS_Y, AXIS_Z]

# Values used to extract frames and create events to be parsed by the continuous queries
FRAME_TIME = "time"
FRAME_BALL = "ball"
FRAME_X = "x"
FRAME_Y = "y"
FRAME_PLAYER = "player"

# Values used in the player information list
STORED_PLAYER_ID = "Id"
STORED_PLAYER_NAME = "Name"
STORED_PLAYER_TEAM = "Team"
STORED_PLAYER_TEAM_1 = "Team1"
STORED_PLAYER_TEAM_2 = "Team2"

# The values used to draw the map
# json parsing results:
# MIN: {'X': -4013.46, 'Y': -5213.3, 'Z': 80.84}
# MAX: {'X': 4014.2, 'Y': 5212.18, 'Z': 1956.81}
MIN_X = -4015
MIN_Y = -5215
MIN_Z = 80

MAX_X = 4015
MAX_Y = 5215
MAX_Z = 1957

LENGTH_X = MAX_X - MIN_X
LENGTH_Y = MAX_Y - MIN_Y
LENGTH_Z = MAX_Z - MIN_Z

# The scale at which we draw the map, in regards to the real map lengths in game units
# We also calculate the scaled lengths here
SCALE = 0.08

SCALED_LENGTH_X = LENGTH_X * SCALE
SCALED_LENGTH_Y = LENGTH_Y * SCALE
SCALED_LENGTH_Z = LENGTH_Z * SCALE

# The offset at which we draw the map, from the top-left corner
OFFSET_X = 25
OFFSET_Y = 25
