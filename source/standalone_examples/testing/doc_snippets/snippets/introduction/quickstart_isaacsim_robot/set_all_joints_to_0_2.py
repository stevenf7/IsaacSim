for i in range(4):
    print("running cycle: ", i)
    if i == 1 or i == 3:
        print("moving")
        # move the arm
        arm.set_joint_positions([[-1.5, 0.0, 0.0, -1.5, 0.0, 1.5, 0.5, 0.04, 0.04]])
        # move the car
        car.set_joint_velocities([[1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]])
    if i == 2:
        print("stopping")
        # reset the arm
        arm.set_joint_positions([[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]])
        # stop the car
        car.set_joint_velocities([[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]])

    for j in range(100):
        # step the simulation, both rendering and physics
        my_world.step(render=True)
        # print the joint positions of the car at every physics step
        if i == 3:
            car_joint_positions = car.get_joint_positions()
            print("car joint positions:", car_joint_positions)
