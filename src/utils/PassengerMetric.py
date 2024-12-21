from datetime import datetime

class PassengerMetric:
    ""
    PATIENCE_INTERVAL = 5 * 60 # 5 minutes

    def __init__(self, start_time) -> None:
        self.start_time = start_time
        self.board_time = None
        self.arrival_time = None

    def update_lift_arrival(self, board_time):
        self.board_time = board_time

    def update_dest_arrival(self, arrival_time):
        self.arrival_time = arrival_time

    def get_patience_end(self):
        if self.arrival_time is None:
            eval_time = datetime.now()
        else:
            eval_time = self.arrival_time
        if (eval_time - self.start_time).seconds > self.PATIENCE_INTERVAL:
            return True
        else:
            return False

    def get_metrics(self):
        eval_metrics = {}
        if self.board_time is not None:
            eval_metrics |= {"wait_time": self.board_time - self.start_time}
        if self.arrival_time is not None:
            eval_metrics |= {"transit_time": self.arrival_time - self.start_time}
            eval_metrics |= {"ride_time": self.arrival_time - self.board_time}
        if self.get_patience_end():
            eval_metrics |= {"timeout": True}
        
        return eval_metrics
    
