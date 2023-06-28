import numpy as np
import matplotlib.pyplot as plt

dayyear=(365*33+8)/33
secday=60*60*24
MaxSimDays=720
#randomseed=9368
NumSim=1000

#Simulation Variables
diff=20

#Model
def RandomDaysToMint(outValue,difficulty,rng):
    rnd = 1
    DaysToMint=0
    for x in range(MaxSimDays):
        rnd = rng.random()
        #print("random")
        #print(rnd)
        probday=outValue*secday*min(60,max((x-30),0))/(diff*2**32)
        if rnd<probday: break
        DaysToMint+=1
    else: DaysToMint=10**11
    #print("DaysToMint")
    #print(MatDaysToMint)
    return DaysToMint

#Reward Wrapper
def MintRewards(outValue,difficulty):
    avgreward=0
    for y in range(NumSim):
        #rewardseed=randomseed+y
        rng = np.random.default_rng()
        MintDays=RandomDaysToMint(outValue,difficulty,rng)
        #Coinage Limit
        CoinageReward=0.03*outValue*min(365,(MintDays))/dayyear
        StaticReward=1.3
        normreward=(CoinageReward+StaticReward)/MintDays
        #print("reward/day")
        #print(normreward)
        avgreward+=normreward/NumSim
    return avgreward

def OutputWrapper():
    #OutArray=[0.01,0.1,1,10,100,1000]
    #OutArray=[10,20,30,35,40,50,75,100]
    OutArray=[1,2,5,8,10,15,20,30,50,75,100,150,200,300,500,750,1000]
    RewardArray=[]
    for z in OutArray:
        probdaymat=z*secday*(60)/(diff*2**32)
        thisreward=MintRewards(z,diff)
        RewardArray.append(thisreward/z)
        #print("Output: {}".format(z))
        #print("probability: {}%/day".format(probdaymat*100))
        #print("Reward/Coin/Day: {}".format(thisreward/z))
    PlotArray=[OutArray,RewardArray]
    return PlotArray

fig, ax = plt.subplots()
for w in range(10):
    RandPlot=OutputWrapper()
    ax.scatter(RandPlot[0],RandPlot[1])
    print(w)
ax.set_xlabel("UTXO Size")
ax.set_ylabel("Reward/Coin/Day")
plt.xscale("log")
plt.yscale("log")
plt.show()

