import numpy as np
from ..bindings import _dynamic_control
import omni.kit.settings


class CartPole:
    """ Cart-pole LQR control demo using dynamic_control Python bindings

        = To run =
        1. Load CartPole.usda from /assets
        2. Load PhysX by starting sim (press play)
            - System should start moving in open-loop
        3. Load the omni.isaac.dynamic_control extension
        4. In the extension window, click on the Test Cartpole button
        5. Click again to generate a new random initial condition

        = Notes =
        The start function generates the LQR controller by linearizing
        the dynamics numerically using the articulations compute joint
        accelerations method. Next, it generates a random initial condition
        and sets the articulation state accordingly.

        The control action is applied in the update method, which is called
        from the extension's subscribe_physics_step_events callback.
    """

    _state_dim = 4
    _input_dim = 1

    def start(self, dc):
        print("starting cp control...")

        ar_path = "/cartpole"
        print("Registering articulation '%s'" % ar_path)

        self.ar = dc.get_articulation(ar_path)
        print("Got ar", self.ar)
        if self.ar == _dynamic_control.INVALID_HANDLE:
            return False

        # get dof indices:
        self.cartIdx = dc.find_articulation_dof_index(self.ar, "cartPrismJoint")
        self.poleIdx = dc.find_articulation_dof_index(self.ar, "poleRevoluteJoint")
        # get handle of cart joint to apply control directly:
        self.cartDofHandle = dc.find_articulation_dof(self.ar, "cartPrismJoint")

        # Get sim timestep:
        _settings_iface = omni.kit.settings.get_settings_interface()
        timesteps_per_second = _settings_iface.get_as_float("/physics/timeStepsPerSecond")
        sample_time = 1.0 / timesteps_per_second
        print("Sampling time is 1.0/{}s".format(timesteps_per_second))
        # design LQR controller:
        # loss matrices for state x and input u: stage loss = x'Qx + u'Ru
        lqr_Q = np.diag([10, 1, 1, 1])  # penalize position more for fast return
        lqr_R = 0.1  # low penalty on control input for aggressive controller
        self.goalState = np.zeros((4, 1))  # goal is upright at rest
        self.goalInput = np.zeros((1, 1))  # goal input

        Act, Bct = self.getLinearizedDynamics(dc, numDiffH=0.01)

        Ad, Bd = CartPole.discretizeLTI(Act, Bct, tau=sample_time)

        K, _ = CartPole.designLQRD(Ad, Bd, lqr_Q, lqr_R)
        # pre-negate the lqr gain to use
        # u_k = lqr_K * (x - x_goal) + u_goal
        self.lqr_K = -K

        # generate random initial condition
        ranges = np.array(
            [-0.5, 0.5, -np.pi / 8.0, -np.pi / 8.0, -1.0, 1.0, -1.0, 1.0]  # pos  # ang  # lin vel
        )  # ang vel

        ic = np.random.uniform(ranges[0::2], ranges[1::2])

        print("Setting initial condition to [x, th, vx, omega] = {}".format(ic))

        # set IC:
        all_states = dc.get_articulation_dof_states(self.ar, _dynamic_control.STATE_NONE)
        all_states["pos"][self.cartIdx] = ic[0]
        all_states["pos"][self.poleIdx] = ic[1]
        all_states["vel"][self.cartIdx] = ic[2]
        all_states["vel"][self.poleIdx] = ic[3]

        dc.set_articulation_dof_states(self.ar, all_states, _dynamic_control.STATE_ALL)

        # setup uniform actuator noise:
        # TODO (@preist): Adjust variance to sampling time to have
        # comparable noise at different sampling times
        self.inputNoiseLim = np.array([-1.0, 1.0]) * 2.0

    def stop(self, dc):
        print("stopping cp control...")

    def update(self, dc, dt):
        # get state:
        stateDC = dc.get_articulation_dof_states(self.ar, _dynamic_control.STATE_ALL)
        state = self.stateFromDC(stateDC)

        # fix pole angle by applying modulo
        state[1] = np.mod(state[1] + np.pi, np.pi * 2.0) - np.pi

        # apply lqr gain on state deviation
        force = (self.lqr_K @ (state - self.goalState))[0] + self.goalInput

        # add input noise:
        inputNoise = np.random.uniform(self.inputNoiseLim[0], self.inputNoiseLim[1])
        force = force + inputNoise

        # use binding to set all dof efforts (True) or just single (False)
        set_all_dof_efforts = False

        if set_all_dof_efforts:
            forces = np.zeros(2, dtype=np.float32)
            forces[self.cartIdx] = force

            dc.apply_articulation_dof_efforts(self.ar, forces)
        else:
            dc.apply_dof_effort(self.cartDofHandle, force)

    def getLinearizedDynamics(self, dc, numDiffH: float = 0.01) -> list:
        # linearizes about goal state and input and returns list of A, B matrices
        Act = np.zeros((CartPole._state_dim, CartPole._state_dim))
        Bct = np.zeros((CartPole._state_dim, CartPole._input_dim))

        # setup goal state and effort
        goalStateDC = self.stateToDC(self.goalState)
        goalEfforts = np.zeros(2, dtype=np.float32)
        goalEfforts[self.cartIdx] = self.goalInput

        # now go through the DOFs and get the derivatives at dof +/- h
        # input zero
        for i in range(CartPole._state_dim):
            statePlus = np.copy(self.goalState)
            statePlus[i] += numDiffH
            stateDerivativePlus = self.stateFromDC(
                dc.get_articulation_dof_state_derivatives(self.ar, self.stateToDC(statePlus), goalEfforts)
            )
            stateMinus = np.copy(self.goalState)
            stateMinus[i] -= numDiffH
            stateDerivativeMinus = self.stateFromDC(
                dc.get_articulation_dof_state_derivatives(self.ar, self.stateToDC(stateMinus), goalEfforts)
            )
            # the difference between plus and minus is the i-th column of A:
            Act[:, [i]] = (stateDerivativePlus - stateDerivativeMinus) / (2.0 * numDiffH)

        # now do the same for the input:
        inputPlus = np.copy(goalEfforts)
        inputPlus[self.cartIdx] += numDiffH
        stateDerivativePlus = self.stateFromDC(
            dc.get_articulation_dof_state_derivatives(self.ar, goalStateDC, inputPlus)
        )
        inputMinus = np.copy(goalEfforts)
        inputMinus[self.cartIdx] -= numDiffH
        stateDerivativeMinus = self.stateFromDC(
            dc.get_articulation_dof_state_derivatives(self.ar, goalStateDC, inputMinus)
        )

        Bct = (stateDerivativePlus - stateDerivativeMinus) / (2.0 * numDiffH)

        return [Act, Bct]

    def discretizeLTI(Act: np.ndarray, Bct: np.ndarray, tau: float):
        M = np.concatenate((Act, Bct), 1)
        M = np.concatenate((M, np.zeros((1, Act.shape[1] + Bct.shape[1]))), 0)

        # calculate matrix exponential exp(M * tau), sans scipy
        # TODO (preist@): use scipy.linalg.expm(M * tau)
        M = M * tau
        Md = np.eye(np.shape(M)[0])
        fact = 1.0
        for i in range(1, 11):
            fact = fact * i
            Md = Md + 1.0 / fact * M
            M = M @ M

        Ad = Md[0 : Act.shape[0], 0 : Act.shape[1]]
        Bd = Md[0 : Bct.shape[0], Act.shape[1] : Act.shape[1] + Bct.shape[1]]

        return [Ad, Bd]

    def designLQRD(Ad, Bd, Q, R):
        # "solve" DARE sans scipy making use of the fact that the time-varying
        # LQR cost-to-go converges for Ad, Bd stabilizable, and Q, R > 0

        S = Q
        for _ in range(200):
            S = Ad.transpose() @ (S - S @ Bd @ np.linalg.inv(Bd.transpose() @ S @ Bd + R) @ Bd.transpose() @ S) @ Ad + Q

        # TODO (preist@): use S = scipy.linalg.solve_discrete_are(Ad, Bd, Q, R)
        K = np.linalg.inv(R + Bd.transpose() @ S @ Bd) @ Bd.transpose() @ S @ Ad
        return K, S

    def stateFromDC(self, dcState):
        state = np.zeros((CartPole._state_dim, 1))
        state[0] = dcState["pos"][self.cartIdx]
        state[1] = dcState["pos"][self.poleIdx]
        state[2] = dcState["vel"][self.cartIdx]
        state[3] = dcState["vel"][self.poleIdx]
        return state

    def stateToDC(self, state):
        dcState = np.zeros(2, dtype=_dynamic_control.DofState.dtype)
        dcState["pos"][self.cartIdx] = state[0]
        dcState["pos"][self.poleIdx] = state[1]
        dcState["vel"][self.cartIdx] = state[2]
        dcState["vel"][self.poleIdx] = state[3]
        return dcState


def get_cart_pole():
    return CartPole()
