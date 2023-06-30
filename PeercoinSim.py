import numpy as np
import random
import matplotlib.pyplot as plt

dayyear=(365*33+8)/33
secday=60*60*24
NumSim=250

#Simulation Variables
diff=20.43
PercentageReward=0
StaticReward=1.34*4
MaxSimDays=365*10
calcMints=False
geometric=True

# Precomputed probability for 31-90 days to be adjusted by value/diff
probsecs = [2**224 * (x+1) / (2**256) for x in range(60)]

#Model
def RandomDaysToMint(outValue,difficulty,rng):

    adj = outValue / difficulty
    DaysToMint=31
    probday=1

    for x in range(60):

        rnd = random.random()
        probday = 1 - (1 - probsecs[x]*adj)**secday

        if rnd<probday:
            return DaysToMint

        DaysToMint+=1

    return DaysToMint+rng.geometric(probday)

rng = np.random.default_rng()

#Reward Wrapper
def MintRewards(outValue, difficulty, PRew, SRew):

    totalreward = 1 if geometric else 0
    totaldays = 0
    mints = 0

    for _ in range(NumSim):

        MintDays=RandomDaysToMint(outValue,difficulty,rng)

        #Coinage Limit
        if MintDays < MaxSimDays:
            mints += 1
            reward=PRew*outValue*min(365, MintDays)/dayyear + SRew
            if geometric:
                totalreward *= 1+(reward/outValue)
            else:
                totalreward+=reward

        # Add to total days the amount of time waited on this mint upto the
        # maximum wait time
        totaldays += min(MintDays, MaxSimDays)

    if calcMints:
        return mints/totaldays/outValue*365

    # Return annualised percentage
    if geometric:
        return (totalreward**(dayyear/totaldays) - 1)*100
    rewardperday = totalreward/totaldays
    return rewardperday/outValue*36500

OutArray=[2**(x/4) for x in range(35)]
print(OutArray)

def OutputWrapper(i, PRew, SRew):
    print(i)
    return [MintRewards(x, diff, PRew, SRew) for x in OutArray]

fig, ax = plt.subplots(figsize=(12, 6))

results = [OutputWrapper(x,PercentageReward,StaticReward) for x in range(25)]
results2 = [OutputWrapper(x,0.03,1.34) for x in range(25)]

for result in results:
    ax.scatter(OutArray, result, c="#AAB")
for result2 in results2:
    ax.scatter(OutArray, result2, c="#AAB")

average = [sum(l) / len(l) for l in list(zip(*results))]
ax.plot(OutArray, average,label ='Custom')

average2 = [sum(m) / len(m) for m in list(zip(*results2))]
ax.plot(OutArray, average2,label ='Current')

ax.set_xlabel("UTXO Size")
ax.set_ylabel("Mints / Coin / Yr" if calcMints else "% Reward / Yr")
#plt.xscale("log")
plt.legend()
plt.grid(which="both")
plt.show()

