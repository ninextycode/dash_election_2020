from threading import Lock
from state_const import states
import data_filters
import random
from data_functions import serialize_pd, deserialize_pd


# is a inside b
def is_subinterval(a, b):
    return b[0] <= a[0] and a[1] <= b[1]


def same_interval(a, b):
    return b[0] == a[0] and a[1] == b[1]


def fill_interval_none(new_interval, old_interval):
    new_interval = list(new_interval)
    if new_interval[0] is None:
        new_interval[0] = old_interval[0]
    if new_interval[1] is None:
        new_interval[1] = old_interval[1]
    return new_interval


class DataModel:
    def __init__(self, data=None):
        if data is not None:
            self.data = data.copy()
            self.original_data = data.copy()
        else:
            self.data = None
            self.original_data = None
        self.rep_state_vote_constraints = {s: (0, 1) for s in states}
        self.rep_natl_vote_constraint = (0, 1)
        self.rep_ec_vote_constraint = (0, 538)
        self.rep_states_win_constraint = (0, 51)
        self.data_changed = True
        self.data_lock = Lock()

    def to_json(self):
        return dict(
            data=serialize_pd(self.data),
            original_data=serialize_pd(self.original_data),
            rep_state_vote_constraints=self.rep_state_vote_constraints,
            rep_natl_vote_constraint=self.rep_natl_vote_constraint,
            rep_ec_vote_constraint=self.rep_ec_vote_constraint,
            rep_states_win_constraint=self.rep_states_win_constraint,
            data_changed=self.data_changed,
        )

    @staticmethod
    def from_json(json_data):
        obj = DataModel(None)
        obj.data = deserialize_pd(json_data["data"])
        obj.original_data = deserialize_pd(json_data["original_data"])
        obj.rep_state_vote_constraints = json_data["rep_state_vote_constraints"]
        obj.rep_natl_vote_constraint = json_data["rep_natl_vote_constraint"]
        obj.rep_ec_vote_constraint = json_data["rep_ec_vote_constraint"]
        obj.rep_states_win_constraint = json_data["rep_states_win_constraint"]
        obj.data_changed = json_data["data_changed"]
        return obj

    def _filter_data(self):
        self._filter_states_vote()
        self._filter_ec()
        self._filter_natl_vote()
        self._filter_states_win()

    def _filter_states_vote(self):
        for s in self.rep_state_vote_constraints.keys():
            self._filter_state_vote(s)

    def _filter_state_vote(self, state):
        (f, t) = self.rep_state_vote_constraints[state]
        self.data = data_filters.filter_rep_state_vote_range(self.data, state, f, t)

    def _filter_ec(self):
        self.data = data_filters.filter_rep_electoral_college_range(self.data, *self.rep_ec_vote_constraint)

    def _filter_natl_vote(self):
        self.data = data_filters.filter_rep_natl_vote_range(self.data, *self.rep_natl_vote_constraint)

    def _filter_states_win(self):
        self.data = data_filters.filter_rep_n_states_win_range(self.data, *self.rep_states_win_constraint)

    def add_state_vote_constraint(self, state, f=None, t=None):
        with self.data_lock:
            return self._add_state_vote_constraint_unsafe(state, f, t)

    def _add_state_vote_constraint_unsafe(self, state, f=None, t=None):
        old_interval = self.rep_state_vote_constraints[state]
        new_interval = fill_interval_none((f, t), old_interval)
        if same_interval(new_interval, old_interval):
            return
        if not is_subinterval(new_interval, old_interval):
            self._remove_state_vote_constraint(state)
        self.rep_state_vote_constraints[state] = new_interval
        self._filter_state_vote(state)
        self.data_changed = True

    def add_natl_vote_constraint(self, f=None, t=None):
        with self.data_lock:
            return self._add_natl_vote_constraint_unsafe(f, t)

    def _add_natl_vote_constraint_unsafe(self, f=None, t=None):
        old_interval = self.rep_natl_vote_constraint
        new_interval = fill_interval_none((f, t), old_interval)
        if same_interval(new_interval, old_interval):
            return
        if not is_subinterval(new_interval, old_interval):
            self._remove_natl_vote_constraint()
        self.rep_natl_vote_constraint = new_interval
        self._filter_natl_vote()
        self.data_changed = True

    def add_ec_vote_constraint(self, f=None, t=None):
        with self.data_lock:
            return self._add_ec_vote_constraint_unsafe(f, t)

    def _add_ec_vote_constraint_unsafe(self, f=None, t=None):
        old_interval = self.rep_ec_vote_constraint
        new_interval = fill_interval_none((f, t), old_interval)
        if same_interval(new_interval, old_interval):
            return
        if not is_subinterval(new_interval, old_interval):
            self._remove_ec_vote_constraint()
        self.rep_ec_vote_constraint = new_interval
        self._filter_ec()
        self.data_changed = True

    def add_states_win_constraint(self, f=None, t=None):
        with self.data_lock:
            return self._add_states_win_constraint_unsafe(f, t)

    def _add_states_win_constraint_unsafe(self, f=None, t=None):
        old_interval = self.rep_states_win_constraint
        new_interval = fill_interval_none((f, t), old_interval)
        if same_interval(new_interval, old_interval):
            return
        if not is_subinterval(new_interval, old_interval):
            self._remove_states_win_constraint()
        self.rep_states_win_constraint = new_interval
        self._filter_states_win()
        self.data_changed = True

    def _remove_state_vote_constraint(self, state):
        interval = self.rep_state_vote_constraints.get(state, (0, 1))
        if not same_interval(interval, (0, 1)):
            self.rep_state_vote_constraints[state] = (0, 1)
            self._reset_filter()

    def _remove_natl_vote_constraint(self):
        if not same_interval(self.rep_natl_vote_constraint, (0, 1)):
            self.rep_natl_vote_constraint = (0, 1)
            self._reset_filter()

    def _remove_ec_vote_constraint(self):
        if not same_interval(self.rep_ec_vote_constraint, (0, 538)):
            self.rep_ec_vote_constraint = (0, 538)
            self._reset_filter()

    def _remove_states_win_constraint(self):
        if not same_interval(self.rep_states_win_constraint, (0, 51)):
            self.rep_states_win_constraint = (0, 51)
            self._reset_filter()

    def reset_data(self):
        with self.data_lock:
            for s in states:
                if not same_interval((0, 1), self.rep_state_vote_constraints[s]):
                    self.rep_state_vote_constraints[s] = (0, 1)
                    self.data_changed = True
            if not same_interval((0, 1), self.rep_natl_vote_constraint):
                self.rep_natl_vote_constraint = (0, 1)
                self.data_changed = True
            if not same_interval((0, 538), self.rep_ec_vote_constraint):
                self.rep_ec_vote_constraint = (0, 538)
                self.data_changed = True
            if not same_interval((0, 51), self.rep_states_win_constraint):
                self.rep_states_win_constraint = (0, 51)
                self.data_changed = True

            self._reset()

    def _reset(self):
        self.data = self.original_data.copy()

    def _reset_filter(self):
        self._reset()
        self._filter_data()

    def get_random_sample(self):
        with self.data_lock:
            if len(self.data) > 0:
                return self.data.iloc[[random.choice(range(len(self.data)))]]
            else:
                return self.data.iloc[[]]
