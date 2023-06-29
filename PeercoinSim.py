import numpy as np
import matplotlib.pyplot as plt

dayyear=(365*33+8)/33
secday=60*60*24
NumSim=100

#Simulation Variables
#StaticReward=1.34
MaxSimDays=365*8
geometric=True

# Precomputed probability for 31-90 days to be adjusted by value/diff
probsecs = [2**224 * (x+1) / (2**256) for x in range(60)]

#Model
def RandomDaysToMint(outValue,difficulty,rng):

    adj = outValue / difficulty
    probs = [1 - (1 - probsecs[x]*adj)**secday for x in range(60)]

    DaysToMint=31
    for x in range(60):

        rnd = rng.random()
        probday = probs[x]

        if rnd<probday: break

        DaysToMint+=1

    else: DaysToMint=DaysToMint+rng.geometric(probs[59])

    return DaysToMint

rng = np.random.default_rng()

#Reward Wrapper
def MintRewards(outValue, difficulty, static):

    totalreward = 1 if geometric else 0
    totaldays = 0

    for _ in range(NumSim):

        MintDays=RandomDaysToMint(outValue,difficulty,rng)

        #Coinage Limit
        if MintDays < MaxSimDays:
            reward=0.03*outValue*min(dayyear, MintDays)/dayyear + static
            if geometric:
                totalreward *= 1+(reward/outValue)
            else:
                totalreward+=reward

        # Add to total days the amount of time waited on this mint upto the
        # maximum wait time
        totaldays += min(MintDays, MaxSimDays)

    # Return annualised percentage
    if geometric:
        return (totalreward**(dayyear/totaldays) - 1)*100
    rewardperday = totalreward/totaldays
    return rewardperday/outValue*36500

OutArray=[2**(x/4) for x in range(50)]
#OutArray=[10,20,30,40,50,60,70,80,90,100,110,120,130,140,150,160,170,180,190,200]
print(OutArray)

def OutputWrapper(diff,static):
    RewardArray=[MintRewards(x,diff,static) for x in OutArray]
    #PlotArray=[OutArray,RewardArray]
    return RewardArray

def DifficultyWrapper(diff,static):
    NumCurves=20
    optimal=0
    for w in range(NumCurves):
        RewardArray=OutputWrapper(diff,static)
        #ax.scatter(RandPlot[0],RandPlot[1])
        #print(w)
        optimal+=OutArray[RewardArray.index(max(RewardArray))]/NumCurves
    print(diff)
    print(static)
    print(optimal)
    return optimal

fig, ax = plt.subplots()
DiffArray=[8,12,16,20,24,28,32]
#DiffArray=[10,20,30]
#StaticArray=[0,0.5,1,1.34,1.5,2,3,4,5,10,20,100]
StaticArray=[0.5,1,1.34,2,3]
for u in StaticArray:
    OptimalArray=[DifficultyWrapper(v,u) for v in DiffArray]
    ax.scatter(DiffArray,OptimalArray)
ax.set_xlabel("Difficulty (unitless)")
ax.set_ylabel("Optimal Output (PPC)")
ax.legend(StaticArray,title="Static Reward (PPC)")
#plt.xscale("log")
plt.grid()
plt.show()


