import time
from enum import Enum
from movement.line_following import LineFollower
from movement.calibrated_motor import CalibratedMotor
from movement.movement_routines import MovementRoutines
from sensors.infrared import InfraredSensor
from core.direction import Direction, RelativeDirection
from core import direction
from io.logger import Logger


class TankRobot:

    # COMPONENT CLASSES
    motor: CalibratedMotor
    infrared: InfraredSensor

    # IO
    logger: Logger

    # CONTROL CLASSES
    movement_routines: MovementRoutines
    line_follower: LineFollower

    # STATE VARIABLES
    class TankState(Enum):
        INITIALIZING = 0
        ERROR = -1
        LINE_FOLLOWING = 1
        AT_NODE = 2
        READY_TO_DEPART = 3
    state: TankState

    facing_direction: Direction
    last_departure_direction: Direction
    next_departure_direction: Direction

    def __init__(self):
        self.switch_state(self.TankState.INITIALIZING)
        self.facing_direction = Direction.UNKNOWN
        self.last_departure_direction = Direction.UNKNOWN
        self.next_departure_direction = Direction.UNKNOWN

        self.logger = Logger()

        self.motor = CalibratedMotor()
        self.infrared = InfraredSensor()

        self.movement_routines = MovementRoutines(self.motor)
        self.line_follower = LineFollower(self.infrared, self.motor, self.movement_routines)

    def switch_state(self, new_state: TankState):
        self.state = new_state
        self.logger.log(f"New TankState: {new_state}")

    def core_loop(self):
        self.switch_state(self.TankState.LINE_FOLLOWING)

        while True:
            if self.state == self.TankState.LINE_FOLLOWING:
                self.logger.log("Starting line following step")
                self.line_follow_step()

            if self.state == self.TankState.READY_TO_DEPART:
                self.logger.log("Starting departure")
                self.depart_from_node()

            if self.state == self.TankState.ERROR:
                self.logger.log("!!! ERROR STATE !!!")
                time.sleep(1) # TODO: Handle error

    def line_follow_step(self):
        follow_result = self.line_follower.follow_to_next_node()

        if follow_result == LineFollower.FollowResult.ARRIVED_AT_NODE:
            self.on_node_arrival()

        elif follow_result == LineFollower.FollowResult.TIMED_OUT:
            self.switch_state(self.TankState.ERROR) # TODO: Handle error

    def on_node_arrival(self):
        self.switch_state(self.TankState.AT_NODE)

        # TODO: Replace with actual path choosing
        cur_dir = direction.str_to_direction(input("Which direction (N,E,S,W) am I facing? "))
        depart_dir = direction.str_to_direction(input("In which direction (N,E,S,W) should I depart? "))

        self.facing_direction = cur_dir
        self.next_departure_direction = depart_dir

        self.logger.log(f"Facing {self.facing_direction}")
        self.logger.log(f"Next departure direction: {self.next_departure_direction}")
        self.switch_state(self.TankState.READY_TO_DEPART)

    def depart_from_node(self):

        # DEPART IN FACING DIRECTION
        target_direction = direction.get_relative_direction(self.facing_direction, self.next_departure_direction)

        if target_direction == RelativeDirection.UNKNOWN:
            self.switch_state(self.TankState.ERROR)  # TODO: Handle error
            return

        self.movement_routines.node_departure(target_direction)

        if target_direction == RelativeDirection.RIGHT:
            self.line_follower.change_strategy(LineFollower.StrategyState.ROTATE_RIGHT)
        elif target_direction == RelativeDirection.LEFT:
            self.line_follower.change_strategy(LineFollower.StrategyState.ROTATE_LEFT)

        self.switch_state(self.TankState.LINE_FOLLOWING)
