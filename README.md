# Rocket League Replay Analyzer

This is a Python tool that allows you to load JSON replays, and analyze them by writing continuous queries in a Streaming SQL-like language.

Screenshot:

![Screenshot](https://github.com/Alxertion/RocketLeagueReplayAnalyzer/blob/master/screenshot.png?raw=true)

A query has this structure:<br>
**IF** _CONDITION_<br>
**FOR** _TIME_WINDOW_<br>
**THEN** PRINT("_MESSAGE_")<br>
**EVERY** _DELAY_ SECONDS<br>

_CONDITION_ can be: a Python-like condition, which can use predefined values as well as numbers / booleans / operators etc.:<br>
<ul>
    <li>ball.x (the ball's position on the X axis);
    <li>ball.y (the ball's position on the Y axis);
    <li>player.1.x;
    <li>player.1.y;
    <li>player.2.x;
    <li>...
    <li>player.6.x;
    <li>player.6.y;
    <li>midfield.x (the position at the middle of the field on the X axis: 0);
</ul>
<i>TIME_WINDOW</i> can be:
<ul>
    <li>LAST x SECONDS (where 'x' is a number)
    <li>LAST x ENTRIES (where 'x' is a number)
</ul>

_MESSAGE_ can be: a string printed when the condition is true _'FOR the LAST x SECONDS/ENTRIES'_.

_DELAY_ can be: a number (2, 10, 0.5, etc); the message will be printed AT MOST every _DELAY_ seconds.

### Query examples:

IF ball.x < midfield.x<br>
FOR LAST 2 SECONDS<br>
THEN PRINT("Orange team defending")<br>
EVERY 1 SECONDS

IF ball.x > midfield.x<br>
FOR LAST 2 SECONDS<br>
THEN PRINT("Blue team defending")<br>
EVERY 1 SECONDS

IF player.3.x > midfield.x and player.5.x > midfield.x and player.6.x > midfield.x<br>
FOR LAST 1 SECONDS<br>
THEN PRINT("Entire orange team is offensive")<br>
EVERY 0.5 SECONDS
