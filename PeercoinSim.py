import numpy as np
import random
import matplotlib.pyplot as plt

# Time-based Constants.
dayyear=(365*33+8)/33
secday=60*60*24

### Start of Parameters as Arrays.  Every combination of given parameters will be plotted

## Statistical Parameters
# Simulated proof of stake difficulty
#PoSDifficulty = [2**((x+12)/4) for x in range(9)]
PoSDifficulty = [x+15 for x in range(10)]
#PoSDifficulty = [20]
# Presumed total length of the minting interval
#MaxSimDays = [dayyear*x/6+90 for x in range(10)]
MaxSimDays = [dayyear*4]
# Use of compounding interest formula
#geometric=[True,False]
geometric=[True]
# Number of days a UTXO must wait before its maturation period begins
#NoMintDays = [0,15,30,45,60]
NoMintDays = [30]
# Number of days for the maturation period after the probability ramp begins
#RampUpDays = [1,30,60,90,120]
RampUpDays = [60]
# NoMintDays+RampUpDays = Total length of maturation period

## Economic Parameters
# Coinage reward as a percentage.  This is the %/coin/year interest for the coinage-based portion of the reward.
#CoinageReward = [0,0.01,0.02,0.03,0.04,0.05,0.06]
CoinageReward = [0.03]
# Static reward as a number of coins.
# We maybe should change this to a percentage of the supply, but that would require an additional input
#StaticReward = [0,0.67,1.34,2.68,5.36]
#StaticReward = [x/10+1.3 for x in range(7)]
StaticReward = [1.34]
# Maximum number of days the coinage reward will build for a UTXO
#MaxCoinageDays = [0.25*dayyear,0.5*dayyear,dayyear,2*dayyear,4*dayyear]
MaxCoinageDays = [dayyear]

## Resolution Parameters
# Repititions that are not reported, only the average is advanced
NumSim=[10000]
# Repititions that are reported up to the top level
Trials=[100]
# Total number of averaged simulations = NumSim*Trials

### The following parameters change the overall form of the plot

# Array of unspent transaction outputs.
# It is good to populate a log plot with exponential points like this:
#UTXO=[2**(x/4) for x in range(45)]
UTXO=[2*x+70 for x in range(40)]

## Method Parameters
# Show mint probabilities instead of rewards (not an array)
calcMints=False
# Plot optimum output size and maximum reward
Optimize=True
# Optimize as a function of:
OptimizeVersus=PoSDifficulty
# If Daily Prob is very small, approximate the ramp up
SmallDailyProb = 0.001

## Plot Parameters
# linear/log (not an array)
ScaleOfX="log"

### End of Parameters Section

# Random number generator (move this out of global for deterministic seeds)
rng = np.random.default_rng()

#In the following definitions, we will avoid collision with global variables using the following mapping:
#[{diff~PoSDifficulty},{MSD~MaxSimDays},{geo~geometric},{NMD~NoMintDays},{RUD~RampUpDays},
#,{Crew~CoinageReward},{Srew~StaticReward},{MCD~MaxCoinageDays},
#,{NS~NumSim},{Trl~Trials},{Outp~UTXO}]

### Model

#Generate a random number of days to mint given chosen parameters
def RandomDaysToMint(probsecs, diff, NMD, RUD, Outp):

    # Adjust probability by UTXO and difficulty
    adj = Outp / diff

    #Initialize.  NMD+1 is the first day you could possibly mint
    DaysToMint=NMD+1
    probday=1
    estprobday = probsecs[RUD-1]*adj*secday
    #print("Out:{},estprobday:{}".format(Outp,estprobday))
    if estprobday>SmallDailyProb:

        # Maturation period
        for x in range(RUD):

            # Random number
            rnd = rng.random()
            # Calculate required probability to mint
            probday = 1 - (1 - probsecs[x]*adj)**secday
            # Did you find a block?
            if rnd<probday:
                return DaysToMint
            # Apparently not
            DaysToMint+=1

    else:
        DaysToMint = NMD+RUD+1
        probay = estprobday

    # Will return either the length of maturation,
    # or the full maturation plus the randomly generated number of days to mint
    return DaysToMint+rng.geometric(probday)


#[{diff~PoSDifficulty},{MSD~MaxSimDays},{geo~geometric},{NMD~NoMintDays},{RUD~RampUpDays},
#,{Crew~CoinageReward},{Srew~StaticReward},{MCD~MaxCoinageDays},
#,{NS~NumSim},{Trl~Trials},{Outp~UTXO}]

# Simulate a single minter with a single output minting many times at constant difficulty
def MinterSimulation(probsecs, diff, MSD, geo, NMD, RUD, CRew, SRew, MCD, NS, Outp):

    # Initialize
    totalreward = 1 if geo else 0
    totaldays = 0
    mints = 0

    # Loop over simulations
    for _ in range(NS):

        # Grab how many days it takes simulation to mint
        MintDays=RandomDaysToMint(probsecs, diff, NMD, RUD, Outp)
        # If they mint before they stop minting
        if MintDays < MSD:
            mints += 1
            # Reward calculation
            reward=CRew*Outp*min(MCD, MintDays)/dayyear + SRew
            # Compounding interest modification
            if geo:
                totalreward *= 1+(reward/Outp)
            else:
                totalreward+=reward

        # Add to total days the amount of time waited on this mint up to the
        # maximum wait time
        totaldays += min(MintDays, MSD)

    # If showing probabilites, return total number of mints per output per year
    if calcMints:
        return mints/totaldays/Outp*dayyear

    # Return annualised percentage (calculated based on compounding or average)
    if geo:
        return (totalreward**(dayyear/totaldays) - 1)*100
    rewardperday = totalreward/totaldays
    return rewardperday/Outp*dayyear*100


#[{diff~PoSDifficulty},{MSD~MaxSimDays},{geo~geometric},{NMD~NoMintDays},{RUD~RampUpDays},
#,{Crew~CoinageReward},{Srew~StaticReward},{MCD~MaxCoinageDays},
#,{NS~NumSim},{Trl~Trials},{Outp~UTXO}]

# Wrap it all up and feed it into the machine
def InputWrapper(i, diff, MSD, geo, NMD, RUD, CRew, SRew, MCD, NS):
    # Print which trial you're on
    print(i)
    # Precompute probabilities to save time lower down
    # Precomputed probability for 31-90 days (or whatever ramp up) to be adjusted by value/diff
    probsecs = [60/(RUD) *2**224 * (x+1) / (2**256) for x in range(RUD)]
    # Simulate a full trial including all UTXO sizes
    return [MinterSimulation(probsecs, diff, MSD, geo, NMD, RUD, CRew, SRew, MCD, NS, Outp) for Outp in UTXO]


#[{diff~PoSDifficulty},{MSD~MaxSimDays},{geo~geometric},{NMD~NoMintDays},{RUD~RampUpDays},
#,{Crew~CoinageReward},{Srew~StaticReward},{MCD~MaxCoinageDays},
#,{NS~NumSim},{Trl~Trials},{Outp~UTXO}]

### Plotting
# Initialize
fig, ax = plt.subplots(figsize=(12, 6))
MaximumAverage=[]
OptimumUTXO=[]
# Add to the plot for every combination of parameters
ParameterNumber=1
for diff in PoSDifficulty:
    for MSD in MaxSimDays:
        for geo in geometric:
            for NMD in NoMintDays:
                for RUD in RampUpDays:
                    for CRew in CoinageReward:
                        for SRew in StaticReward:
                            for MCD in MaxCoinageDays:
                                for NS in NumSim:
                                    for Trl in Trials:
                                        print("Parameter number {}".format(ParameterNumber))
                                        # Make a random set of trials
                                        SetofTrials = [InputWrapper(x, diff, MSD, geo, NMD, RUD, CRew, SRew, MCD, NS) for x in range(Trl)]
                                        # Average the trials
                                        AverageTrial = [sum(l) / len(l) for l in list(zip(*SetofTrials))]
                                        # Plot (and/or scatter plot) the trials
                                        if Optimize == True:
                                            MaximumAverage.append(max(AverageTrial))
                                            OptimumUTXO.append(UTXO[np.array(AverageTrial).argmax()])
                                        else:
                                            ax.plot(UTXO, AverageTrial, label ="100CRew= {}".format(round(CRew*100,0)))
                                            #ax.scatter(UTXO, SetofTrials, c="#AAB")
                                        ParameterNumber+=1

#round(MSD,-1)

#Plot details
if Optimize == True:
    fig, ay = plt.subplots(figsize=(12, 6))
    ax.plot(OptimizeVersus, MaximumAverage)
    ay.plot(OptimizeVersus, OptimumUTXO)
    ax.set_xlabel("Difficulty")
    ay.set_xlabel("Difficulty")
    ax.set_ylabel("Maximum Mints / Coin / Yr" if calcMints else "Maximum Reward (% / Yr)")
    ay.set_ylabel("Optimum Output for Minting (PPC)" if calcMints else "Optimum Output for Rewards (PPC)")
    MaxAvgFit = np.polyfit(OptimizeVersus, MaximumAverage, 1)
    MaxAvgEq = np.poly1d(MaxAvgFit)
    ax.plot(OptimizeVersus, MaxAvgEq(OptimizeVersus),label="y=%.2fx+%.2f)"%(MaxAvgFit[0],MaxAvgFit[1]))
    ax.legend(title="Linear")
    OutputFit = np.polyfit(OptimizeVersus, OptimumUTXO, 1)
    OutputEq = np.poly1d(OutputFit)
    ay.plot(OptimizeVersus, OutputEq(OptimizeVersus),label="y=%.1fx+%.1f"%(OutputFit[0],OutputFit[1]))
    #plt.xscale(ScaleOfX)
    ay.legend(title="Linear")
    ax.grid(which="both")
    ay.grid(which="both")
    plt.show()
else:
    ax.set_xlabel("UTXO Size")
    ax.set_ylabel("Mints / Coin / Yr" if calcMints else "% Reward / Yr")
    plt.xscale(ScaleOfX)
    plt.legend(title="Coinage Reward (%)")
    plt.grid(which="both")
    plt.show()
