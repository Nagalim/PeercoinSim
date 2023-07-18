import numpy as np
import random
import matplotlib.pyplot as plt
import peakutils as pk
from scipy.optimize import curve_fit
import scipy.optimize

# Time-based Constants.
dayyear=(365*33+8)/33
secday=60*60*24

### Start of Parameters as Arrays.  Every combination of given parameters will be plotted

## Statistical Parameters
# Simulated proof of stake difficulty
#PoSDifficulty = [2**((x+12)/4) for x in range(9)]
#PoSDifficulty = [3*x+1 for x in range(15)]
PoSDifficulty = [20]
# Presumed total length of the minting interval
#MaxSimDays = [dayyear*x/6+90 for x in range(10)]
MaxSimDays = [dayyear*4]
# Use of compounding interest formula
#geometric=[True,False]
geometric=[False]
# Number of days a UTXO must wait before its maturation period begins
#NoMintDays = [0,15,30,45,60]
NoMintDays = [30]
# Number of days for the maturation period after the probability ramp begins
#RampUpDays = [1,30,60,90,120]
RampUpDays = [60]
# NoMintDays+RampUpDays = Total length of maturation period

## Economic Parameters
# Coinage reward as a percentage.  This is the %/coin/year interest for the coinage-based portion of the reward.
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
Trials=[10]
# Total number of averaged simulations = NumSim*Trials

### The following parameters change the overall form of the plot

# Array of unspent transaction outputs.
# It is good to populate a log plot with exponential points like this:
UTXO=[2**(x/4)*10 for x in range(40)]
#UTXO=[2**(x/2)*10 for x in range(20)]
#UTXO=[25*x+1 for x in range(40)]
#UTXO=[10]

## Method Parameters
# Show mint probabilities instead of rewards (not an array)
calcMints=False
# Plot optimum output size and maximum reward
Optimize=False
# Optimize as a function of:
OptimizeVersus=PoSDifficulty
# SmallDailyProb is a number from 0 (precise) to 1 (estimate).
# If Daily Prob is very small, approximate the ramp up.
# What does x<<1 mean to you?  x=0.01?
SmallDailyProb = 0
Fit=False

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

#[{diff~PoSDifficulty},{MSD~MaxSimDays},{geo~geometric},{NMD~NoMintDays},{RUD~RampUpDays},
#,{Crew~CoinageReward},{Srew~StaticReward},{MCD~MaxCoinageDays},
#,{NS~NumSim},{Trl~Trials},{Outp~UTXO}]

# Simulate a single minter with a single output minting many times at constant difficulty
def MinterSimulation(probsecs, diff, MSD, geo, NMD, RUD, CRew, SRew, MCD, NS, Outp):

    # Initialize
    totalreward = 1 if geo else 0
    totaldays = 0
    mints = 0
    #rnd = rng.random()
    adj = Outp / diff
    probday=1
    RampSim=NS
    DaysToMint=NMD+1
    for x in range(RUD):
        probday = 1 - (1 - probsecs[x]*adj)**secday
        SimsMinted = RampSim * probday
        rnd = np.random.normal()
        SimsMinted = int(max(0,min(RampSim,np.floor(SimsMinted + rnd * (SimsMinted)**1/2))))
        DaysToMint += 1
        MintDays=DaysToMint
        
        for j in range(SimsMinted):
            if MintDays < MSD:
                mints += 1
                reward=CRew*Outp*min(MCD, MintDays)/dayyear + SRew
                if geo:
                    totalreward *= 1+(reward/Outp)
                else:
                    totalreward+=reward
            totaldays += min(MintDays, MSD)
        RampSim = RampSim - SimsMinted
    for j in range(RampSim):
        MintDays = DaysToMint + rng.geometric(probday)
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

def poly(x, a, b, c, d, e, f, g):
    return a*x**4+b*x**3+c*x**2+d*x+e+f*x**5+g*x**6

PolyGuess = np.array([0.27,-2.5,11.6,-24.8,23,-0.0135,0.00025])
    
def BalancedExp(x, a, b, c, d, e, f, g):
    return (a/np.exp(b*x**(-d))+f/(np.exp(-c*x**(-e))+g))**(-1)-g

InitGuess = np.array([0.25,65,6.2,0.73,0.26,0.056,0.14])

#[{diff~PoSDifficulty},{MSD~MaxSimDays},{geo~geometric},{NMD~NoMintDays},{RUD~RampUpDays},
#,{Crew~CoinageReward},{Srew~StaticReward},{MCD~MaxCoinageDays},
#,{NS~NumSim},{Trl~Trials},{Outp~UTXO}]

### Plotting
# Initialize
fig, ax = plt.subplots(figsize=(12, 6))
MaximumAverage=[]
OptimumUTXO=[]
MaxUTXO=[]
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
                                        # Some Peak Finding Stuff
                                        MaxAvg=max(AverageTrial)
                                        MaximumAverage.append(MaxAvg)
                                        MaxOutp=UTXO[np.array(AverageTrial).argmax()]
                                        MaxUTXO.append(MaxOutp)
                                        #ApproxPeakIndx = pk.indexes(np.array(AverageTrial), thres=0.3, min_dist=1000)
                                        #GaussPeaks = np.exp(pk.interpolate(np.array(np.log(UTXO)), np.array(AverageTrial), ind=ApproxPeakIndx))
                                        #OptimumUTXO.append(GaussPeaks[0])
                                        # Plot individual trials and fits
                                        if Optimize == False:
                                            ax.plot(UTXO, AverageTrial)
                                        if Fit == True:
                                            #ax.plot(UTXO, AverageTrial, label ="SRew={}".format(round(SRew,2)))
                                            ax.plot(UTXO, AverageTrial)
                                            #ax.scatter([GaussPeaks[0]], [MaxAvg],c="#458B00", label="Gauss")
                                            ax.scatter([MaxOutp], [MaxAvg],c="#000",label="Max")
                                            Balancedparams, Balancedcurve = curve_fit(BalancedExp, UTXO, AverageTrial,InitGuess)
                                            exppolyparams, exppolycurve = curve_fit(poly, np.log(UTXO), AverageTrial,PolyGuess)
                                            print("Balancedparams")
                                            print(Balancedparams)
                                            print("exppolyparams")
                                            print(exppolyparams)
                                            #print("zero")
                                            #print(BalancedExp(0, *Balancedparams))
                                            plt.plot(UTXO, BalancedExp(np.array(UTXO), *Balancedparams))
                                            plt.plot(UTXO, poly(np.array(np.log(UTXO)), *exppolyparams))
                                            BalancedOpt = scipy.optimize.fmin(lambda x: -BalancedExp(x,*Balancedparams), 100)
                                            ax.scatter(BalancedOpt, [BalancedExp(BalancedOpt[0],*Balancedparams)],c="#A80000",marker='^',label="Fit")
                                            
                                        ParameterNumber+=1




#Plot details
if Optimize == True:
    fig, ay = plt.subplots(figsize=(12, 6))
    #ax.plot(OptimizeVersus, MaximumAverage)
    ay.plot(OptimizeVersus, OptimumUTXO)
    #ax.set_xlabel("Difficulty")
    ay.set_xlabel("Difficulty")
    #ax.set_ylabel("Maximum Mints / Coin / Yr" if calcMints else "Maximum Reward (% / Yr)")
    ay.set_ylabel("Optimum Output for Minting (PPC)" if calcMints else "Optimum Output for Rewards (PPC)")
    #MaxAvgFit = np.polyfit(OptimizeVersus, MaximumAverage, 1)
    #MaxAvgEq = np.poly1d(MaxAvgFit)
    #ax.plot(OptimizeVersus, MaxAvgEq(OptimizeVersus),label="y=%.2fx+%.2f)"%(MaxAvgFit[0],MaxAvgFit[1]))
    #ax.legend(title="Linear")
    OutputFit = np.polyfit(OptimizeVersus[10:20], OptimumUTXO[10:20], 1)
    OutputEq = np.poly1d(OutputFit)
    ay.plot(OptimizeVersus[10:20], OutputEq(OptimizeVersus[10:20]),label="y=%.1fx+%.1f"%(OutputFit[0],OutputFit[1]))
    #plt.xscale(ScaleOfX)
    ay.legend(title="Linear")
    #ax.grid(which="both")
    ay.grid(which="both")
    plt.show()
else:
    #ax.plot(OptimumUTXO, MaximumAverage, c="#458B00")
    ax.plot(MaxUTXO, MaximumAverage, c="#000")
    ax.set_xlabel("UTXO Size")
    ax.set_ylabel("Mints / Coin / Yr" if calcMints else "% Reward / Yr")
    plt.xscale(ScaleOfX)
    plt.legend(title="Difficulty")
    plt.grid(which="both")
    plt.show()

