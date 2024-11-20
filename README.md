python3 -m venv env


To Do Tasks:
  1. accurate collision physics [DONE]
  2. Find details on the following:
      - grade or incline angle of surfaces
      - obstacle density
      - verticle and horizontal area coverage
      - frequency of floor gaps and gap widths
      - minimum aperture size
  3. Add zones for ground differences above
  4. Add sensor details in the simulation
  5. Add distributed sensing [DONE]
Meeting Notes:
The goal is to 1. generate a baseline on power consumption required, 2. figure out optimal sensor split.
Get list of papers that do 2D multi agent algorithms and see what experiments they conducted


https://www.reuters.com/graphics/EARTHQUAKE-RESCUE/mopajqojmva/
https://www.maggianolaw.com/blog/types-of-structural-collapse/


RQ 2. How does deployment method affect a microrobot team’s operational range?
range of space that can be reached and acted on
the individual and combined cost of transport
analyze which factors increase operational range without affecting COT
RQ 5. How can navigation policies for a heterogeneous team be developed considering the symbiotic interactions?
develop a cohesive model of the team that accounts for both individual capabilities and symbiotic capabilities that arise between agents within the team, which we will formalize as a Markov decision process. 
To begin, we will look at the agents as heterogeneous individuals, developing the action space and transition probabilities of the growing robot and microrobots by themselves.
For deciding when to instantiate new agents, we will examine two possibilities, either using the task allocation MDP level to deploy robots [31] and creating new individual performance MDPs to represent the new microrobots, or having undeployed microrobots always be instantiated and act as agents with limited action space and a state location matching the growing robot before deployment.

RQ 6. How can navigation and exploration be balanced within a heterogenous team?
(1) searching for a single target within a space (for example a trapped victim) and 
(2) distributing sensors to monitor a full environment with minimal overlap.
answer the relative capabilities of the team for a single target search and full space search 
investigate how different team compositions and capabilities would effect the relative effectiveness
example: increasing the operation time of the microrobots, or the speed of movement of the growing robot



Similar Papers:

Trajectory Planning for Heterogeneous Robot Teams 
  - https://act.usc.edu/publications/Debord_IROS2018.pdf
  - 3D Simulation enviroment, addresses trajectory planning with asymmetric inter-robot collisions in known enviroments

Cooperative behavior of a heterogeneous robot team for planetary exploration using deep reinforcement learning 
  - https://www.sciencedirect.com/science/article/pii/S0094576523005751?fr=RR-2&ref=pdf_download&rr=8e1f63506c8fc998
  - establishes a method for determining the reward criteria (figures of merit) that can be used for training the robot swarm through reinforcement learning techniques
  - 